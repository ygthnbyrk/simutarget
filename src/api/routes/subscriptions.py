"""
SimuTarget Abonelik Yönetimi API

DEPRECATION NOT (Oturum #8.2):
  Bu modülün /subscribe, /change ve /cancel endpoint'leri ÖDEME ALMADAN
  DB'de direkt subscription oluşturuyordu/değiştiriyordu (mock/legacy kod —
  Lemon Squeezy entegrasyonundan önce yazılmış).

  Live Mode'a geçişte güvenlik için 410 Gone dönecek şekilde devre dışı
  bırakıldılar. Yeni akış:

    Yeni abonelik:   POST /api/v1/lemonsqueezy/checkout
    Plan değiştir:   POST /api/v1/lemonsqueezy/checkout (yeni plan ile)
    Mevcut yönetim:  POST /api/v1/lemonsqueezy/portal (cancel/upgrade dahil)

Hala aktif olan endpoint'ler:
  GET  /api/v1/subscriptions/plans   → planları listele (auth gerekmez)
  GET  /api/v1/subscriptions/current → mevcut abonelik bilgisi (auth gerekli)
"""

from fastapi import APIRouter, HTTPException, Depends, status
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
    """Plan seçimi isteği. (DEPRECATED — artık kullanılmıyor)"""
    plan_slug: str = Field(..., description="Plan slug: disposable, starter, pro, business, enterprise")


class ChangePlanRequest(BaseModel):
    """Plan değiştirme isteği. (DEPRECATED — artık kullanılmıyor)"""
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
# AKTİF ENDPOINTS
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


# ============================================
# DEVRE DIŞI ENDPOINTS — 410 GONE
# (Live Mode güvenlik kapısı — Oturum #8.2)
# ============================================

_DEPRECATED_MSG_SUBSCRIBE = (
    "Bu endpoint devre dışı bırakıldı. Yeni abonelik için "
    "POST /api/v1/lemonsqueezy/checkout kullanılmalıdır. "
    "(Eski mock endpoint ödeme almadan abonelik oluşturuyordu — Live Mode'a "
    "geçişte güvenlik nedeniyle kapatıldı.)"
)

_DEPRECATED_MSG_CHANGE = (
    "Bu endpoint devre dışı bırakıldı. Plan değişikliği için: "
    "1) POST /api/v1/lemonsqueezy/portal ile mevcut aboneliği iptal et, "
    "2) POST /api/v1/lemonsqueezy/checkout ile yeni plana abone ol."
)

_DEPRECATED_MSG_CANCEL = (
    "Bu endpoint devre dışı bırakıldı. Abonelik iptali için "
    "POST /api/v1/lemonsqueezy/portal kullanılmalıdır — Lemon Squeezy "
    "customer portal'ından iptal edebilirsiniz. (DB-only cancel artık "
    "kullanılmıyor, çünkü gerçek ödeme provider'da kesinti devam ederdi.)"
)


@router.post("/subscribe", deprecated=True)
async def subscribe_to_plan_deprecated(
    request: SubscribeRequest,
    user: User = Depends(get_current_user),
):
    """DEPRECATED — bkz. POST /api/v1/lemonsqueezy/checkout"""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=_DEPRECATED_MSG_SUBSCRIBE,
    )


@router.post("/change", deprecated=True)
async def change_plan_deprecated(
    request: ChangePlanRequest,
    user: User = Depends(get_current_user),
):
    """DEPRECATED — bkz. POST /api/v1/lemonsqueezy/checkout"""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=_DEPRECATED_MSG_CHANGE,
    )


@router.post("/cancel", deprecated=True)
async def cancel_subscription_deprecated(
    user: User = Depends(get_current_user),
):
    """DEPRECATED — bkz. POST /api/v1/lemonsqueezy/portal"""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=_DEPRECATED_MSG_CANCEL,
    )
