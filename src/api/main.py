"""FastAPI application for SimuTarget.ai."""
import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .routes import (
    personas, campaigns, health, subscriptions,
    agent_mining, paddle, lemonsqueezy, admin,
)
from src.database.connection import get_db
from src.api.auth import (
    UserRegister, UserLogin, GoogleLoginRequest, TokenResponse, UserProfile,
    ForgotPasswordRequest, ResetPasswordRequest, MessageResponse,
    register_user, login_user, login_or_register_google,
    forgot_password, reset_password,
    get_user_profile, get_current_user,
)
from src.database.models import User
from src.database.credit_service import CreditService, FeatureGateService

# ---- Ortam ayrimi ----
# Coolify'da ENVIRONMENT=production tanimli. Tanimli degilse guvenli tarafta
# kalmak icin production varsayiyoruz (docs kapali olur).
ENV = os.getenv("ENVIRONMENT", "production").lower()
IS_PROD = ENV == "production"

# Create FastAPI app
# Production'da API dokumantasyonu (Swagger/ReDoc/OpenAPI) kapatilir —
# endpoint semasini disariya sizdirmamak icin. Dev'de acik kalir.
app = FastAPI(
    title="SimuTarget.ai API",
    description="AI-Powered Synthetic Market Research Platform",
    version="0.2.0",
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/redoc",
    openapi_url=None if IS_PROD else "/openapi.json",
)

# CORS middleware
# allow_origins="*" yerine sadece kendi origin'lerimize izin veriyoruz.
# allow_credentials=False kaldi (token Authorization header'da tasiniyor,
# cookie kullanilmiyor).
ALLOWED_ORIGINS = [
    "https://www.simutarget.ai",
    "https://simutarget.ai",
]
# Dev ortaminda local frontend'e de izin ver (uretimde eklenmez).
if not IS_PROD:
    ALLOWED_ORIGINS += [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(personas.router, prefix="/api/v1/personas", tags=["Personas"])
app.include_router(campaigns.router, prefix="/api/v1/campaigns", tags=["Campaigns"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["Subscriptions"])
app.include_router(agent_mining.router, prefix="/api/v1/agent-mining", tags=["Agent Mining"])
app.include_router(paddle.router, prefix="/api/v1/paddle", tags=["Paddle"])
app.include_router(lemonsqueezy.router, prefix="/api/v1/lemonsqueezy", tags=["Lemon Squeezy"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])


@app.get("/")
async def root():
    return {
        "name": "SimuTarget.ai API",
        "version": "0.2.0",
        "status": "running",
        "docs": "/docs" if not IS_PROD else "disabled",
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


@app.post("/api/v1/auth/google", response_model=TokenResponse, tags=["Auth"])
async def google_login(data: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Google OAuth ile giris veya kayit.

    Frontend Google Identity Services popup'undan ID token alir,
    bu endpoint'e gonderir. Backend verify edip JWT doner.

    Email mevcutsa: Google hesabini otomatik baglar (auto-link).
    Email yoksa: Yeni kullanici olusturur, Telegram bildirimi gonderir.
    """
    return login_or_register_google(data, db)


@app.post("/api/v1/auth/forgot-password", response_model=MessageResponse, tags=["Auth"])
async def forgot_password_endpoint(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Sifre sifirlama talebi.

    Guvenlik: email var/yok bilgisini sizdirmaz — her durumda ayni generic 200 doner.
    Email kayitliysa 1 saat gecerli, tek kullanimlik bir sifirlama baglantisi gonderir.
    """
    return forgot_password(data, db)


@app.post("/api/v1/auth/reset-password", response_model=MessageResponse, tags=["Auth"])
async def reset_password_endpoint(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Sifre sifirlama tamamlama.

    Email'deki token + yeni sifre alir. Token gecerliyse sifreyi gunceller.
    """
    return reset_password(data, db)


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
            "features": p.features,
            "paddle_price_id": p.paddle_price_id,
            "lemonsqueezy_variant_id": p.lemonsqueezy_variant_id,
        }
        for p in plans
    ]
