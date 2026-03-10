"""
Agent Mining - Veritabanı Modelleri
Persona, Campaign ve Decision tablolarını tanımlar.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean,
    DateTime, Text, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, DeclarativeBase
import enum


class Base(DeclarativeBase):
    pass


class SegmentType(str, enum.Enum):
    TR = "TR"          # TÜİK bazlı Türkiye segmenti
    GLOBAL = "GLOBAL"  # US/EU ağırlıklı global segment


class DecisionType(str, enum.Enum):
    BUY = "EVET"
    NO_BUY = "HAYIR"


class CampaignStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# PERSONA
# ---------------------------------------------------------------------------

class Persona(Base):
    """
    Sentetik tüketici persona kaydı.
    50K+ ön-üretim için tasarlandı.
    """
    __tablename__ = "am_personas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment = Column(SAEnum(SegmentType), nullable=False, index=True)

    # --- Kimlik ---
    name = Column(String(100), nullable=False)

    # --- Demografik ---
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False, default="Türkiye")
    income_level = Column(String(30), nullable=False)   # Düşük / Orta / Yüksek
    education = Column(String(50), nullable=False)
    occupation = Column(String(100), nullable=False)
    marital_status = Column(String(30), nullable=False)
    household_size = Column(Integer, nullable=True)

    # --- Big Five Psikografi (0.0 - 1.0) ---
    openness = Column(Float, nullable=False)
    conscientiousness = Column(Float, nullable=False)
    extraversion = Column(Float, nullable=False)
    agreeableness = Column(Float, nullable=False)
    neuroticism = Column(Float, nullable=False)

    # --- Değerler & İlgiler (JSON array) ---
    values = Column(JSON, nullable=False, default=list)         # ["aile", "kariyer", ...]
    interests = Column(JSON, nullable=False, default=list)      # ["teknoloji", "spor", ...]
    brands_liked = Column(JSON, nullable=False, default=list)   # ["Apple", "Nike", ...]
    price_sensitivity = Column(Float, nullable=False)           # 0-1

    # --- Dijital davranış ---
    social_media_usage = Column(String(20), nullable=True)  # az / orta / yoğun
    online_shopping_freq = Column(String(20), nullable=True)  # nadiren / aylık / haftalık

    # --- Meta ---
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    generation_model = Column(String(50), nullable=True)  # hangi LLM üretildi
    is_validated = Column(Boolean, default=False)  # referans kampanya çalıştı mı

    # Relationships
    decisions = relationship("AgentDecision", back_populates="persona", lazy="dynamic")

    def __repr__(self):
        return f"<Persona {self.name} | {self.age}y | {self.city} | {self.segment}>"

    def to_prompt_dict(self) -> dict:
        """Prompt template'e beslenecek dict döner."""
        sensitivity_label = (
            "yüksek" if self.price_sensitivity > 0.7
            else "orta" if self.price_sensitivity > 0.4
            else "düşük"
        )
        return {
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "city": self.city,
            "country": self.country,
            "income_level": self.income_level,
            "education": self.education,
            "occupation": self.occupation,
            "marital_status": self.marital_status,
            "openness": round(self.openness * 10, 1),
            "conscientiousness": round(self.conscientiousness * 10, 1),
            "extraversion": round(self.extraversion * 10, 1),
            "agreeableness": round(self.agreeableness * 10, 1),
            "neuroticism": round(self.neuroticism * 10, 1),
            "values": ", ".join(self.values),
            "interests": ", ".join(self.interests),
            "price_sensitivity_label": sensitivity_label,
            "social_media_usage": self.social_media_usage or "orta",
            "online_shopping_freq": self.online_shopping_freq or "aylık",
        }


# ---------------------------------------------------------------------------
# REFERENCE CAMPAIGN
# ---------------------------------------------------------------------------

class ReferenceCampaign(Base):
    """
    Kural motoru ve fine-tune için kullanılacak referans kampanyalar.
    Farklı kategorilerde ~20-50 kampanya ile veri toplarız.
    """
    __tablename__ = "am_reference_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)  # FMCG / Teknoloji / Tekstil ...
    
    # Kampanya içeriği (reklam metni, ürün açıklaması, fiyat)
    content = Column(Text, nullable=False)
    product_name = Column(String(200), nullable=True)
    price_tl = Column(Float, nullable=True)
    price_usd = Column(Float, nullable=True)
    
    # Hedef segment filtresi (null = hepsi)
    target_segment = Column(SAEnum(SegmentType), nullable=True)
    target_age_min = Column(Integer, nullable=True)
    target_age_max = Column(Integer, nullable=True)
    
    status = Column(SAEnum(CampaignStatus), default=CampaignStatus.PENDING, nullable=False)
    
    # Kaç persona'ya çalıştırıldı
    total_personas_run = Column(Integer, default=0)
    buy_count = Column(Integer, default=0)
    no_buy_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    decisions = relationship("AgentDecision", back_populates="campaign", lazy="dynamic")

    @property
    def buy_rate(self) -> float | None:
        if self.total_personas_run == 0:
            return None
        return self.buy_count / self.total_personas_run

    def __repr__(self):
        return f"<Campaign '{self.name}' | {self.category} | {self.status}>"


# ---------------------------------------------------------------------------
# AGENT DECISION (Ana veri toplama tablosu)
# ---------------------------------------------------------------------------

class AgentDecision(Base):
    """
    Her persona × kampanya çiftinden gelen karar.
    Fine-tune ve kural motoru için ham veri.
    
    Hedef: ~50K persona × ~20 kampanya = 1M karar noktası
    """
    __tablename__ = "am_agent_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("am_personas.id"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("am_reference_campaigns.id"), nullable=False, index=True)

    # LLM çıktısı
    decision = Column(SAEnum(DecisionType), nullable=False, index=True)
    confidence = Column(Integer, nullable=False)   # 1-10
    reasoning = Column(Text, nullable=True)        # kısa gerekçe

    # Kullanılan prompt (debugging ve fine-tune için)
    system_prompt_hash = Column(String(64), nullable=True)  # SHA256[:16]
    
    # Maliyet takibi
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    model_used = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    persona = relationship("Persona", back_populates="decisions")
    campaign = relationship("ReferenceCampaign", back_populates="decisions")

    def __repr__(self):
        return f"<Decision {self.decision} | conf={self.confidence} | persona={self.persona_id}>"
