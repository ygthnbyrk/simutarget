"""SimuTarget veritabanı modelleri"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    ForeignKey, Text, Numeric, JSON
)
from sqlalchemy.orm import relationship
from src.database.connection import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    track = Column(String(20), nullable=False)  # individual / agency
    price_monthly = Column(Numeric(10, 2), nullable=False)
    credits_monthly = Column(Integer, nullable=False)
    max_team_size = Column(Integer, default=1)
    features = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Paddle entegrasyonu (oturum #7.8) — DEPRECATED
    paddle_price_id = Column(String(100), unique=True, nullable=True, index=True)

    # Lemon Squeezy entegrasyonu (oturum #7.9) — ACTIVE
    lemonsqueezy_variant_id = Column(String(100), unique=True, nullable=True, index=True)

    # Yıllık plan (oturum #8.4)
    price_yearly = Column(Numeric(10, 2), nullable=True)
    lemonsqueezy_yearly_variant_id = Column(String(100), unique=True, nullable=True, index=True)

    # İlişkiler
    subscriptions = relationship("Subscription", back_populates="plan")

    def has_feature(self, category: str, feature: str) -> bool:
        """Planın belirli bir özelliği var mı kontrol et"""
        return self.features.get(category, {}).get(feature, False)


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    max_members = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    members = relationship("User", back_populates="team")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    # password_hash NULLABLE — Google ile kayıt olan kullanıcıların şifresi yoktur
    password_hash = Column(String(255), nullable=True)
    role = Column(String(20), default="user")  # user / admin
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Google OAuth entegrasyonu (oturum #8.1)
    google_id = Column(String(100), unique=True, nullable=True, index=True)
    auth_provider = Column(String(20), nullable=False, default="email")  # "email" / "google"

    # Paddle entegrasyonu (oturum #7.8) — DEPRECATED
    # Paddle'da customer kaydının ID'si — ilk transaction'da oluşturulup buraya yazılır
    paddle_customer_id = Column(String(100), nullable=True, index=True)

    # Lemon Squeezy entegrasyonu (oturum #7.9) — ACTIVE
    # LS'de customer kaydının ID'si — ilk checkout'ta oluşturulup buraya yazılır
    lemonsqueezy_customer_id = Column(String(100), nullable=True, index=True)

    # İlişkiler
    team = relationship("Team", back_populates="members")
    subscriptions = relationship("Subscription", back_populates="user")
    credit_entries = relationship("CreditLedger", back_populates="user")
    campaigns = relationship("Campaign", back_populates="user")
    usage_logs = relationship("UsageLog", back_populates="user")
    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    status = Column(String(20), nullable=False)  # active / cancelled / past_due / paused
    stripe_subscription_id = Column(String(255), nullable=True)  # legacy, kullanılmıyor
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    cancel_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Paddle entegrasyonu (oturum #7.8) — DEPRECATED
    paddle_subscription_id = Column(String(100), unique=True, nullable=True, index=True)
    paddle_customer_id = Column(String(100), nullable=True, index=True)
    paddle_transaction_id = Column(String(100), nullable=True, index=True)  # ilk transaction

    # Lemon Squeezy entegrasyonu (oturum #7.9) — ACTIVE
    lemonsqueezy_subscription_id = Column(String(100), unique=True, nullable=True, index=True)
    lemonsqueezy_customer_id = Column(String(100), nullable=True, index=True)
    lemonsqueezy_order_id = Column(String(100), nullable=True, index=True)  # ilk order

    # İlişkiler
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")

    @property
    def is_active(self) -> bool:
        return self.status == "active" and self.current_period_end > datetime.utcnow()


class CreditLedger(Base):
    __tablename__ = "credit_ledger"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # + veya -
    type = Column(String(20), nullable=False)  # grant / usage / topup / expire / reserve / release
    balance_after = Column(Integer, nullable=False)
    reference_id = Column(String(255), nullable=True)
    description = Column(String(500), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    user = relationship("User", back_populates="credit_entries")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False)  # single / ab / abc
    content = Column(JSON, nullable=False)
    persona_count = Column(Integer, nullable=False)
    region = Column(String(10), nullable=False)  # TR / US / EU / MENA
    filters = Column(JSON, nullable=True)
    status = Column(String(20), default="pending")  # pending / running / completed / failed
    results = Column(JSON, nullable=True)
    credits_consumed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    user = relationship("User", back_populates="campaigns")
    persona_responses = relationship("CampaignPersonaResponse", back_populates="campaign")


class CampaignPersonaResponse(Base):
    __tablename__ = "campaign_persona_responses"

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    persona_data = Column(JSON, nullable=False)
    decision = Column(String(10), nullable=False)  # EVET / HAYIR
    confidence = Column(Integer, nullable=False)  # 1-10
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    campaign = relationship("Campaign", back_populates="persona_responses")


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    persona_count = Column(Integer, nullable=False)
    credits_used = Column(Integer, nullable=False)
    region = Column(String(10), nullable=True)
    filters_used = Column(JSON, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    user = relationship("User", back_populates="usage_logs")


# ============================================
# PADDLE ENTEGRASYONU — DEPRECATED (oturum #7.8)
# ============================================

class PaddleWebhookEvent(Base):
    """
    Paddle'dan gelen webhook event'lerinin kaydı.
    Idempotency için kritik: aynı event_id 2 kez gelirse 2. çağrıda
    işlem yapılmaz (UNIQUE constraint yakalar).

    DEPRECATED: LS canlıya geçtikten sonra silinecek.
    """
    __tablename__ = "paddle_webhook_events"

    id = Column(Integer, primary_key=True)
    event_id = Column(String(100), unique=True, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    processing_error = Column(Text, nullable=True)
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ============================================
# LEMON SQUEEZY ENTEGRASYONU — ACTIVE (oturum #7.9)
# ============================================

class LemonSqueezyWebhookEvent(Base):
    """
    Lemon Squeezy'den gelen webhook event'lerinin kaydı.
    Idempotency için kritik.

    NOT: LS Paddle gibi unique event_id göndermez. Backend raw_body'nin
    SHA256 hash'ini event_id olarak kullanır. Aynı body 2 kez gelirse
    aynı hash → UNIQUE constraint yakalar → idempotency.
    """
    __tablename__ = "lemonsqueezy_webhook_events"

    id = Column(Integer, primary_key=True)
    event_id = Column(String(100), unique=True, nullable=False, index=True)  # SHA256 hex
    event_name = Column(String(100), nullable=False, index=True)  # subscription_created vs.
    payload = Column(JSON, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    processing_error = Column(Text, nullable=True)
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ============================================
# ŞİFRE SIFIRLAMA — ACTIVE (oturum #8.3)
# ============================================

class PasswordResetToken(Base):
    """
    Şifre sıfırlama token'ları.

    Güvenlik:
      - Ham token (secrets.token_urlsafe) yalnızca kullanıcıya email ile gider.
      - DB'ye yalnızca SHA256 hash yazılır → DB sızsa bile token kullanılamaz.
        (LS webhook idempotency'sindeki SHA256 mantığının aynısı.)
      - 1 saat geçerli (expires_at), tek kullanımlık (used).
      - Yeni token üretilince kullanıcının eski kullanılmamış token'ları
        geçersiz kılınır (used=True).
    """
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA256 hex
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    user = relationship("User", back_populates="password_reset_tokens")

    @property
    def is_valid(self) -> bool:
        """Token kullanılmamış ve süresi dolmamış mı?"""
        return (not self.used) and self.expires_at > datetime.utcnow()
