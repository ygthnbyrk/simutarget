"""
Paddle Billing entegrasyonu — webhook handler ve checkout endpoints.

Akış:
  1. Frontend POST /api/v1/paddle/checkout → backend transaction yaratır → frontend Paddle.Checkout.open()
  2. Kullanıcı ödeme yapar → Paddle webhook gönderir → backend POST /api/v1/paddle/webhook alır
  3. Backend signature doğrular → event'i idempotent olarak işler → credit/subscription oluşturur
  4. Frontend POST /api/v1/paddle/portal → customer Paddle portal'ına yönlenir (subscription manage)

Webhook event'leri:
  - transaction.completed   → one-time payment veya subscription ilk ödeme
  - transaction.paid        → ödeme alındı
  - subscription.created    → yeni subscription
  - subscription.activated  → aktif oldu
  - subscription.updated    → plan değişikliği vb.
  - subscription.canceled   → iptal
  - subscription.past_due   → ödeme alınamadı
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends, Header, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database.connection import get_db
from src.database.models import (
    User, Plan, Subscription, CreditLedger, PaddleWebhookEvent
)
from src.database.credit_service import CreditService
from src.api.auth import get_current_user
from src.services.paddle_service import (
    PaddleClient,
    verify_webhook_signature,
    PaddleSignatureError,
    PaddleError,
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


class CheckoutResponse(BaseModel):
    """Frontend'e dönen — Paddle.Checkout.open() için gerekli."""
    transaction_id: str
    customer_id: str
    plan_slug: str
    plan_name: str


class PortalResponse(BaseModel):
    """Customer portal session URL."""
    portal_url: str
    expires_at: str


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
    Paddle checkout için transaction oluştur.

    Akış:
      1. Plan'ı veritabanından al, paddle_price_id'sini doğrula
      2. Kullanıcının Paddle customer'ı yoksa yarat, paddle_customer_id'yi User'a kaydet
      3. Paddle'a transaction oluştur, custom_data'ya user_id ve plan_slug koy
      4. Frontend transaction_id ile Paddle.Checkout.open() çağırır
    """
    # Plan kontrolü
    plan = db.query(Plan).filter(
        Plan.slug == request.plan_slug,
        Plan.is_active == True,
    ).first()

    if not plan:
        raise HTTPException(404, f"Plan bulunamadı: {request.plan_slug}")

    if not plan.paddle_price_id:
        raise HTTPException(
            400,
            f"Plan '{plan.name}' Paddle'a bağlı değil (paddle_price_id boş). "
            "Migration'ın çalıştığından ve price_id'lerin yüklendiğinden emin ol."
        )

    # Enterprise self-serve değil — atla
    if plan.slug == "enterprise":
        raise HTTPException(
            400,
            "Enterprise planı self-serve checkout ile satılamaz. "
            "Lütfen sales@simutarget.ai adresine yazın."
        )

    # Paddle ile haberleş
    try:
        async with PaddleClient() as paddle:
            # Customer get-or-create
            if user.paddle_customer_id:
                customer_id = user.paddle_customer_id
            else:
                customer = await paddle.get_or_create_customer(
                    email=user.email,
                    name=user.name,
                )
                customer_id = customer["id"]
                user.paddle_customer_id = customer_id
                db.commit()

            # Transaction yarat
            transaction = await paddle.create_transaction(
                price_id=plan.paddle_price_id,
                customer_id=customer_id,
                custom_data={
                    "user_id": user.id,
                    "plan_slug": plan.slug,
                    "plan_id": plan.id,
                },
            )
    except PaddleError as e:
        logger.exception(f"Paddle checkout hatası — user_id={user.id}, plan={request.plan_slug}")
        raise HTTPException(502, f"Paddle hizmeti şu an cevap vermiyor: {str(e)}")

    return CheckoutResponse(
        transaction_id=transaction["id"],
        customer_id=customer_id,
        plan_slug=plan.slug,
        plan_name=plan.name,
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
    Customer portal session URL'i al.

    Kullanıcı 'Manage subscription' butonuna basınca bu URL'e yönlendiriyoruz.
    Paddle'ın kendi UI'ında subscription'ını yönetir, fatura indirir, kart günceller.
    """
    if not user.paddle_customer_id:
        raise HTTPException(
            404,
            "Henüz Paddle hesabı oluşturulmadı. Önce bir abonelik satın alın."
        )

    try:
        async with PaddleClient() as paddle:
            session = await paddle.create_portal_session(user.paddle_customer_id)
    except PaddleError as e:
        logger.exception(f"Portal session hatası — user_id={user.id}")
        raise HTTPException(502, f"Paddle hizmeti şu an cevap vermiyor: {str(e)}")

    # Paddle response'unda urls.general.overview gibi alan döner
    urls = session.get("urls", {}).get("general", {})
    portal_url = urls.get("overview", "")

    return PortalResponse(
        portal_url=portal_url,
        expires_at=session.get("created_at", ""),
    )


# ============================================
# WEBHOOK ENDPOINT (Auth YOK — signature ile doğrulanır)
# ============================================

@router.post("/webhook")
async def paddle_webhook(
    request: Request,
    paddle_signature: Optional[str] = Header(None, alias="Paddle-Signature"),
    db: Session = Depends(get_db),
):
    """
    Paddle webhook receiver.

    Auth gerektirmez — onun yerine her request'in `Paddle-Signature` header'ı
    HMAC-SHA256 ile doğrulanır. Yanlış signature ise 401 dönülür.

    Idempotency: Aynı event_id 2 kez gelirse 2. seferde noop dönülür.
    """
    # Raw body al — signature doğrulaması için gerekli (parsed JSON DEĞİL)
    raw_body = await request.body()

    # Signature doğrula
    try:
        is_valid = verify_webhook_signature(
            raw_body=raw_body,
            signature_header=paddle_signature or "",
        )
    except PaddleSignatureError as e:
        logger.error(f"Webhook signature hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Signature doğrulanamadı: {str(e)}",
        )

    if not is_valid:
        logger.error(f"Webhook signature mismatch — header: {paddle_signature}")
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

    event_id = payload.get("event_id")
    event_type = payload.get("event_type")

    if not event_id or not event_type:
        raise HTTPException(400, "event_id veya event_type eksik")

    # Idempotency kontrolü — UNIQUE constraint'e güveniyoruz
    existing_event = db.query(PaddleWebhookEvent).filter(
        PaddleWebhookEvent.event_id == event_id
    ).first()

    if existing_event and existing_event.processed_at:
        logger.info(f"Webhook event zaten işlenmiş: {event_id}")
        return {"status": "already_processed", "event_id": event_id}

    # Event'i kaydet
    if not existing_event:
        webhook_event = PaddleWebhookEvent(
            event_id=event_id,
            event_type=event_type,
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
        await _process_event(event_type, payload, db)
        webhook_event.processed_at = datetime.utcnow()
        db.commit()
    except Exception as e:
        logger.exception(f"Webhook event işleme hatası: {event_id} ({event_type})")
        webhook_event.processing_error = str(e)
        db.commit()
        # Paddle 500 alırsa retry yapar; biz hatayı kaydettik, retry'da idempotency kontrol edilecek
        raise HTTPException(500, f"Event işlenemedi: {str(e)}")

    return {"status": "processed", "event_id": event_id, "event_type": event_type}


# ============================================
# WEBHOOK EVENT PROCESSING (internal)
# ============================================

async def _process_event(event_type: str, payload: dict, db: Session):
    """Event tipine göre uygun handler'ı çağır."""
    data = payload.get("data", {})

    handlers = {
        "transaction.completed": _handle_transaction_completed,
        "transaction.paid": _handle_transaction_completed,  # Aynı handler
        "subscription.created": _handle_subscription_created,
        "subscription.activated": _handle_subscription_activated,
        "subscription.updated": _handle_subscription_updated,
        "subscription.canceled": _handle_subscription_canceled,
        "subscription.past_due": _handle_subscription_past_due,
    }

    handler = handlers.get(event_type)
    if not handler:
        logger.info(f"Webhook event türü işlenmiyor (skip): {event_type}")
        return

    handler(data, db)


def _get_user_from_custom_data(custom_data: dict, db: Session) -> Optional[User]:
    """custom_data['user_id']'den User'ı getir."""
    user_id = custom_data.get("user_id") if custom_data else None
    if not user_id:
        return None
    return db.query(User).filter(User.id == int(user_id)).first()


def _get_plan_from_custom_data(custom_data: dict, db: Session) -> Optional[Plan]:
    """custom_data['plan_slug']'den Plan'ı getir."""
    plan_slug = custom_data.get("plan_slug") if custom_data else None
    if not plan_slug:
        return None
    return db.query(Plan).filter(Plan.slug == plan_slug).first()


# --------------------------------------------
# Transaction handlers
# --------------------------------------------

def _handle_transaction_completed(data: dict, db: Session):
    """
    Transaction tamamlandı.

    İki durum:
      A) Disposable (one-time): Subscription oluşturma, sadece 5 credit ekle
      B) Subscription ilk ödeme: subscription.created event'i de gelecek, burada
         bir şey yapma (veya credit'i burada da ekleyebiliriz, hangi event önce gelir
         garanti değil — best practice subscription event'inde yapmak).

    Disposable'ı burada işliyoruz çünkü subscription.created event'i gelmeyecek.
    """
    custom_data = data.get("custom_data") or {}
    user = _get_user_from_custom_data(custom_data, db)
    plan = _get_plan_from_custom_data(custom_data, db)

    if not user or not plan:
        logger.warning(
            f"transaction.completed — user veya plan bulunamadı, custom_data: {custom_data}"
        )
        return

    transaction_id = data.get("id")

    # Sadece disposable için credit ekle (subscription'lar subscription event'lerinde işlenir)
    if plan.slug != "disposable":
        logger.info(
            f"transaction.completed — disposable değil ({plan.slug}), "
            f"subscription event'inde işlenecek. tx_id={transaction_id}"
        )
        return

    # Idempotency: aynı transaction için credit zaten eklendi mi?
    existing_credit = db.query(CreditLedger).filter(
        CreditLedger.user_id == user.id,
        CreditLedger.reference_id == transaction_id,
        CreditLedger.type == "topup",
    ).first()

    if existing_credit:
        logger.info(f"Disposable credit zaten eklenmiş: tx_id={transaction_id}")
        return

    # Disposable: 5 credit ekle (Plan.credits_monthly'den oku)
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
        last_entry.reference_id = transaction_id
        last_entry.description = f"Disposable test pack — {plan.credits_monthly} credit"
        db.commit()

    logger.info(
        f"Disposable credit eklendi: user_id={user.id}, "
        f"amount={plan.credits_monthly}, tx_id={transaction_id}"
    )


# --------------------------------------------
# Subscription handlers
# --------------------------------------------

def _handle_subscription_created(data: dict, db: Session):
    """
    Yeni subscription oluşturuldu.

    Bizim DB'mizde Subscription kaydı oluştur, plan kredisini yükle.
    """
    custom_data = data.get("custom_data") or {}
    user = _get_user_from_custom_data(custom_data, db)
    plan = _get_plan_from_custom_data(custom_data, db)

    if not user or not plan:
        logger.warning(
            f"subscription.created — user veya plan yok, custom_data: {custom_data}"
        )
        return

    paddle_sub_id = data.get("id")
    paddle_customer_id = data.get("customer_id")

    # Idempotency: bu paddle_subscription_id zaten var mı?
    existing = db.query(Subscription).filter(
        Subscription.paddle_subscription_id == paddle_sub_id
    ).first()

    if existing:
        logger.info(f"Subscription zaten var: paddle_sub_id={paddle_sub_id}")
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
    current_period = data.get("current_billing_period", {})
    period_start = _parse_paddle_datetime(current_period.get("starts_at"))
    period_end = _parse_paddle_datetime(current_period.get("ends_at"))

    if not period_start or not period_end:
        # Fallback: şu an + 30 gün
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)

    # User'ın paddle_customer_id'sini güncelle (yoksa)
    if not user.paddle_customer_id and paddle_customer_id:
        user.paddle_customer_id = paddle_customer_id

    # Yeni Subscription oluştur
    subscription = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        status="active",
        current_period_start=period_start,
        current_period_end=period_end,
        paddle_subscription_id=paddle_sub_id,
        paddle_customer_id=paddle_customer_id,
    )
    db.add(subscription)
    db.flush()

    # Plan kredisini yükle
    credit_service = CreditService(db)
    credit_service.grant_credits(
        user_id=user.id,
        amount=plan.credits_monthly,
        description=f"{plan.name} aktivasyonu — {plan.credits_monthly} credit",
        expires_at=period_end,
    )

    db.commit()

    logger.info(
        f"Subscription oluşturuldu: user_id={user.id}, plan={plan.slug}, "
        f"paddle_sub_id={paddle_sub_id}, credits={plan.credits_monthly}"
    )


def _handle_subscription_activated(data: dict, db: Session):
    """Subscription aktive oldu — status'u 'active' yap."""
    paddle_sub_id = data.get("id")
    sub = db.query(Subscription).filter(
        Subscription.paddle_subscription_id == paddle_sub_id
    ).first()

    if not sub:
        # subscription.created henüz gelmediyse, bu event'te oluşturmaya gerek yok —
        # Paddle her ikisini de gönderir
        logger.info(f"subscription.activated — sub bulunamadı (henüz created gelmemiş): {paddle_sub_id}")
        return

    sub.status = "active"
    db.commit()
    logger.info(f"Subscription aktif: paddle_sub_id={paddle_sub_id}")


def _handle_subscription_updated(data: dict, db: Session):
    """
    Subscription güncellendi (plan değişikliği, billing dönem yenilendi vb.).

    Önemli case: yenileme. Paddle her ay otomatik ödeme alır,
    bunu subscription.updated ile bildirir. Yeni dönem için credit ekleyeceğiz.
    """
    paddle_sub_id = data.get("id")
    sub = db.query(Subscription).filter(
        Subscription.paddle_subscription_id == paddle_sub_id
    ).first()

    if not sub:
        logger.warning(f"subscription.updated — sub bulunamadı: {paddle_sub_id}")
        return

    # Yeni periyot bilgisini güncelle
    current_period = data.get("current_billing_period", {})
    new_period_start = _parse_paddle_datetime(current_period.get("starts_at"))
    new_period_end = _parse_paddle_datetime(current_period.get("ends_at"))

    if new_period_start and new_period_end:
        # Periyot değiştiyse (yenileme)
        if new_period_start > sub.current_period_start:
            sub.current_period_start = new_period_start
            sub.current_period_end = new_period_end

            # Yeni dönem kredisi yükle
            plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
            if plan:
                # Önce eski dönemden kalan kredileri sıfırla
                credit_service = CreditService(db)
                credit_service.expire_credits(sub.user_id)
                credit_service.grant_credits(
                    user_id=sub.user_id,
                    amount=plan.credits_monthly,
                    description=f"{plan.name} dönem yenileme — {plan.credits_monthly} credit",
                    expires_at=new_period_end,
                )

                logger.info(
                    f"Subscription yenilendi: user_id={sub.user_id}, "
                    f"plan={plan.slug}, paddle_sub_id={paddle_sub_id}"
                )

    # Status güncelle
    paddle_status = data.get("status", "active")
    sub.status = paddle_status if paddle_status in ("active", "paused", "past_due") else sub.status
    db.commit()


def _handle_subscription_canceled(data: dict, db: Session):
    """Subscription iptal edildi."""
    paddle_sub_id = data.get("id")
    sub = db.query(Subscription).filter(
        Subscription.paddle_subscription_id == paddle_sub_id
    ).first()

    if not sub:
        logger.warning(f"subscription.canceled — sub bulunamadı: {paddle_sub_id}")
        return

    sub.status = "cancelled"
    canceled_at = _parse_paddle_datetime(data.get("canceled_at"))
    sub.cancel_at = canceled_at or datetime.utcnow()
    db.commit()

    logger.info(f"Subscription iptal: paddle_sub_id={paddle_sub_id}")


def _handle_subscription_past_due(data: dict, db: Session):
    """Subscription past_due — ödeme alınamadı."""
    paddle_sub_id = data.get("id")
    sub = db.query(Subscription).filter(
        Subscription.paddle_subscription_id == paddle_sub_id
    ).first()

    if not sub:
        return

    sub.status = "past_due"
    db.commit()
    logger.warning(f"Subscription past_due: paddle_sub_id={paddle_sub_id}")


# ============================================
# UTILITY
# ============================================

def _parse_paddle_datetime(value: Optional[str]) -> Optional[datetime]:
    """Paddle ISO 8601 datetime string → naive UTC datetime."""
    if not value:
        return None
    try:
        # Paddle: "2026-05-04T07:04:33.123Z"
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        # Naive UTC'ye çevir (modelde naive kullanılıyor)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except (ValueError, TypeError):
        logger.warning(f"Paddle datetime parse hatası: {value}")
        return None
