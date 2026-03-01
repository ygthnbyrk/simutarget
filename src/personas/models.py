"""Persona data models - Global Version with 34 fields."""

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class Region(str, Enum):
    TURKEY = "TR"
    USA = "US"
    EUROPE = "EU"
    MENA = "MENA"


class Gender(str, Enum):
    MALE = "Erkek"
    FEMALE = "Kad\u0131n"


class MaritalStatus(str, Enum):
    SINGLE = "Bekar"
    MARRIED = "Evli"
    DIVORCED = "Bo\u015fanm\u0131\u015f"


class Education(str, Enum):
    PRIMARY = "\u0130lkokul"
    MIDDLE_SCHOOL = "Ortaokul"
    HIGH_SCHOOL = "Lise"
    ASSOCIATE = "\u00d6n Lisans"
    UNIVERSITY = "\u00dcniversite"
    MASTERS = "Y\u00fcksek Lisans"
    PHD = "Doktora"


class IncomeLevel(str, Enum):
    LOW = "D\u00fc\u015f\u00fck"
    LOWER_MIDDLE = "Orta-D\u00fc\u015f\u00fck"
    MIDDLE = "Orta"
    UPPER_MIDDLE = "Orta-Y\u00fcksek"
    HIGH = "Y\u00fcksek"


class LifeOutlook(str, Enum):
    OPTIMIST = "\u0130yimser"
    PESSIMIST = "K\u00f6t\u00fcmser"
    REALIST = "Ger\u00e7ek\u00e7i"
    ADVENTUROUS = "Macerac\u0131"
    CONSERVATIVE = "Muhafazakar"
    PROGRESSIVE = "Yenilik\u00e7i"


class PoliticalView(str, Enum):
    LEFT = "Sol"
    CENTER_LEFT = "Merkez Sol"
    CENTER = "Merkez"
    CENTER_RIGHT = "Merkez Sa\u011f"
    RIGHT = "Sa\u011f"
    APOLITICAL = "Apolitik"


class Religion(str, Enum):
    MUSLIM = "M\u00fcsl\u00fcman"
    CHRISTIAN = "Hristiyan"
    JEWISH = "Yahudi"
    ATHEIST = "Ateist"
    AGNOSTIC = "Agnostik"
    HINDU = "Hindu"
    BUDDHIST = "Budist"
    OTHER = "Di\u011fer"


class ShoppingPreference(str, Enum):
    ONLINE_ONLY = "Sadece Online"
    MOSTLY_ONLINE = "\u00c7o\u011funlukla Online"
    HYBRID = "Karma"
    MOSTLY_PHYSICAL = "\u00c7o\u011funlukla Fiziksel"
    PHYSICAL_ONLY = "Sadece Fiziksel"


class BuyingStyle(str, Enum):
    PLANNER = "Planl\u0131 Al\u0131c\u0131"
    IMPULSIVE = "Anl\u0131k Al\u0131c\u0131"
    RESEARCHER = "Ara\u015ft\u0131rmac\u0131"
    BARGAIN_HUNTER = "F\u0131rsat Avc\u0131s\u0131"
    BRAND_LOYAL = "Marka Ba\u011f\u0131ml\u0131s\u0131"


class TechAdoption(str, Enum):
    EARLY_ADOPTER = "Erken Benimseyen"
    EARLY_MAJORITY = "Erken \u00c7o\u011funluk"
    LATE_MAJORITY = "Ge\u00e7 \u00c7o\u011funluk"
    TRADITIONALIST = "Gelenek\u00e7i"


class SocialMediaInfluence(str, Enum):
    INFLUENCER_FOLLOWER = "Influencer Takip\u00e7isi"
    REVIEW_READER = "Yorum Okuyucu"
    AD_RESISTANT = "Reklam Kar\u015f\u0131t\u0131"
    FRIEND_REFERRAL = "Arkada\u015f Referans\u0131"


class FinancialBehavior(str, Enum):
    SAVER = "Tasarruf\u00e7u"
    SPENDER = "Harcamac\u0131"
    INVESTOR = "Yat\u0131r\u0131mc\u0131"
    DEBT_USER = "Bor\u00e7 Kullan\u0131c\u0131s\u0131"


class ScreenTime(str, Enum):
    LOW = "1-2 saat"
    MEDIUM = "3-5 saat"
    HIGH = "5+ saat"


class OnlineShoppingFrequency(str, Enum):
    NEVER = "Hi\u00e7"
    MONTHLY = "Ayda 1"
    WEEKLY = "Haftada 1"
    DAILY = "Her g\u00fcn"


class PaymentPreference(str, Enum):
    CREDIT_CARD = "Kredi Kart\u0131"
    DEBIT_CARD = "Banka Kart\u0131"
    CASH_ON_DELIVERY = "Kap\u0131da \u00d6deme"
    DIGITAL_WALLET = "Dijital C\u00fczdan"


class PersonalValues(BaseModel):
    animal_lover: bool = False
    environmentalist: bool = False
    family_oriented: bool = False


class DigitalHabits(BaseModel):
    primary_platform: str = "Instagram"
    screen_time: ScreenTime = ScreenTime.MEDIUM
    online_shopping_freq: OnlineShoppingFrequency = OnlineShoppingFrequency.MONTHLY
    payment_preference: PaymentPreference = PaymentPreference.CREDIT_CARD


class Anxiety(BaseModel):
    id: str
    name: str
    description: str


class BigFiveTraits(BaseModel):
    openness: float = Field(ge=0.0, le=1.0, default=0.5)
    conscientiousness: float = Field(ge=0.0, le=1.0, default=0.5)
    extraversion: float = Field(ge=0.0, le=1.0, default=0.5)
    agreeableness: float = Field(ge=0.0, le=1.0, default=0.5)
    neuroticism: float = Field(ge=0.0, le=1.0, default=0.5)


class Persona(BaseModel):
    """Global Persona Model - 34 Fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    region: Region
    country: str
    city: str
    age: int = Field(ge=18, le=80)
    gender: Gender
    marital_status: MaritalStatus
    children_count: int = Field(ge=0, le=6, default=0)
    education: Education
    occupation: str
    income_level: IncomeLevel
    purchasing_power: float = Field(ge=0.0, le=1.0, default=0.5)
    life_outlook: LifeOutlook
    political_view: Optional[PoliticalView] = None
    religion: Religion
    personal_values: PersonalValues = Field(default_factory=PersonalValues)
    shopping_preference: ShoppingPreference
    buying_style: BuyingStyle
    tech_adoption: TechAdoption
    social_media_influence: SocialMediaInfluence
    financial_behavior: FinancialBehavior
    digital_habits: DigitalHabits = Field(default_factory=DigitalHabits)
    primary_anxiety: Optional[Anxiety] = None
    secondary_anxiety: Optional[Anxiety] = None
    personality: BigFiveTraits = Field(default_factory=BigFiveTraits)
    
    class Config:
        use_enum_values = True


class PersonaFilters(BaseModel):
    """Persona \u00fcretim filtreleri - plan bazl\u0131 eri\u015fim."""
    # Pro filters
    gender: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    income_levels: Optional[list[str]] = None
    # Business filters
    education_levels: Optional[list[str]] = None
    buying_styles: Optional[list[str]] = None
    marital_statuses: Optional[list[str]] = None
    # Enterprise filters
    tech_adoptions: Optional[list[str]] = None
    online_shopping_freqs: Optional[list[str]] = None
    financial_behaviors: Optional[list[str]] = None


class PersonaConfig(BaseModel):
    region: Region = Region.TURKEY
    min_age: int = 18
    max_age: int = 80
    gender_balance: bool = True
    country_filter: Optional[str] = None
    city_filter: Optional[str] = None
    filters: Optional[PersonaFilters] = None


class PersonaDecision(BaseModel):
    persona_id: str
    persona_name: str
    campaign_id: str
    decision: bool
    confidence: int = Field(ge=1, le=10)
    reasoning: str
    influencing_factors: list[str] = Field(default_factory=list)
    anxiety_impact: Optional[str] = None
    timestamp: str


class ComparisonResult(BaseModel):
    persona_id: str
    persona_name: str
    persona_political_view: Optional[str] = None
    persona_age: int
    persona_gender: str
    persona_occupation: str
    choice: str
    confidence: int = Field(ge=1, le=10)
    reasoning: str
    option_scores: dict = Field(default_factory=dict)
    influencing_factors: list[str] = Field(default_factory=list)
    political_influence: Optional[str] = None
    timestamp: str