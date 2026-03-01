"""FastAPI application for SimuTarget.ai."""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .routes import personas, campaigns, health, subscriptions
from src.database.connection import get_db
from src.api.auth import (
    UserRegister, UserLogin, TokenResponse, UserProfile,
    register_user, login_user, get_user_profile, get_current_user
)
from src.database.models import User
from src.database.credit_service import CreditService, FeatureGateService

# Create FastAPI app
app = FastAPI(
    title="SimuTarget.ai API",
    description="AI-Powered Synthetic Market Research Platform",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(personas.router, prefix="/api/v1/personas", tags=["Personas"])
app.include_router(campaigns.router, prefix="/api/v1/campaigns", tags=["Campaigns"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["Subscriptions"])


@app.get("/")
async def root():
    return {
        "name": "SimuTarget.ai API",
        "version": "0.2.0",
        "status": "running",
        "docs": "/docs",
    }


# ---- Auth Endpoints ----

@app.post("/api/v1/auth/register", response_model=TokenResponse, tags=["Auth"])
async def register(data: UserRegister, db: Session = Depends(get_db)):
    """Yeni kullanici kaydi"""
    return register_user(data, db)


@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["Auth"])
async def login(data: UserLogin, db: Session = Depends(get_db)):
    """Kullanici girisi"""
    return login_user(data, db)


@app.get("/api/v1/auth/profile", response_model=UserProfile, tags=["Auth"])
async def profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kullanici profili ve kredi bilgisi"""
    return get_user_profile(current_user, db)


# ---- Credit Endpoints ----

@app.get("/api/v1/credits/balance", tags=["Credits"])
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kullanicinin kredi bakiyesi"""
    credit_service = CreditService(db)
    summary = credit_service.get_usage_summary(current_user.id)
    return summary


@app.get("/api/v1/credits/check/{amount}", tags=["Credits"])
async def check_credits(
    amount: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Yeterli kredi var mi kontrol et"""
    credit_service = CreditService(db)
    balance = credit_service.get_balance(current_user.id)
    return {
        "sufficient": balance >= amount,
        "balance": balance,
        "required": amount,
        "shortfall": max(0, amount - balance)
    }


# ---- Feature Gate Endpoints ----

@app.get("/api/v1/features/filter/{filter_name}", tags=["Features"])
async def check_filter(
    filter_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Filtre erisim kontrolu"""
    gate_service = FeatureGateService(db)
    return gate_service.check_filter_access(current_user.id, filter_name)


@app.get("/api/v1/features/test/{test_type}", tags=["Features"])
async def check_test_type(
    test_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test turu erisim kontrolu"""
    gate_service = FeatureGateService(db)
    return gate_service.check_test_type_access(current_user.id, test_type)


# ---- Plans Endpoint ----

@app.get("/api/v1/plans", tags=["Plans"])
async def list_plans(db: Session = Depends(get_db)):
    """Tum aktif planlari listele"""
    from src.database.models import Plan
    plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.price_monthly).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "price_monthly": float(p.price_monthly),
            "credits_monthly": p.credits_monthly,
            "max_team_size": p.max_team_size,
            "features": p.features
        }
        for p in plans
    ]