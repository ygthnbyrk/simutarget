"""
Lemon Squeezy Billing entegrasyonu — webhook handler ve checkout endpoints.

Akış:
  1. Frontend POST /api/v1/lemonsqueezy/checkout → backend checkout URL alır → frontend Lemon.js overlay açar
  2. Kullanıcı ödeme yapar → LS webhook gönderir → backend POST /api/v1/lemonsqueezy/webhook alır
  3. Backend signature doğrular → event'i idempotent olarak işler → credit/subscription oluşturur
  4. Frontend POST /api/v1/lemonsqueezy/portal → customer LS portal'ına yönlenir (subscription manage)

Webhook event'leri (13 tane, hepsi handle ediliyor):
  - order_created                    → one-time payment (disposable) veya sub ilk ödeme
  - order_refunded                   → para iadesi
  - subscription_created             → yeni subscription
  - subscription_updated             → durum/plan değişikliği
  - subscription_cancelled           → iptal (dönem sonunda biter)
  - subscription_resumed             → iptali geri al
  - subscription_expired             → tamamen sona erdi
  - subscription_paused              → geçici durdurma
  - subscription_unpaused            → durdurmadan döndü
  - subscription_payment_success     → ödeme alındı (initial veya renewal)
  - subscription_payment_failed      → ödeme alınamadı (past_due)
  - subscription_payment_recovered   → past_due'dan kurtuldu
  - customer_updated                 → email/isim güncelleme
"""
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends, Header, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database.connection import get_db
from src.database.models import (
    User, Plan, Subscription, CreditLedger, LemonSqueezyWebhookEvent
)
from src.database.credit_service import CreditService
from src.api.auth import get_current_user
from src.services.lemonsqueezy_service import (
    LemonSqueezyClient,
    verify_webhook_signature,
    LemonSqueezySignatureError,
    LemonSqueezyError,
)
from src.services.notification_service import (
    notify_new_subscription,
    notify_one_time_payment,
    notify_subscription_cancelled,
    notify_payment_failed,
    notify_refund,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# REQUEST / RESPONSE MODELLERİ
# ============================================

class CheckoutRequest(BaseModel):
    """Frontend'den gelen checkout başlatma isteği."""
    plan_slug: str = Field(
        ...,
        description="Plan slug: disposable, starter, pro, business"
    )
    billing_period: str = Field(
        "monthly",
        description="Faturalama periyodu: 'monthly' veya 'yearly'",
    )
    redirect_url: Optional[str] = Field(
        None,
        description="Ödeme sonrası dönülecek URL (overlay için fallback)"
    )


class CheckoutResponse(BaseModel):
    """Frontend'e dönen — Lemon.js overlay'ı buraya açacak."""
    checkout_id: str
    checkout_url: str
    plan_slug: str
    plan_name: str
    expires_at: Optional[str] = None


class PortalResponse(BaseModel):
    """Customer portal URL."""
    portal_url: str


# ============================================
# CHECKOUT ENDPOINT (Auth gerekli)
# ============================================

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lemon Squeezy checkout için URL oluştur.

    Akış:
      1. Plan'ı veritabanından al, lemonsqueezy_variant_id'sini doğrula
      2. LS'a checkout oluştur, custom_data'ya user_id ve plan_slug koy
      3. Frontend dönen URL'i Lemon.js ile açar (overlay) veya direkt redirect
      4. Customer LS tarafında otomatik oluşur, customer_id webhook'ta gelir
    """
    # Plan kontrolü
    plan = db.query(Plan).filter(
        Plan.slug == request.plan_slug,
        Plan.is_active == True,
    ).first()

    if not plan:
        raise HTTPException(404, f"Plan bulunamadı: {request.plan_slug}")

    # Enterprise self-serve değil — atla
    if plan.slug == "enterprise":
        raise HTTPException(
            400,
            "Enterprise planı self-serve checkout ile satılamaz. "
            "Lütfen sales@simutarget.ai adresine yazın."
        )

    # Faturalama periyodu doğrula
    billing_period = (request.billing_period or "monthly").lower()
    if billing_period not in ("monthly", "yearly"):
        raise HTTPException(400, f"Geçersiz billing_period: {request.billing_period}")

    # Periyoda göre variant seç
    if billing_period == "yearly":
        variant_id = plan.lemonsqueezy_yearly_variant_id
    else:
        variant_id = plan.lemonsqueezy_variant_id

    if not variant_id:
        raise HTTPException(
            400,
            f"Plan '{plan.name}' için '{billing_period}' variant tanımlı değil "
            "(LS variant ID boş). LS dashboard'da variant oluşturup plans "
            "tablosuna yazın."
        )

    # LS ile haberleş
    try:
        async with LemonSqueezyClient() as ls:
            checkout = await ls.create_checkout(
                variant_id=variant_id,
                user_email=user.email,
                user_name=user.name,
                custom_data={
                    "user_id": user.id,
                    "plan_slug": plan.slug,
                    "plan_id": plan.id,
                    "billing_period": billing_period,
                },
                redirect_url=request.redirect_url,
                embed=True,  # Lemon.js overlay için
            )
    except LemonSqueezyError as e:
        logger.exception(f"LS checkout hatası — user_id={user.id}, plan={request.plan_slug}")
        raise HTTPException(502, f"Lemon Squeezy hizmeti şu an cevap vermiyor: {str(e)}")

    return CheckoutResponse(
        checkout_id=checkout["id"],
        checkout_url=checkout["url"],
        plan_slug=plan.slug,
        plan_name=plan.name,
        expires_at=checkout.get("expires_at"),
    )


# ============================================
# CUSTOMER PORTAL ENDPOINT (Auth gerekli)
# ============================================

@router.post("/portal", response_model=PortalResponse)
async def get_customer_portal(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Customer portal URL'i al.

    Kullanıcı 'Manage subscription' butonuna basınca bu URL'e yönlendiriyoruz.
    LS'in kendi UI'ında subscription'ını yönetir, fatura indirir, kart günceller.
    """
    if not user.lemonsqueezy_customer_id:
        raise HTTPException(
            404,
            "Henüz Lemon Squeezy hesabı oluşturulmadı. Önce bir abonelik satın alın."
        )

    try:
        async with LemonSqueezyClient() as ls:
            portal_url = await ls.get_customer_portal_url(user.lemonsqueezy_customer_id)
    except LemonSqueezyError as e:
        logger.exception(f"Portal URL hatası — user_id={user.id}")
        raise HTTPException(502, f"Lemon Squeezy hizmeti şu an cevap vermiyor: {str(e)}")

    return PortalResponse(portal_url=portal_url)


# ============================================
# WEBHOOK ENDPOINT (Auth YOK — signature ile doğrulanır)
# ============================================

@router.post("/webhook")
async def lemonsqueezy_webhook(
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_event_name: Optional[str] = Header(None, alias="X-Event-Name"),
    db: Session = Depends(get_db),
):
    """
    Lemon Squeezy webhook receiver.

    Auth gerektirmez — onun yerine her request'in `X-Signature` header'ı
    HMAC-SHA256 ile doğrulanır. Yanlış signature ise 401 dönülür.

    Idempotency: LS unique event_id GÖNDERMEZ. Backend raw_body'nin
    SHA256 hash'ini event_id olarak kullanır. Aynı body 2 kez gelirse aynı
    hash → UNIQUE constraint yakalar → 2. çağrıda noop dönülür.
    """
    # Raw body al — signature doğrulaması için gerekli (parsed JSON DEĞİL)
    raw_body = await request.body()

    # Signature doğrula
    try:
        is_valid = verify_webhook_signature(
            raw_body=raw_body,
            signature_header=x_signature or "",
        )
    except LemonSqueezySignatureError as e:
        logger.error(f"Webhook signature hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Signature doğrulanamadı: {str(e)}",
        )

    if not is_valid:
        logger.error(f"Webhook signature mismatch — header: {x_signature}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature mismatch",
        )

    # JSON parse
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Webhook JSON parse hatası: {e}")
        raise HTTPException(400, "Geçersiz JSON")

    # Event name'i payload'dan al (öncelik), header'dan fallback
    meta = payload.get("meta") or {}
    event_name = meta.get("event_name") or x_event_name

    if not event_name:
        raise HTTPException(400, "event_name eksik (ne payload.meta'da ne X-Event-Name header'da)")

    # Idempotency key: raw_body SHA256 hash
    event_id = hashlib.sha256(raw_body).hexdigest()

    # Idempotency kontrolü
    existing_event = db.query(LemonSqueezyWebhookEvent).filter(
        LemonSqueezyWebhookEvent.event_id == event_id
    ).first()

    if existing_event and existing_event.processed_at:
        logger.info(f"Webhook event zaten işlenmiş: {event_id} ({event_name})")
        return {"status": "already_processed", "event_id": event_id}

    # Event'i kaydet
    if not existing_event:
        webhook_event = LemonSqueezyWebhookEvent(
            event_id=event_id,
            event_name=event_name,
            payload=payload,
        )
        db.add(webhook_event)
        try:
            db.commit()
        except IntegrityError:
            # Race condition — başka request aynı event'i kaydetti
            db.rollback()
            logger.info(f"Webhook event race condition: {event_id}")
            return {"status": "race_skipped", "event_id": event_id}
    else:
        webhook_event = existing_event

    # Event'i işle
    try:
        await _process_event(event_name, payload, db)
        webhook_event.processed_at = datetime.utcnow()
        db.commit()
    except Exception as e:
        logger.exception(f"Webhook event işleme hatası: {event_id} ({event_name})")
        webhook_event.processing_error = str(e)
        db.commit()
        # LS 500 alırsa retry yapar; biz hatayı kaydettik, retry'da idempotency kontrol edilecek
        raise HTTPException(500, f"Event işlenemedi: {str(e)}")

    return {"status": "processed", "event_id": event_id, "event_name": event_name}


# ============================================
# WEBHOOK EVENT PROCESSING (internal)
# ============================================

async def _process_event(event_name: str, payload: dict, db: Session):
    """Event tipine göre uygun handler'ı çağır."""
    handlers = {
        "order_created": _handle_order_created,
        "order_refunded": _handle_order_refunded,
        "subscription_created": _handle_subscription_created,
        "subscription_updated": _handle_subscription_updated,
        "subscription_cancelled": _handle_subscription_cancelled,
        "subscription_resumed": _handle_subscription_resumed,
        "subscription_expired": _handle_subscription_expired,
        "subscription_paused": _handle_subscription_paused,
        "subscription_unpaused": _handle_subscription_unpaused,
        "subscription_payment_success": _handle_subscription_payment_success,
        "subscription_payment_failed": _handle_subscription_payment_failed,
        "subscription_payment_recovered": _handle_subscription_payment_recovered,
        "customer_updated": _handle_customer_updated,
    }

    handler = handlers.get(event_name)
    if not handler:
        logger.info(f"Webhook event türü işlenmiyor (skip): {event_name}")
        return

    handler(payload, db)


# ============================================
# HELPER FUNCTIONS
# ============================================

def _get_custom_data(payload: dict) -> dict:
    """LS payload'undan custom_data'yı çıkar (meta seviyesinde)."""
    meta = payload.get("meta") or {}
    return meta.get("custom_data") or {}


def _get_attributes(payload: dict) -> dict:
    """LS payload'undan data.attributes'i çıkar."""
    data = payload.get("data") or {}
    return data.get("attributes") or {}


def _get_data_id(payload: dict) -> Optional[str]:
    """LS payload'undan data.id'yi çıkar (her zaman string)."""
    data = payload.get("data") or {}
    return str(data["id"]) if data.get("id") is not None else None


def _get_user_from_custom_data(custom_data: dict, db: Session) -> Optional[User]:
    """custom_data['user_id']'den User'ı getir. LS string olarak gönderdiği için int'e çevir."""
    user_id = custom_data.get("user_id") if custom_data else None
    if not user_id:
        return None
    try:
        return db.query(User).filter(User.id == int(user_id)).first()
    except (ValueError, TypeError):
        return None


def _get_plan_from_custom_data(custom_data: dict, db: Session) -> Optional[Plan]:
    """custom_data['plan_slug']'den Plan'ı getir."""
    plan_slug = custom_data.get("plan_slug") if custom_data else None
    if not plan_slug:
        return None
    return db.query(Plan).filter(Plan.slug == plan_slug).first()


def _get_plan_from_variant_id(variant_id, db: Session) -> Optional[Plan]:
    """LS variant_id ile Plan'ı bul (custom_data yoksa fallback)."""
    if variant_id is None:
        return None
    return db.query(Plan).filter(
        Plan.lemonsqueezy_variant_id == str(variant_id)
    ).first()


def _map_ls_status(ls_status: str) -> str:
    """
    LS subscription status → bizim DB status enum.

    LS statuses: active, on_trial, paused, past_due, unpaid, cancelled, expired
    Bizim:       active, paused,   paused, past_due, past_due, cancelled, cancelled
    """
    mapping = {
        "active": "active",
        "on_trial": "active",
        "paused": "paused",
        "past_due": "past_due",
        "unpaid": "past_due",
        "cancelled": "cancelled",
        "expired": "cancelled",
    }
    return mapping.get(ls_status, "active")


def _parse_ls_datetime(value: Optional[str]) -> Optional[datetime]:
    """LS ISO 8601 datetime string → naive UTC datetime."""
    if not value:
        return None
    try:
        # LS: "2026-06-07T15:30:00.000000Z"
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        # Naive UTC'ye çevir (modelde naive kullanılıyor)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except (ValueError, TypeError):
        logger.warning(f"LS datetime parse hatası: {value}")
        return None


# ============================================
# ORDER HANDLERS
# ============================================

def _handle_order_created(payload: dict, db: Session):
    """
    Order tamamlandı (one-time veya subscription ilk ödeme).

    İki durum:
      A) Disposable (one-time): Subscription oluşturma, sadece credit ekle
      B) Subscription ilk ödeme: subscription_created event'i de gelecek,
         burada bir şey yapma — credit grant orada olacak.
    """
    custom_data = _get_custom_data(payload)
    attrs = _get_attributes(payload)

    user = _get_user_from_custom_data(custom_data, db)
    plan = _get_plan_from_custom_data(custom_data, db)

    if not user or not plan:
        logger.warning(
            f"order_created — user veya plan bulunamadı, custom_data: {custom_data}"
        )
        return

    order_id = _get_data_id(payload)

    # Sadece disposable için credit ekle (subscription'lar subscription event'lerinde işlenir)
    if plan.slug != "disposable":
        logger.info(
            f"order_created — disposable değil ({plan.slug}), "
            f"subscription event'inde işlenecek. order_id={order_id}"
        )
        return

    # Idempotency: aynı order için credit zaten eklendi mi?
    existing_credit = db.query(CreditLedger).filter(
        CreditLedger.user_id == user.id,
        CreditLedger.reference_id == order_id,
        CreditLedger.type == "topup",
    ).first()

    if existing_credit:
        logger.info(f"Disposable credit zaten eklenmiş: order_id={order_id}")
        return

    # User'ın lemonsqueezy_customer_id'sini güncelle (yoksa)
    ls_customer_id = attrs.get("customer_id")
    if not user.lemonsqueezy_customer_id and ls_customer_id is not None:
        user.lemonsqueezy_customer_id = str(ls_customer_id)

    # Disposable: plan.credits_monthly kadar credit ekle
    credit_service = CreditService(db)
    credit_service.topup_credits(
        user_id=user.id,
        amount=plan.credits_monthly,
        expires_at=datetime.utcnow() + timedelta(days=30),
    )

    # Reference'ı güncelle
    last_entry = db.query(CreditLedger).filter(
        CreditLedger.user_id == user.id
    ).order_by(CreditLedger.id.desc()).first()
    if last_entry:
        last_entry.reference_id = order_id
        last_entry.description = f"Disposable test pack — {plan.credits_monthly} credit"
        db.commit()

    logger.info(
        f"Disposable credit eklendi: user_id={user.id}, "
        f"amount={plan.credits_monthly}, order_id={order_id}"
    )

    # Telegram bildirimi (fire-and-forget)
    try:
        # LS total cent → dollar
        amount_cents = attrs.get("total") or 0
        amount_usd = amount_cents / 100 if amount_cents else None
        notify_one_time_payment(
            email=user.email,
            product=plan.name,
            amount_usd=amount_usd,
            order_id=order_id,
        )
    except Exception as e:
        logger.warning(f"order_created bildirimi gönderilemedi: {e}")


def _handle_order_refunded(payload: dict, db: Session):
    """
    Order iade edildi — bu order için verilen kredileri geri al.

    Akış:
      1. User'ı bul (custom_data veya LS customer_id ile)
      2. Bu order için verilmiş orijinal credit entry'leri bul (topup veya grant)
      3. Idempotency: zaten refund edilmiş mi kontrol et
      4. Refund miktarını mevcut bakiye ile capla (kullanıcı zaten harcadıysa
         negative bakiyeye düşürmüyoruz — para iadesi LS tarafında yapılır)
      5. CreditLedger'a negatif entry yaz (type='expire', refund açıklaması)
    """
    attrs = _get_attributes(payload)
    order_id = _get_data_id(payload)
    ls_customer_id = attrs.get("customer_id")
    refund_amount_dollars = attrs.get("total_usd", 0) / 100  # cent → dollar (log için)

    # User'ı bulmaya çalış (custom_data yoksa customer_id ile)
    user = None
    custom_data = _get_custom_data(payload)
    if custom_data:
        user = _get_user_from_custom_data(custom_data, db)
    if not user and ls_customer_id is not None:
        user = db.query(User).filter(
            User.lemonsqueezy_customer_id == str(ls_customer_id)
        ).first()

    if not user:
        logger.warning(
            f"order_refunded — user bulunamadı, order_id={order_id}, "
            f"ls_customer_id={ls_customer_id}, amount=${refund_amount_dollars:.2f}"
        )
        return

    # Bu order için verilen orijinal credit entry'leri bul
    original_entries = db.query(CreditLedger).filter(
        CreditLedger.user_id == user.id,
        CreditLedger.reference_id == order_id,
        CreditLedger.type.in_(["topup", "grant"]),
        CreditLedger.amount > 0,
    ).all()

    if not original_entries:
        logger.warning(
            f"order_refunded — bu order için orijinal credit entry yok "
            f"(disposable değil veya henüz işlenmemiş). "
            f"user_id={user.id}, order_id={order_id}"
        )
        return

    # Idempotency: bu order için zaten refund yapıldı mı?
    existing_refund = db.query(CreditLedger).filter(
        CreditLedger.user_id == user.id,
        CreditLedger.reference_id == order_id,
        CreditLedger.type == "expire",
        CreditLedger.amount < 0,
    ).first()

    if existing_refund:
        logger.info(f"Order zaten refund edildi: order_id={order_id}")
        return

    # Toplam refund edilecek miktar (orijinal verilen)
    total_to_refund = sum(e.amount for e in original_entries)

    # Şu anki bakiye
    last_entry = db.query(CreditLedger).filter(
        CreditLedger.user_id == user.id
    ).order_by(CreditLedger.id.desc()).first()
    current_balance = last_entry.balance_after if last_entry else 0

    # Bakiye yetmiyorsa (kullanıcı zaten harcadı) sadece kalanı düş, negative gitmiyoruz
    actual_refund = min(total_to_refund, current_balance)

    if actual_refund <= 0:
        # Kullanıcı tüm krediyi harcamış — refund yapacak credit yok ama yine de
        # idempotency için bir kayıt bırakalım (0 amount, açıklayıcı)
        logger.warning(
            f"order_refunded — kullanıcı tüm krediyi harcamış, credit refund 0. "
            f"user_id={user.id}, order_id={order_id}, would_refund={total_to_refund}, "
            f"current_balance={current_balance}, money_refund=${refund_amount_dollars:.2f}"
        )
        # 0 amount entry — gelecekteki idempotency check için
        zero_entry = CreditLedger(
            user_id=user.id,
            amount=0,
            type="expire",
            balance_after=current_balance,
            reference_id=order_id,
            description=f"Refund order #{order_id} — kullanılmış, credit düşümü yok",
        )
        db.add(zero_entry)
        db.commit()
        return

    new_balance = current_balance - actual_refund

    refund_entry = CreditLedger(
        user_id=user.id,
        amount=-actual_refund,
        type="expire",
        balance_after=new_balance,
        reference_id=order_id,
        description=f"Refund order #{order_id} — ${refund_amount_dollars:.2f} iade",
    )
    db.add(refund_entry)
    db.commit()

    logger.info(
        f"Order refund: user_id={user.id}, order_id={order_id}, "
        f"credits_refunded={actual_refund}, money_refund=${refund_amount_dollars:.2f}"
    )

    # Telegram bildirimi (fire-and-forget)
    try:
        notify_refund(
            email=user.email,
            amount_usd=refund_amount_dollars,
            order_id=order_id,
        )
    except Exception as e:
        logger.warning(f"order_refunded bildirimi gönderilemedi: {e}")


# ============================================
# SUBSCRIPTION HANDLERS
# ============================================

def _handle_subscription_created(payload: dict, db: Session):
    """
    Yeni subscription oluşturuldu.

    Bizim DB'mizde Subscription kaydı oluştur, plan kredisini yükle.
    """
    custom_data = _get_custom_data(payload)
    attrs = _get_attributes(payload)

    user = _get_user_from_custom_data(custom_data, db)
    plan = _get_plan_from_custom_data(custom_data, db)

    # Fallback: variant_id ile plan bul
    if not plan:
        plan = _get_plan_from_variant_id(attrs.get("variant_id"), db)

    if not user or not plan:
        logger.warning(
            f"subscription_created — user veya plan yok, "
            f"custom_data: {custom_data}, variant_id: {attrs.get('variant_id')}"
        )
        return

    # Faturalama periyodu: custom_data öncelikli, yoksa variant_id ile çıkar
    billing_period = (custom_data.get("billing_period") or "").lower()
    if billing_period not in ("monthly", "yearly"):
        incoming_variant = attrs.get("variant_id")
        if (
            plan.lemonsqueezy_yearly_variant_id
            and incoming_variant is not None
            and str(incoming_variant) == str(plan.lemonsqueezy_yearly_variant_id)
        ):
            billing_period = "yearly"
        else:
            billing_period = "monthly"

    ls_sub_id = _get_data_id(payload)
    ls_customer_id = attrs.get("customer_id")
    ls_order_id = attrs.get("order_id")

    # Idempotency: bu lemonsqueezy_subscription_id zaten var mı?
    existing = db.query(Subscription).filter(
        Subscription.lemonsqueezy_subscription_id == ls_sub_id
    ).first()

    if existing:
        logger.info(f"Subscription zaten var: ls_sub_id={ls_sub_id}")
        return

    # Önceki aktif subscription'ı iptal et (varsa) — kullanıcı plan değiştirmiş olabilir
    old_sub = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active",
    ).first()

    if old_sub:
        old_sub.status = "cancelled"
        old_sub.cancel_at = datetime.utcnow()
        # Eski kredileri sıfırla
        credit_service = CreditService(db)
        credit_service.expire_credits(user.id)

    # Periyot bilgilerini al
    # LS: created_at = period_start, renews_at = period_end
    period_start = _parse_ls_datetime(attrs.get("created_at")) or datetime.utcnow()
    period_end = _parse_ls_datetime(attrs.get("renews_at"))
    if not period_end:
        # Fallback: şu an + 30 gün
        period_end = period_start + timedelta(days=30)

    # User'ın lemonsqueezy_customer_id'sini güncelle (yoksa)
    if not user.lemonsqueezy_customer_id and ls_customer_id is not None:
        user.lemonsqueezy_customer_id = str(ls_customer_id)

    # Yeni Subscription oluştur
    subscription = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        status=_map_ls_status(attrs.get("status", "active")),
        current_period_start=period_start,
        current_period_end=period_end,
        billing_period=billing_period,
        lemonsqueezy_subscription_id=ls_sub_id,
        lemonsqueezy_customer_id=str(ls_customer_id) if ls_customer_id is not None else None,
        lemonsqueezy_order_id=str(ls_order_id) if ls_order_id is not None else None,
    )
    db.add(subscription)
    db.flush()

    # Plan kredisini yükle.
    # Option A: yıllık abone 12 ay kredisini peşin alır, dönem sonuna (1 yıl) kadar geçerli.
    credit_amount = plan.credits_monthly * 12 if billing_period == "yearly" else plan.credits_monthly

    credit_service = CreditService(db)
    credit_service.grant_credits(
        user_id=user.id,
        amount=credit_amount,
        description=f"{plan.name} aktivasyonu ({billing_period}) — {credit_amount} credit",
        expires_at=period_end,
    )

    db.commit()

    logger.info(
        f"Subscription oluşturuldu: user_id={user.id}, plan={plan.slug}, "
        f"ls_sub_id={ls_sub_id}, credits={plan.credits_monthly}"
    )

    # Telegram bildirimi (fire-and-forget)
    try:
        if billing_period == "yearly" and plan.price_yearly:
            amount_usd = float(plan.price_yearly)
        else:
            amount_usd = float(plan.price_monthly) if plan.price_monthly else None
        notify_new_subscription(
            email=user.email,
            plan=plan.name,
            amount_usd=amount_usd,
            subscription_id=ls_sub_id,
            is_renewal=False,
        )
    except Exception as e:
        logger.warning(f"subscription_created bildirimi gönderilemedi: {e}")


def _handle_subscription_updated(payload: dict, db: Session):
    """
    Subscription güncellendi (status değişikliği, plan değişikliği vb.).

    NOT: Yenileme (renewal) için bu event GELMEZ — onun için
    subscription_payment_success kullanılır.
    """
    attrs = _get_attributes(payload)
    ls_sub_id = _get_data_id(payload)

    sub = db.query(Subscription).filter(
        Subscription.lemonsqueezy_subscription_id == ls_sub_id
    ).first()

    if not sub:
        logger.warning(f"subscription_updated — sub bulunamadı: {ls_sub_id}")
        return

    # Status güncelle
    new_status = _map_ls_status(attrs.get("status", "active"))
    sub.status = new_status

    # Plan değişikliği (upgrade/downgrade) kontrolü
    new_variant_id = attrs.get("variant_id")
    if new_variant_id is not None:
        new_plan = _get_plan_from_variant_id(new_variant_id, db)
        if new_plan and new_plan.id != sub.plan_id:
            old_plan_id = sub.plan_id
            sub.plan_id = new_plan.id
            logger.info(
                f"Subscription plan değişti: ls_sub_id={ls_sub_id}, "
                f"old_plan_id={old_plan_id}, new_plan_id={new_plan.id}"
            )
            # NOT: Plan değişiminde credit ayarlaması yapmıyoruz şu an —
            # bir sonraki renewal'da yeni plan'ın credit'i otomatik gelecek.

    # Renewal date değişti mi (güncellenebilir)
    renews_at = _parse_ls_datetime(attrs.get("renews_at"))
    if renews_at and renews_at > sub.current_period_end:
        sub.current_period_end = renews_at

    db.commit()
    logger.info(f"Subscription güncellendi: ls_sub_id={ls_sub_id}, status={new_status}")


def _handle_subscription_cancelled(payload: dict, db: Session):
    """
    Subscription iptal edildi (kullanıcı iptal etti).

    LS davranışı: status='cancelled' ama dönem sonuna kadar erişim devam eder.
    Subscription dönem bittiğinde subscription_expired event'i gelir.
    """
    attrs = _get_attributes(payload)
    ls_sub_id = _get_data_id(payload)

    sub = db.query(Subscription).filter(
        Subscription.lemonsqueezy_subscription_id == ls_sub_id
    ).first()

    if not sub:
        logger.warning(f"subscription_cancelled — sub bulunamadı: {ls_sub_id}")
        return

    sub.status = "cancelled"
    # ends_at = ne zaman tamamen biteceği (genelde current_period_end ile aynı)
    ends_at = _parse_ls_datetime(attrs.get("ends_at"))
    sub.cancel_at = ends_at or datetime.utcnow()
    db.commit()

    logger.info(f"Subscription iptal: ls_sub_id={ls_sub_id}, ends_at={ends_at}")

    # Telegram bildirimi (fire-and-forget)
    try:
        user = db.query(User).filter(User.id == sub.user_id).first()
        plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
        if user and plan:
            notify_subscription_cancelled(
                email=user.email,
                plan=plan.name,
                subscription_id=ls_sub_id,
                ends_at=ends_at,
            )
    except Exception as e:
        logger.warning(f"subscription_cancelled bildirimi gönderilemedi: {e}")


def _handle_subscription_resumed(payload: dict, db: Session):
    """Kullanıcı iptali geri aldı — subscription tekrar aktif."""
    ls_sub_id = _get_data_id(payload)
    sub = db.query(Subscription).filter(
        Subscription.lemonsqueezy_subscription_id == ls_sub_id
    ).first()

    if not sub:
        logger.warning(f"subscription_resumed — sub bulunamadı: {ls_sub_id}")
        return

    sub.status = "active"
    sub.cancel_at = None
    db.commit()
    logger.info(f"Subscription geri alındı: ls_sub_id={ls_sub_id}")


def _handle_subscription_expired(payload: dict, db: Session):
    """
    Subscription tamamen sona erdi (cancelled sonrası dönem bitti veya unpaid sonrası terminate).

    Krediyi sıfırla, kullanıcı artık plan özelliklerine erişemez.
    """
    ls_sub_id = _get_data_id(payload)
    sub = db.query(Subscription).filter(
        Subscription.lemonsqueezy_subscription_id == ls_sub_id
    ).first()

    if not sub:
        logger.warning(f"subscription_expired — sub bulunamadı: {ls_sub_id}")
        return

    sub.status = "cancelled"
    sub.current_period_end = datetime.utcnow()  # Şu an itibariyle bitti

    # Kredileri expire et
    credit_service = CreditService(db)
    credit_service.expire_credits(sub.user_id)

    db.commit()
    logger.info(f"Subscription sona erdi: ls_sub_id={ls_sub_id}, user_id={sub.user_id}")


def _handle_subscription_paused(payload: dict, db: Session):
    """Subscription geçici durduruldu (LS feature)."""
    ls_sub_id = _get_data_id(payload)
    sub = db.query(Subscription).filter(
        Subscription.lemonsqueezy_subscription_id == ls_sub_id
    ).first()

    if not sub:
        return

    sub.status = "paused"
    db.commit()
    logger.info(f"Subscription duraklatıldı: ls_sub_id={ls_sub_id}")


def _handle_subscription_unpaused(payload: dict, db: Session):
    """Subscription duraklatmadan döndü."""
    ls_sub_id = _get_data_id(payload)
    sub = db.query(Subscription).filter(
        Subscription.lemonsqueezy_subscription_id == ls_sub_id
    ).first()

    if not sub:
        return

    sub.status = "active"
    db.commit()
    logger.info(f"Subscription devam ediyor: ls_sub_id={ls_sub_id}")


def _handle_subscription_payment_success(payload: dict, db: Session):
    """
    Aylık ödeme başarılı.

    İki tip:
      A) billing_reason='initial' → ilk ödeme, subscription_created handle ediyor, atla
      B) billing_reason='renewal' → renewal, yeni dönem başlat, kredi yenile

    LS subscription_payment_success event'i 'subscription-invoices' tipinde gelir,
    subscription_id attribute'unda referans var.
    """
    attrs = _get_attributes(payload)
    ls_sub_id = attrs.get("subscription_id")
    billing_reason = attrs.get("billing_reason", "")

    if not ls_sub_id:
        logger.warning(f"subscription_payment_success — subscription_id yok, attrs: {attrs}")
        return

    sub = db.query(Subscription).filter(
        Subscription.lemonsqueezy_subscription_id == str(ls_sub_id)
    ).first()

    if not sub:
        logger.warning(f"subscription_payment_success — sub bulunamadı: {ls_sub_id}")
        return

    # Status'u active'e çek (past_due'dan dönmüş olabilir)
    sub.status = "active"

    # Sadece renewal için yeni dönem + kredi yenileme
    if billing_reason == "renewal":
        new_period_start = _parse_ls_datetime(attrs.get("created_at")) or datetime.utcnow()
        # Dönem uzunluğu faturalama periyoduna göre (yıllık 365, aylık 30 gün)
        period_days = 365 if sub.billing_period == "yearly" else 30
        new_period_end = new_period_start + timedelta(days=period_days)

        # Sadece gerçekten ileri bir tarihse güncelle (idempotency koruması)
        if new_period_start > sub.current_period_start:
            sub.current_period_start = new_period_start
            sub.current_period_end = new_period_end

            # Plan'ı al, krediyi yenile
            plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
            if plan:
                # Option A: yıllıkta 12 ay peşin, aylıkta 1 ay
                credit_amount = (
                    plan.credits_monthly * 12
                    if sub.billing_period == "yearly"
                    else plan.credits_monthly
                )
                credit_service = CreditService(db)
                # Önce eski dönemden kalan kredileri sıfırla
                credit_service.expire_credits(sub.user_id)
                # Yeni dönem kredisi
                credit_service.grant_credits(
                    user_id=sub.user_id,
                    amount=credit_amount,
                    description=f"{plan.name} dönem yenileme ({sub.billing_period}) — {credit_amount} credit",
                    expires_at=new_period_end,
                )

                logger.info(
                    f"Subscription yenilendi: user_id={sub.user_id}, "
                    f"plan={plan.slug}, ls_sub_id={ls_sub_id}"
                )

                # Telegram bildirimi (sadece renewal — initial subscription_created'da bildirildi)
                try:
                    user = db.query(User).filter(User.id == sub.user_id).first()
                    if user:
                        if sub.billing_period == "yearly" and plan.price_yearly:
                            amount_usd = float(plan.price_yearly)
                        else:
                            amount_usd = float(plan.price_monthly) if plan.price_monthly else None
                        notify_new_subscription(
                            email=user.email,
                            plan=plan.name,
                            amount_usd=amount_usd,
                            subscription_id=str(ls_sub_id),
                            is_renewal=True,
                        )
                except Exception as e:
                    logger.warning(f"renewal bildirimi gönderilemedi: {e}")

    db.commit()


def _handle_subscription_payment_failed(payload: dict, db: Session):
    """Ödeme alınamadı — past_due'ya çek. LS retry yapacak."""
    attrs = _get_attributes(payload)
    ls_sub_id = attrs.get("subscription_id")

    if not ls_sub_id:
        return

    sub = db.query(Subscription).filter(
        Subscription.lemonsqueezy_subscription_id == str(ls_sub_id)
    ).first()

    if not sub:
        return

    sub.status = "past_due"
    db.commit()
    logger.warning(f"Subscription ödeme başarısız: ls_sub_id={ls_sub_id}")

    # Telegram bildirimi (fire-and-forget)
    try:
        user = db.query(User).filter(User.id == sub.user_id).first()
        plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
        if user and plan:
            notify_payment_failed(
                email=user.email,
                plan=plan.name,
                subscription_id=str(ls_sub_id),
            )
    except Exception as e:
        logger.warning(f"payment_failed bildirimi gönderilemedi: {e}")


def _handle_subscription_payment_recovered(payload: dict, db: Session):
    """Past_due'dan kurtuldu — ödeme tahsil edildi."""
    attrs = _get_attributes(payload)
    ls_sub_id = attrs.get("subscription_id")

    if not ls_sub_id:
        return

    sub = db.query(Subscription).filter(
        Subscription.lemonsqueezy_subscription_id == str(ls_sub_id)
    ).first()

    if not sub:
        return

    sub.status = "active"
    db.commit()
    logger.info(f"Subscription ödeme kurtarıldı: ls_sub_id={ls_sub_id}")


# ============================================
# CUSTOMER HANDLERS
# ============================================

def _handle_customer_updated(payload: dict, db: Session):
    """LS'te customer email/isim değişti — User'a sync et."""
    attrs = _get_attributes(payload)
    ls_customer_id = _get_data_id(payload)
    new_email = attrs.get("email")
    new_name = attrs.get("name")

    if not ls_customer_id:
        return

    user = db.query(User).filter(
        User.lemonsqueezy_customer_id == ls_customer_id
    ).first()

    if not user:
        logger.info(f"customer_updated — user bulunamadı: ls_customer_id={ls_customer_id}")
        return

    changed = False
    # NOT: Email değişimi hassas — kullanıcı LS'te değiştirdi diye bizim DB'de
    # değiştirmek auth/login akışını bozabilir. Şimdilik sadece name güncelliyoruz.
    if new_name and new_name != user.name:
        user.name = new_name
        changed = True

    if changed:
        db.commit()
        logger.info(f"User güncellendi: user_id={user.id}, ls_customer_id={ls_customer_id}")