"""
SimuTarget Admin Dashboard endpoints.

Tüm endpoint'ler get_current_admin dependency ile korunur —
User.role == 'admin' değilse 403 döner.

Endpoint'ler:
  GET  /api/v1/admin/stats           — overview metrics (cards + charts + funnel)
  GET  /api/v1/admin/users           — paginated user listesi
  GET  /api/v1/admin/subscriptions   — paginated subscription listesi
  GET  /api/v1/admin/campaigns       — paginated kampanya listesi
  GET  /api/v1/admin/recent-activity — son N olay (interleaved feed)

Yer: backend/src/api/routes/admin.py
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import (
    User, Plan, Subscription, Campaign, CreditLedger,
    LemonSqueezyWebhookEvent
)
from src.api.auth import get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# RESPONSE MODELS
# ============================================

class StatsCards(BaseModel):
    total_users: int
    users_today: int
    users_7d: int
    users_30d: int
    active_subscriptions: int
    cancelled_subscriptions: int
    past_due_subscriptions: int
    mrr_usd: float
    arr_usd: float
    total_campaigns: int
    campaigns_today: int
    campaigns_7d: int


class DailyPoint(BaseModel):
    date: str  # YYYY-MM-DD
    value: float


class PlanBreakdown(BaseModel):
    plan_name: str
    plan_slug: str
    active_count: int
    monthly_revenue_usd: float


class ConversionFunnel(BaseModel):
    signed_up: int
    ran_first_campaign: int
    has_paid_subscription: int
    signup_to_activation_pct: float
    activation_to_paid_pct: float
    overall_conversion_pct: float


class StatsResponse(BaseModel):
    cards: StatsCards
    daily_signups: List[DailyPoint]
    daily_revenue: List[DailyPoint]
    plan_breakdown: List[PlanBreakdown]
    conversion_funnel: ConversionFunnel


class UserListItem(BaseModel):
    id: int
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime
    has_active_subscription: bool
    current_plan: Optional[str] = None
    total_campaigns: int


class UserListResponse(BaseModel):
    items: List[UserListItem]
    total: int
    page: int
    page_size: int


class SubscriptionListItem(BaseModel):
    id: int
    user_id: int
    user_email: str
    plan_name: str
    plan_slug: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at: Optional[datetime] = None
    lemonsqueezy_subscription_id: Optional[str] = None
    created_at: datetime


class SubscriptionListResponse(BaseModel):
    items: List[SubscriptionListItem]
    total: int
    page: int
    page_size: int


class CampaignListItem(BaseModel):
    id: int
    user_id: int
    user_email: str
    name: str
    type: str
    region: str
    persona_count: int
    status: str
    credits_consumed: int
    created_at: datetime


class CampaignListResponse(BaseModel):
    items: List[CampaignListItem]
    total: int
    page: int
    page_size: int


class RecentActivityItem(BaseModel):
    type: str  # 'user_signup' | 'subscription_created' | 'subscription_cancelled' | 'campaign_run'
    timestamp: datetime
    title: str
    subtitle: Optional[str] = None
    user_email: Optional[str] = None


class RecentActivityResponse(BaseModel):
    items: List[RecentActivityItem]


# ============================================
# STATS ENDPOINT
# ============================================

@router.get("/stats", response_model=StatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """
    Dashboard overview metrikleri tek seferde döner.

    İçerik:
      - 12 metric card (total users, MRR, active subs, vs.)
      - 30 günlük günlük yeni üye serisi
      - 30 günlük günlük gelir serisi
      - Plan başına aktif abonelik dağılımı
      - Conversion funnel (signup → activation → paid)
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    days_7_ago = now - timedelta(days=7)
    days_30_ago = now - timedelta(days=30)

    # ===== CARDS =====
    total_users = db.query(func.count(User.id)).scalar() or 0
    users_today = db.query(func.count(User.id)).filter(
        User.created_at >= today_start
    ).scalar() or 0
    users_7d = db.query(func.count(User.id)).filter(
        User.created_at >= days_7_ago
    ).scalar() or 0
    users_30d = db.query(func.count(User.id)).filter(
        User.created_at >= days_30_ago
    ).scalar() or 0

    active_subs = db.query(func.count(Subscription.id)).filter(
        Subscription.status == "active",
        Subscription.current_period_end > now,
    ).scalar() or 0

    cancelled_subs = db.query(func.count(Subscription.id)).filter(
        Subscription.status == "cancelled"
    ).scalar() or 0

    past_due_subs = db.query(func.count(Subscription.id)).filter(
        Subscription.status == "past_due"
    ).scalar() or 0

    # MRR: aktif aboneliklerin plan_monthly toplamı
    mrr = db.query(func.coalesce(func.sum(Plan.price_monthly), 0)).join(
        Subscription, Subscription.plan_id == Plan.id
    ).filter(
        Subscription.status == "active",
        Subscription.current_period_end > now,
        Plan.slug != "disposable",  # disposable subscription değil
    ).scalar() or 0
    mrr_usd = float(mrr)
    arr_usd = mrr_usd * 12

    total_campaigns = db.query(func.count(Campaign.id)).scalar() or 0
    campaigns_today = db.query(func.count(Campaign.id)).filter(
        Campaign.created_at >= today_start
    ).scalar() or 0
    campaigns_7d = db.query(func.count(Campaign.id)).filter(
        Campaign.created_at >= days_7_ago
    ).scalar() or 0

    cards = StatsCards(
        total_users=total_users,
        users_today=users_today,
        users_7d=users_7d,
        users_30d=users_30d,
        active_subscriptions=active_subs,
        cancelled_subscriptions=cancelled_subs,
        past_due_subscriptions=past_due_subs,
        mrr_usd=round(mrr_usd, 2),
        arr_usd=round(arr_usd, 2),
        total_campaigns=total_campaigns,
        campaigns_today=campaigns_today,
        campaigns_7d=campaigns_7d,
    )

    # ===== DAILY SIGNUPS (last 30 days) =====
    signups_raw = db.execute(text("""
        SELECT DATE(created_at) AS d, COUNT(*) AS c
        FROM users
        WHERE created_at >= :start_date
        GROUP BY DATE(created_at)
        ORDER BY d ASC
    """), {"start_date": days_30_ago}).fetchall()

    signup_map = {row[0].isoformat(): row[1] for row in signups_raw}

    daily_signups = []
    for i in range(30, -1, -1):
        day = (now - timedelta(days=i)).date()
        daily_signups.append(DailyPoint(
            date=day.isoformat(),
            value=signup_map.get(day.isoformat(), 0),
        ))

    # ===== DAILY REVENUE (last 30 days) =====
    # LS webhook event'lerinden çıkarılır:
    #   - subscription_payment_success → initial + renewal ödemeler
    #   - order_created + plan_slug='disposable' → tek seferlik
    # Total cents olarak gelir, /100 ile USD'ye çevrilir.
    revenue_raw = db.execute(text("""
        SELECT
            DATE(received_at) AS d,
            COALESCE(SUM(
                CASE
                    WHEN event_name = 'subscription_payment_success'
                    THEN COALESCE(
                        NULLIF(payload->'data'->'attributes'->>'total', '')::numeric,
                        NULLIF(payload->'data'->'attributes'->>'total_usd', '')::numeric,
                        0
                    )
                    WHEN event_name = 'order_created'
                         AND payload->'meta'->'custom_data'->>'plan_slug' = 'disposable'
                    THEN COALESCE(
                        NULLIF(payload->'data'->'attributes'->>'total', '')::numeric,
                        NULLIF(payload->'data'->'attributes'->>'total_usd', '')::numeric,
                        0
                    )
                    ELSE 0
                END
            ), 0) / 100.0 AS revenue_usd
        FROM lemonsqueezy_webhook_events
        WHERE received_at >= :start_date
          AND processed_at IS NOT NULL
        GROUP BY DATE(received_at)
        ORDER BY d ASC
    """), {"start_date": days_30_ago}).fetchall()

    revenue_map = {row[0].isoformat(): float(row[1] or 0) for row in revenue_raw}

    daily_revenue = []
    for i in range(30, -1, -1):
        day = (now - timedelta(days=i)).date()
        daily_revenue.append(DailyPoint(
            date=day.isoformat(),
            value=round(revenue_map.get(day.isoformat(), 0.0), 2),
        ))

    # ===== PLAN BREAKDOWN =====
    plan_rows = db.query(
        Plan.id,
        Plan.name,
        Plan.slug,
        Plan.price_monthly,
        func.count(Subscription.id).label("active_count"),
    ).outerjoin(
        Subscription,
        (Subscription.plan_id == Plan.id) &
        (Subscription.status == "active") &
        (Subscription.current_period_end > now),
    ).filter(
        Plan.is_active == True,
    ).group_by(
        Plan.id, Plan.name, Plan.slug, Plan.price_monthly,
    ).order_by(Plan.price_monthly.asc()).all()

    plan_breakdown = []
    for row in plan_rows:
        monthly_rev = float(row.price_monthly or 0) * row.active_count
        plan_breakdown.append(PlanBreakdown(
            plan_name=row.name,
            plan_slug=row.slug,
            active_count=row.active_count,
            monthly_revenue_usd=round(monthly_rev, 2),
        ))

    # ===== CONVERSION FUNNEL =====
    ran_first_campaign = db.query(
        func.count(func.distinct(Campaign.user_id))
    ).scalar() or 0

    has_paid_sub = db.query(
        func.count(func.distinct(Subscription.user_id))
    ).filter(
        Subscription.lemonsqueezy_subscription_id.isnot(None),
    ).scalar() or 0

    signup_to_activation = (
        round((ran_first_campaign / total_users) * 100, 1)
        if total_users > 0 else 0.0
    )
    activation_to_paid = (
        round((has_paid_sub / ran_first_campaign) * 100, 1)
        if ran_first_campaign > 0 else 0.0
    )
    overall_conv = (
        round((has_paid_sub / total_users) * 100, 1)
        if total_users > 0 else 0.0
    )

    conversion_funnel = ConversionFunnel(
        signed_up=total_users,
        ran_first_campaign=ran_first_campaign,
        has_paid_subscription=has_paid_sub,
        signup_to_activation_pct=signup_to_activation,
        activation_to_paid_pct=activation_to_paid,
        overall_conversion_pct=overall_conv,
    )

    return StatsResponse(
        cards=cards,
        daily_signups=daily_signups,
        daily_revenue=daily_revenue,
        plan_breakdown=plan_breakdown,
        conversion_funnel=conversion_funnel,
    )


# ============================================
# USER LIST ENDPOINT
# ============================================

@router.get("/users", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None, description="Email veya isimde arama"),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Tüm kullanıcıları listele (paginated, search destekli)."""
    now = datetime.utcnow()
    query = db.query(User)

    if search:
        like = f"%{search.lower()}%"
        query = query.filter(
            func.lower(User.email).like(like) | func.lower(User.name).like(like)
        )

    total = query.count()
    users = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for user in users:
        # Aktif sub kontrolü
        active_sub = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == "active",
            Subscription.current_period_end > now,
        ).first()

        current_plan = None
        if active_sub:
            plan = db.query(Plan).filter(Plan.id == active_sub.plan_id).first()
            current_plan = plan.name if plan else None

        campaign_count = db.query(func.count(Campaign.id)).filter(
            Campaign.user_id == user.id
        ).scalar() or 0

        items.append(UserListItem(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            has_active_subscription=active_sub is not None,
            current_plan=current_plan,
            total_campaigns=campaign_count,
        ))

    return UserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ============================================
# SUBSCRIPTION LIST ENDPOINT
# ============================================

@router.get("/subscriptions", response_model=SubscriptionListResponse)
def list_subscriptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None, description="active / cancelled / past_due / paused"),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Tüm aboneliklerin listesi (paginated, status filter destekli)."""
    query = db.query(
        Subscription, User, Plan
    ).join(
        User, User.id == Subscription.user_id
    ).join(
        Plan, Plan.id == Subscription.plan_id
    )

    if status:
        query = query.filter(Subscription.status == status)

    total = query.count()
    rows = (
        query.order_by(Subscription.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        SubscriptionListItem(
            id=sub.id,
            user_id=user.id,
            user_email=user.email,
            plan_name=plan.name,
            plan_slug=plan.slug,
            status=sub.status,
            current_period_start=sub.current_period_start,
            current_period_end=sub.current_period_end,
            cancel_at=sub.cancel_at,
            lemonsqueezy_subscription_id=sub.lemonsqueezy_subscription_id,
            created_at=sub.created_at,
        )
        for (sub, user, plan) in rows
    ]

    return SubscriptionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ============================================
# CAMPAIGN LIST ENDPOINT
# ============================================

@router.get("/campaigns", response_model=CampaignListResponse)
def list_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Tüm kampanyaları listele."""
    query = db.query(Campaign, User).join(
        User, User.id == Campaign.user_id
    )

    if status:
        query = query.filter(Campaign.status == status)

    total = query.count()
    rows = (
        query.order_by(Campaign.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        CampaignListItem(
            id=camp.id,
            user_id=user.id,
            user_email=user.email,
            name=camp.name,
            type=camp.type,
            region=camp.region,
            persona_count=camp.persona_count,
            status=camp.status,
            credits_consumed=camp.credits_consumed or 0,
            created_at=camp.created_at,
        )
        for (camp, user) in rows
    ]

    return CampaignListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ============================================
# RECENT ACTIVITY ENDPOINT
# ============================================

@router.get("/recent-activity", response_model=RecentActivityResponse)
def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """
    Son N olayı interleaved feed olarak döner.
    Yeni üye + yeni abonelik + iptal + kampanya — hepsi karışık.
    """
    activities: List[RecentActivityItem] = []

    # Son üyeler
    recent_users = db.query(User).order_by(
        User.created_at.desc()
    ).limit(limit).all()
    for u in recent_users:
        activities.append(RecentActivityItem(
            type="user_signup",
            timestamp=u.created_at,
            title="Yeni üye",
            subtitle=u.name,
            user_email=u.email,
        ))

    # Son abonelikler
    recent_subs = db.query(
        Subscription, User, Plan
    ).join(
        User, User.id == Subscription.user_id
    ).join(
        Plan, Plan.id == Subscription.plan_id
    ).order_by(Subscription.created_at.desc()).limit(limit).all()
    for sub, user, plan in recent_subs:
        if sub.status == "cancelled":
            activities.append(RecentActivityItem(
                type="subscription_cancelled",
                timestamp=sub.cancel_at or sub.created_at,
                title=f"İptal: {plan.name}",
                subtitle=f"${float(plan.price_monthly):.2f}/ay",
                user_email=user.email,
            ))
        else:
            activities.append(RecentActivityItem(
                type="subscription_created",
                timestamp=sub.created_at,
                title=f"Yeni abonelik: {plan.name}",
                subtitle=f"${float(plan.price_monthly):.2f}/ay",
                user_email=user.email,
            ))

    # Son kampanyalar (sadece completed)
    recent_camps = db.query(
        Campaign, User
    ).join(
        User, User.id == Campaign.user_id
    ).filter(
        Campaign.status == "completed"
    ).order_by(Campaign.created_at.desc()).limit(limit).all()
    for camp, user in recent_camps:
        activities.append(RecentActivityItem(
            type="campaign_run",
            timestamp=camp.created_at,
            title=f"Kampanya: {camp.name}",
            subtitle=f"{camp.persona_count} persona, {camp.region}",
            user_email=user.email,
        ))

    # Hepsini birleştir, timestamp'e göre sırala, limit kadar al
    activities.sort(key=lambda x: x.timestamp, reverse=True)
    activities = activities[:limit]

    return RecentActivityResponse(items=activities)
