"""
SimuTarget Abonelik Yönetimi API

Akış:
  POST /subscriptions/subscribe → Plan seç → Subscription oluştur → Kredi yükle
  GET  /subscriptions/current → Mevcut abonelik bilgisi
  POST /subscriptions/change → Plan değiştir (yükselt/düşür)
  POST /subscriptions/cancel → Abonelik iptal et
  
Not: Stripe entegrasyonu sonraki adımda eklenecek.
Şimdilik "free trial" mantığıyla çalışır — plan seçince direkt aktif olur.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.models import User, Plan, Subscription, CreditLedger
from src.database.credit_service import CreditService
from src.api.auth import get_current_user

router = APIRouter()


# ============================================
# REQUEST / RESPONSE MODELLERİ
# ============================================

class SubscribeRequest(BaseModel):
    """Plan seçimi isteği."""
    plan_slug: str = Field(..., description="Plan slug: disposable, starter, pro, business, enterprise")


class ChangePlanRequest(BaseModel):
    """Plan değiştirme isteği."""
    new_plan_slug: str = Field(..., description="Yeni plan slug")


class SubscriptionResponse(BaseModel):
    """Abonelik bilgisi."""
    id: int
    plan_name: str
    plan_slug: str
    price_monthly: float
    credits_monthly: int
    credits_remaining: int
    status: str
    current_period_start: str
    current_period_end: str
    features: dict


class PlanResponse(BaseModel):
    """Plan bilgisi."""
    id: int
    name: str
    slug: str
    price_monthly: float
    credits_monthly: int
    max_team_size: int
    features: dict


# ============================================
# YARDIMCI FONKSİYONLAR
# ============================================

def _get_plan_or_404(plan_slug: str, db: Session) -> Plan:
    """Plan slug'ından planı getir."""
    plan = db.query(Plan).filter(Plan.slug == plan_slug, Plan.is_active == True).first()
    if not plan:
        raise HTTPException(404, f"Plan bulunamadı: {plan_slug}")
    return plan


def _get_active_subscription(user_id: int, db: Session) -> Optional[Subscription]:
    """Kullanıcının aktif aboneliğini getir."""
    return (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user_id,
            Subscription.status == "active",
        )
        .first()
    )


def _create_subscription(user: User, plan: Plan, db: Session) -> Subscription:
    """Yeni abonelik oluştur ve kredi yükle."""
    now = datetime.now(timezone.utc)
    period_end = now + timedelta(days=30)

    subscription = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        status="active",
        current_period_start=now,
        current_period_end=period_end,
    )
    db.add(subscription)
    db.flush()  # ID almak için

    # Kredi yükle
    credit_service = CreditService(db)
    credit_service.grant_credits(
        user_id=user.id,
        amount=plan.credits_monthly,
        description=f"{plan.name} planı aktivasyonu — {plan.credits_monthly} kredi",
        expires_at=period_end,
    )

    return subscription


def _build_subscription_response(
    subscription: Subscription, plan: Plan, credits_remaining: int
) -> SubscriptionResponse:
    """Subscription → API Response."""
    return SubscriptionResponse(
        id=subscription.id,
        plan_name=plan.name,
        plan_slug=plan.slug,
        price_monthly=float(plan.price_monthly),
        credits_monthly=plan.credits_monthly,
        credits_remaining=credits_remaining,
        status=subscription.status,
        current_period_start=subscription.current_period_start.isoformat(),
        current_period_end=subscription.current_period_end.isoformat(),
        features=plan.features,
    )


# ============================================
# ENDPOINTS
# ============================================

@router.get("/plans", response_model=list[PlanResponse])
async def list_available_plans(db: Session = Depends(get_db)):
    """Tüm aktif planları listele (auth gerektirmez)."""
    plans = (
        db.query(Plan)
        .filter(Plan.is_active == True)
        .order_by(Plan.price_monthly)
        .all()
    )
    return [
        PlanResponse(
            id=p.id,
            name=p.name,
            slug=p.slug,
            price_monthly=float(p.price_monthly),
            credits_monthly=p.credits_monthly,
            max_team_size=p.max_team_size,
            features=p.features,
        )
        for p in plans
    ]


@router.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe_to_plan(
    request: SubscribeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Plana abone ol.
    - Aktif abonelik varsa hata verir (change endpoint kullanılmalı)
    - Subscription oluşturur
    - Plan kredilerini otomatik yükler
    """
    # Plan kontrolü
    plan = _get_plan_or_404(request.plan_slug, db)

    # Mevcut aktif abonelik kontrolü
    existing = _get_active_subscription(user.id, db)
    if existing:
        raise HTTPException(
            400,
            f"Zaten aktif bir aboneliğiniz var ({existing.plan.name}). "
            f"Plan değiştirmek için /subscriptions/change endpoint'ini kullanın."
        )

    # Abonelik oluştur + kredi yükle
    subscription = _create_subscription(user, plan, db)
    db.commit()
    db.refresh(subscription)

    # Güncel bakiye
    credit_service = CreditService(db)
    balance = credit_service.get_balance(user.id)

    return _build_subscription_response(subscription, plan, balance)


@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mevcut aktif abonelik bilgisini getir."""
    subscription = _get_active_subscription(user.id, db)

    if not subscription:
        raise HTTPException(404, "Aktif abonelik bulunamadı.")

    plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
    credit_service = CreditService(db)
    balance = credit_service.get_balance(user.id)

    return _build_subscription_response(subscription, plan, balance)


@router.post("/change", response_model=SubscriptionResponse)
async def change_plan(
    request: ChangePlanRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Plan değiştir (yükselt veya düşür).
    - Mevcut aboneliği iptal eder
    - Kalan kredileri sıfırlar
    - Yeni plan ile yeni abonelik oluşturur
    - Yeni plan kredilerini yükler
    
    Not: Gerçek üründe Stripe proration yapılacak. Şimdilik basit geçiş.
    """
    # Yeni plan kontrolü
    new_plan = _get_plan_or_404(request.new_plan_slug, db)

    # Mevcut abonelik kontrolü
    current_sub = _get_active_subscription(user.id, db)
    if not current_sub:
        raise HTTPException(400, "Aktif abonelik yok. Önce /subscriptions/subscribe kullanın.")

    # Aynı plana geçiş engelle
    if current_sub.plan_id == new_plan.id:
        raise HTTPException(400, "Zaten bu planda abonesiniz.")

    # 1. Mevcut aboneliği iptal et
    current_sub.status = "cancelled"
    current_sub.cancel_at = datetime.now(timezone.utc)

    # 2. Kalan kredileri sıfırla
    credit_service = CreditService(db)
    credit_service.expire_credits(user.id)

    # 3. Yeni abonelik + kredi yükle
    new_subscription = _create_subscription(user, new_plan, db)
    db.commit()
    db.refresh(new_subscription)

    balance = credit_service.get_balance(user.id)

    return _build_subscription_response(new_subscription, new_plan, balance)


@router.post("/cancel")
async def cancel_subscription(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Aboneliği iptal et.
    - Dönem sonuna kadar aktif kalır
    - Krediler dönem sonunda sıfırlanır
    
    Not: Gerçek üründe Stripe cancellation yapılacak.
    """
    subscription = _get_active_subscription(user.id, db)
    if not subscription:
        raise HTTPException(404, "Aktif abonelik bulunamadı.")

    plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()

    # İptal işaretle — dönem sonuna kadar aktif kalacak
    subscription.status = "cancelled"
    subscription.cancel_at = subscription.current_period_end
    db.commit()

    return {
        "status": "cancelled",
        "message": f"{plan.name} aboneliğiniz iptal edildi. "
                   f"{subscription.current_period_end.strftime('%d.%m.%Y')} tarihine kadar aktif kalacak.",
        "active_until": subscription.current_period_end.isoformat(),
    }