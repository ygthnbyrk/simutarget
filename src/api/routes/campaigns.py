"""
SimuTarget Campaign API - DB-Backed Version
Kredi Sistemi + Persona Engine + LLM + PostgreSQL

Akış:
  POST /campaigns/ → Kampanya oluştur (DB'ye kaydet)
  POST /campaigns/{id}/test → Auth → Feature Gate → Kredi Reserve → Persona Üret → LLM → DB'ye Kaydet → Kredi Confirm
  POST /campaigns/{id}/compare → A/B karşılaştırma (aynı akış)
  GET  /campaigns/ → Kullanıcının kampanyalarını listele (DB'den)
  GET  /campaigns/{id} → Kampanya detayı + sonuçlar (DB'den)
  GET  /campaigns/{id}/results → Test sonuçları (DB'den)
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid
import time
import base64
import os
import tempfile

from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.models import (
    User, Campaign as CampaignDB,
    CampaignPersonaResponse, UsageLog
)
from src.database.credit_service import CreditService, FeatureGateService
from src.api.auth import get_current_user
from src.personas.factory import PersonaFactory
from src.personas.models import PersonaConfig, Region, PersonaFilters
from src.inference.openai_client import SimuTargetLLM

router = APIRouter()

# ============================================
# GÖRSEL UPLOAD AYARLARI
# ============================================

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "campaigns")
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


# ============================================
# REQUEST / RESPONSE MODELLERİ
# ============================================

class CampaignCreate(BaseModel):
    """Kampanya oluşturma isteği."""
    name: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)
    region: str = Field(default="TR")


class PersonaFiltersRequest(BaseModel):
    """Frontend'den gelen filtre verisi."""
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


class CampaignTestRequest(BaseModel):
    """Kampanya test isteği."""
    persona_count: int = Field(default=10, ge=1, le=500)
    region: Optional[str] = Field(default=None)
    filters: Optional[PersonaFiltersRequest] = None
    lang: str = Field(default="tr", description="Response language (en, tr)")


class CampaignCompareRequest(BaseModel):
    """A/B karşılaştırma isteği."""
    content_b: str = Field(..., min_length=10)
    persona_count: int = Field(default=10, ge=1, le=500)
    region: Optional[str] = Field(default=None)
    filters: Optional[PersonaFiltersRequest] = None
    lang: str = Field(default="tr", description="Response language (en, tr)")

class CampaignMultiCompareRequest(BaseModel):
    """Multi karsilastirma istegi (3-4 secenek)."""
    options: dict[str, str] = Field(..., min_length=3, max_length=4)
    persona_count: int = Field(default=10, ge=1, le=500)
    region: Optional[str] = Field(default=None)
    filters: Optional[PersonaFiltersRequest] = None
    lang: str = Field(default="tr", description="Response language (en, tr)")


class CampaignResponse(BaseModel):
    """Kampanya bilgisi."""
    id: int
    name: str
    type: str
    content: dict
    region: str
    status: str
    persona_count: int
    credits_consumed: int
    created_at: str
    has_image: bool = False
    image_filename: Optional[str] = None
    results_summary: Optional[dict] = None


class TestResultResponse(BaseModel):
    """Kampanya test sonucu."""
    campaign_id: int
    campaign_name: str
    total_personas: int
    successful_evaluations: int
    failed_evaluations: int
    yes_count: int
    no_count: int
    conversion_rate: float
    avg_confidence: float
    credits_used: int
    results: list[dict]


class CompareResultResponse(BaseModel):
    """A/B karşılaştırma sonucu."""
    campaign_id: int
    campaign_name: str
    option_a: str
    option_b: str
    total_personas: int
    a_votes: int
    b_votes: int
    neither_votes: int
    a_percentage: float
    b_percentage: float
    avg_confidence: float
    credits_used: int
    results: list[dict]

class MultiCompareResultResponse(BaseModel):
    campaign_id: int
    campaign_name: str
    options: dict[str, str]
    total_personas: int
    votes: dict[str, int]
    percentages: dict[str, float]
    neither_votes: int
    avg_confidence: float
    credits_used: int
    results: list[dict]


# ============================================
# YARDIMCI FONKSİYONLAR
# ============================================

VALID_REGIONS = ["TR", "US", "EU", "MENA"]


def _validate_region(region: str) -> str:
    region = region.upper()
    if region not in VALID_REGIONS:
        raise HTTPException(400, f"Geçersiz bölge: {region}. Geçerli: {', '.join(VALID_REGIONS)}")
    return region


def _get_campaign_or_404(campaign_id: int, user_id: int, db: Session) -> CampaignDB:
    """Kampanyayı DB'den getir, yoksa veya başkasının ise hata."""
    campaign = db.query(CampaignDB).filter(CampaignDB.id == campaign_id).first()
    if not campaign:
        raise HTTPException(404, "Kampanya bulunamadı.")
    if campaign.user_id != user_id:
        raise HTTPException(403, "Bu kampanyaya erişim yetkiniz yok.")
    return campaign


# Test türüne göre kredi çarpanı (kaç kampanya değerlendiriliyor)
CREDIT_MULTIPLIERS = {
    "single": 1,        # 1 kampanya → persona × 1
    "ab_compare": 2,    # 2 kampanya → persona × 2
    "multi_compare": 3, # 3-4 kampanya → persona × 3 (ortalama)
}


def _check_credits_and_features(
    user: User, db: Session, persona_count: int, test_type: str = "single",
    campaign_count: int = 1,
) -> tuple[CreditService, int]:
    """Feature gate + kredi kontrolü."""
    feature_gate = FeatureGateService(db)
    access = feature_gate.check_test_type_access(user.id, test_type)

    if not access["allowed"]:
        raise HTTPException(
            403,
            f"{access['message']} Yükseltme önerisi: {access.get('upgrade_to', 'pro')}"
        )

    max_personas = feature_gate.get_max_personas(user.id)
    if persona_count > max_personas:
        raise HTTPException(
            400,
            f"Planınız tek sorguda en fazla {max_personas} persona destekliyor. İstenen: {persona_count}"
        )

    credit_service = CreditService(db)
    balance = credit_service.get_balance(user.id)
    
    # Kredi hesabı: persona sayısı × kampanya sayısı
    multiplier = campaign_count if test_type != "single" else 1
    required_credits = persona_count * multiplier

    if balance < required_credits:
        raise HTTPException(
            402,
            f"Yetersiz kredi. Gerekli: {required_credits} ({persona_count} persona × {multiplier} kampanya), Mevcut: {balance}."
        )

    return credit_service, required_credits


def _build_persona_data(persona, lang: str = "tr") -> dict:
    """Persona verilerini dict olarak oluştur — her zaman ham değer kaydeder."""
    def _val(attr):
        return attr.value if hasattr(attr, 'value') else str(attr)
    return {
        "name": persona.name,
        "age": persona.age,
        "gender": _val(persona.gender),
        "city": persona.city,
        "country": persona.country,
        "occupation": persona.occupation,
        "income_level": _val(persona.income_level),
        "education": _val(persona.education) if hasattr(persona, 'education') else None,
        "buying_style": _val(persona.buying_style) if hasattr(persona, 'buying_style') else None,
    }


def _build_campaign_response(campaign: CampaignDB) -> CampaignResponse:
    """DB Campaign → API Response dönüşümü."""
    content = campaign.content if isinstance(campaign.content, dict) else {"text": str(campaign.content)}
    
    # Görsel bilgisi
    has_image = bool(content.get("image_path"))
    image_filename = content.get("image_filename")
    
    # Response'a image_path göndermiyoruz (güvenlik), sadece filename
    safe_content = {k: v for k, v in content.items() if k != "image_path"}
    
    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        type=campaign.type,
        content=safe_content,
        region=campaign.region,
        status=campaign.status,
        persona_count=campaign.persona_count,
        credits_consumed=campaign.credits_consumed or 0,
        created_at=campaign.created_at.isoformat(),
        has_image=has_image,
        image_filename=image_filename,
        results_summary=campaign.results,
    )


def _build_persona_filters(request_filters: Optional[PersonaFiltersRequest]) -> Optional[PersonaFilters]:
    """Frontend filtre isteğini PersonaFilters modeline dönüştür."""
    if not request_filters:
        return None

    # Boş mu kontrol et (tüm alanlar None ise filtre yok demektir)
    data = request_filters.model_dump(exclude_none=True)
    if not data:
        return None

    return PersonaFilters(
        gender=request_filters.gender,
        min_age=request_filters.min_age,
        max_age=request_filters.max_age,
        income_levels=request_filters.income_levels,
        education_levels=request_filters.education_levels,
        buying_styles=request_filters.buying_styles,
        marital_statuses=request_filters.marital_statuses,
        tech_adoptions=request_filters.tech_adoptions,
        online_shopping_freqs=request_filters.online_shopping_freqs,
        financial_behaviors=request_filters.financial_behaviors,
    )


# ============================================
# GÖRSEL YARDIMCI FONKSİYONLAR
# ============================================

def _ensure_upload_dir():
    """Upload dizinini oluştur."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def _get_campaign_image_base64(campaign: CampaignDB) -> Optional[str]:
    """Kampanyanın görselini base64 olarak oku. Yoksa None döner."""
    content = campaign.content if isinstance(campaign.content, dict) else {}
    image_path = content.get("image_path")
    
    if not image_path or not os.path.exists(image_path):
        return None
    
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return None


def _check_image_feature_gate(user: User, db: Session):
    """Kullanıcının görsel özelliğine erişimi var mı kontrol et."""
    feature_gate = FeatureGateService(db)
    access = feature_gate.check_media_access(user.id, "image")
    
    if not access["allowed"]:
        raise HTTPException(
            403,
            f"{access['message']} Yükseltme önerisi: {access.get('upgrade_to', 'pro')}"
        )


# ============================================
# ENDPOINTS
# ============================================

@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    request: CampaignCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Yeni kampanya oluştur (DB'ye kaydet)."""
    region = _validate_region(request.region)

    campaign = CampaignDB(
        user_id=user.id,
        name=request.name,
        type="single",
        content={"text": request.content},
        persona_count=0,
        region=region,
        status="draft",
        credits_consumed=0,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    return _build_campaign_response(campaign)


@router.post("/{campaign_id}/upload-image")
async def upload_campaign_image(
    campaign_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Kampanyaya görsel yükle.
    Feature gate: Sadece Pro, Business ve Enterprise planlar.
    Max 5MB, desteklenen formatlar: JPEG, PNG, WebP, GIF.
    """
    # 1. Feature gate kontrolü
    _check_image_feature_gate(user, db)
    
    # 2. Kampanya kontrolü
    campaign = _get_campaign_or_404(campaign_id, user.id, db)
    
    # 3. Dosya tipi kontrolü
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            400,
            f"Desteklenmeyen dosya formatı: {file.content_type}. "
            f"Desteklenen: JPEG, PNG, WebP, GIF"
        )
    
    # 4. Boyut kontrolü
    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            400,
            f"Dosya çok büyük: {len(contents) / (1024*1024):.1f}MB. Maksimum: 5MB"
        )
    
    # 5. Dosyayı kaydet
    _ensure_upload_dir()
    
    # Benzersiz dosya adı
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    filename = f"campaign_{campaign_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Eski görseli sil (varsa)
    old_content = campaign.content if isinstance(campaign.content, dict) else {}
    old_image = old_content.get("image_path")
    if old_image and os.path.exists(old_image):
        try:
            os.remove(old_image)
        except OSError:
            pass
    
    # Yeni görseli yaz
    with open(filepath, "wb") as f:
        f.write(contents)
    
    # 6. Campaign content'e image_path ekle
    if isinstance(campaign.content, dict):
        campaign.content = {**campaign.content, "image_path": filepath, "image_filename": filename}
    else:
        campaign.content = {"text": str(campaign.content), "image_path": filepath, "image_filename": filename}
    
    db.commit()
    db.refresh(campaign)
    
    return {
        "status": "success",
        "message": "Görsel başarıyla yüklendi.",
        "campaign_id": campaign_id,
        "image_filename": filename,
        "image_size_kb": round(len(contents) / 1024, 1),
        "content_type": file.content_type,
    }


@router.delete("/{campaign_id}/image")
async def delete_campaign_image(
    campaign_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Kampanyadaki görseli sil."""
    campaign = _get_campaign_or_404(campaign_id, user.id, db)
    
    content = campaign.content if isinstance(campaign.content, dict) else {}
    image_path = content.get("image_path")
    
    if not image_path:
        raise HTTPException(404, "Bu kampanyada görsel bulunamadı.")
    
    # Dosyayı sil
    if os.path.exists(image_path):
        os.remove(image_path)
    
    # Content'ten image bilgilerini kaldır
    content.pop("image_path", None)
    content.pop("image_filename", None)
    campaign.content = content
    
    db.commit()
    
    return {"status": "success", "message": "Görsel silindi.", "campaign_id": campaign_id}


@router.get("/", response_model=list[CampaignResponse])
async def list_campaigns(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Kullanıcının kampanyalarını listele."""
    campaigns = (
        db.query(CampaignDB)
        .filter(CampaignDB.user_id == user.id)
        .order_by(CampaignDB.created_at.desc())
        .all()
    )
    return [_build_campaign_response(c) for c in campaigns]


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Kampanya detayını getir."""
    campaign = _get_campaign_or_404(campaign_id, user.id, db)
    return _build_campaign_response(campaign)


@router.post("/{campaign_id}/test", response_model=TestResultResponse)
async def test_campaign(
    campaign_id: int,
    request: CampaignTestRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Kampanyayı sentetik personalarla test et.
    Auth → Feature Gate → Kredi Reserve → Persona Üret → LLM → DB Kaydet → Kredi Confirm
    """
    start_time = time.time()

    # 1. Kampanya kontrolü
    campaign = _get_campaign_or_404(campaign_id, user.id, db)
    region = _validate_region(request.region or campaign.region)
    campaign_text = campaign.content.get("text", "") if isinstance(campaign.content, dict) else str(campaign.content)
    
    # Görsel kontrolü — varsa base64 oku
    image_base64 = _get_campaign_image_base64(campaign)

    # 2. Feature gate + kredi kontrolü
    credit_service, required_credits = _check_credits_and_features(
        user=user, db=db, persona_count=request.persona_count, test_type="single",
    )

    # 3. Kredi RESERVE
    reference_id = f"campaign_{campaign_id}_{uuid.uuid4().hex[:8]}"
    reserve_result = credit_service.check_and_reserve(
        user_id=user.id, amount=required_credits, reference_id=reference_id,
    )
    if not reserve_result["success"]:
        raise HTTPException(402, reserve_result["message"])

    try:
        # 4. Persona üret (filtreli)
        config = PersonaConfig(
            region=Region(region),
            filters=_build_persona_filters(request.filters),
        )
        factory = PersonaFactory(config)
        personas = factory.generate_batch(request.persona_count)

        # 5. LLM değerlendirmesi (PARALEL)
        llm = SimuTargetLLM()
        campaign.status = "running"
        db.commit()

        test_result = await llm.test_campaign_async(
            personas=personas,
            campaign_content=campaign_text,
            campaign_id=str(campaign_id),
            max_concurrent=10,
            verbose=False,
            lang=request.lang,
            image_base64=image_base64,
        )

        # 6. Sonuçları DB'ye kaydet
        results_data = []
        for r in test_result.results:
            decision_str = "EVET" if (r.decision and r.decision.decision) else "HAYIR"
            confidence = r.decision.confidence if r.decision else 0
            reasoning = r.decision.reasoning if r.decision else "Değerlendirme başarısız"

            # CampaignPersonaResponse tablosuna yaz
            persona_response = CampaignPersonaResponse(
                campaign_id=campaign.id,
                persona_data=_build_persona_data(r.persona, lang=request.lang),
                decision=decision_str,
                confidence=confidence,
                reasoning=reasoning,
            )
            db.add(persona_response)

            results_data.append({
                "persona_name": r.persona.name,
                "persona_age": r.persona.age,
                "persona_gender": r.persona.gender.value if hasattr(r.persona.gender, 'value') else str(r.persona.gender),
                "persona_city": r.persona.city,
                "persona_country": r.persona.country,
                "persona_occupation": r.persona.occupation,
                "persona_income": r.persona.income_level.value if hasattr(r.persona.income_level, 'value') else str(r.persona.income_level),
                "decision": r.decision.decision if r.decision else None,
                "confidence": confidence,
                "reasoning": reasoning,
                "success": r.success,
            })

        # Kampanya özetini güncelle
        elapsed_ms = int((time.time() - start_time) * 1000)

        campaign.status = "completed"
        campaign.persona_count = test_result.total_personas
        campaign.credits_consumed = required_credits
        campaign.results = {
            "total_personas": test_result.total_personas,
            "successful": test_result.successful_evaluations,
            "failed": test_result.failed_evaluations,
            "yes_count": test_result.yes_count,
            "no_count": test_result.no_count,
            "conversion_rate": round(test_result.conversion_rate, 1),
            "avg_confidence": round(test_result.avg_confidence, 1),
            "response_time_ms": elapsed_ms,
        }

        # Usage log kaydet
        usage_log = UsageLog(
            user_id=user.id,
            campaign_id=campaign.id,
            persona_count=request.persona_count,
            credits_used=required_credits,
            region=region,
            response_time_ms=elapsed_ms,
        )
        db.add(usage_log)

        # 7. Kredi CONFIRM
        credit_service.confirm_usage(
            user_id=user.id, amount=required_credits, reference_id=reference_id,
        )

        db.commit()

        return TestResultResponse(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            total_personas=test_result.total_personas,
            successful_evaluations=test_result.successful_evaluations,
            failed_evaluations=test_result.failed_evaluations,
            yes_count=test_result.yes_count,
            no_count=test_result.no_count,
            conversion_rate=test_result.conversion_rate,
            avg_confidence=test_result.avg_confidence,
            credits_used=required_credits,
            results=results_data,
        )

    except Exception as e:
        credit_service.release_reserve(
            user_id=user.id, amount=required_credits, reference_id=reference_id,
        )
        campaign.status = "failed"
        db.commit()

        raise HTTPException(
            500, f"Test sırasında hata: {str(e)}. Kredileriniz iade edildi."
        )


@router.post("/{campaign_id}/compare", response_model=CompareResultResponse)
async def compare_campaigns(
    campaign_id: int,
    request: CampaignCompareRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    A/B karşılaştırma — kampanyayı ikinci seçenekle karşılaştır.
    Auth → Feature Gate (ab_compare) → Kredi Reserve → Persona Üret → LLM → DB Kaydet → Confirm
    """
    start_time = time.time()

    # 1. Kampanya kontrolü
    campaign = _get_campaign_or_404(campaign_id, user.id, db)
    region = _validate_region(request.region or campaign.region)
    campaign_text = campaign.content.get("text", "") if isinstance(campaign.content, dict) else str(campaign.content)
    
    # Görsel kontrolü — A seçeneği için
    image_a_base64 = _get_campaign_image_base64(campaign)

    # 2. Feature gate + kredi kontrolü
    credit_service, required_credits = _check_credits_and_features(
        user=user, db=db, persona_count=request.persona_count, test_type="ab_compare",
        campaign_count=2,
    )

    # 3. Kredi RESERVE
    reference_id = f"compare_{campaign_id}_{uuid.uuid4().hex[:8]}"
    reserve_result = credit_service.check_and_reserve(
        user_id=user.id, amount=required_credits, reference_id=reference_id,
    )
    if not reserve_result["success"]:
        raise HTTPException(402, reserve_result["message"])

    try:
        # 4. Persona üret (filtreli)
        config = PersonaConfig(
            region=Region(region),
            filters=_build_persona_filters(request.filters),
        )
        factory = PersonaFactory(config)
        personas = factory.generate_batch(request.persona_count)

        # 5. LLM A/B karşılaştırma
        llm = SimuTargetLLM()

        campaign.type = "ab"
        campaign.content = {"text_a": campaign_text, "text_b": request.content_b}
        campaign.status = "running"
        db.commit()

        a_votes = 0
        b_votes = 0
        neither_votes = 0
        total_confidence = 0
        results_data = []

        # PARALEL A/B karşılaştırma
        import asyncio
        semaphore = asyncio.Semaphore(10)

        async def compare_one(persona):
            async with semaphore:
                return persona, await llm.compare_campaigns_async(
                    persona=persona,
                    campaign_a=campaign_text,
                    campaign_b=request.content_b,
                    lang=request.lang,
                    image_a_base64=image_a_base64,
                )

        tasks = [compare_one(p) for p in personas]
        comparisons = await asyncio.gather(*tasks)

        for persona, comparison in comparisons:
            if comparison.choice == "A":
                a_votes += 1
            elif comparison.choice == "B":
                b_votes += 1
            else:
                neither_votes += 1

            total_confidence += comparison.confidence

            # DB'ye kaydet
            persona_response = CampaignPersonaResponse(
                campaign_id=campaign.id,
                persona_data=_build_persona_data(persona, lang=request.lang),
                decision=comparison.choice,
                confidence=comparison.confidence,
                reasoning=comparison.reasoning,
            )
            db.add(persona_response)

            results_data.append({
                "persona_name": persona.name,
                "persona_age": persona.age,
                "persona_gender": persona.gender.value if hasattr(persona.gender, 'value') else str(persona.gender),
                "persona_city": persona.city,
                "persona_occupation": persona.occupation,
                "choice": comparison.choice,
                "confidence": comparison.confidence,
                "reasoning": comparison.reasoning,
                "a_score": comparison.option_scores.get("A", 0),
                "b_score": comparison.option_scores.get("B", 0),
                "influencing_factors": comparison.influencing_factors,
            })

        # Kampanya özetini güncelle
        total = len(personas)
        elapsed_ms = int((time.time() - start_time) * 1000)

        campaign.status = "completed"
        campaign.persona_count = total
        campaign.credits_consumed = required_credits
        campaign.results = {
            "type": "ab_compare",
            "total_personas": total,
            "a_votes": a_votes,
            "b_votes": b_votes,
            "neither_votes": neither_votes,
            "a_percentage": round((a_votes / total * 100), 1) if total > 0 else 0,
            "b_percentage": round((b_votes / total * 100), 1) if total > 0 else 0,
            "avg_confidence": round(total_confidence / total, 1) if total > 0 else 0,
            "response_time_ms": elapsed_ms,
        }

        # Usage log
        usage_log = UsageLog(
            user_id=user.id,
            campaign_id=campaign.id,
            persona_count=total,
            credits_used=required_credits,
            region=region,
            response_time_ms=elapsed_ms,
        )
        db.add(usage_log)

        # Kredi CONFIRM
        credit_service.confirm_usage(
            user_id=user.id, amount=required_credits, reference_id=reference_id,
        )

        db.commit()

        avg_conf = total_confidence / total if total > 0 else 0

        return CompareResultResponse(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            option_a=campaign_text[:200],
            option_b=request.content_b[:200],
            total_personas=total,
            a_votes=a_votes,
            b_votes=b_votes,
            neither_votes=neither_votes,
            a_percentage=round((a_votes / total * 100), 1) if total > 0 else 0,
            b_percentage=round((b_votes / total * 100), 1) if total > 0 else 0,
            avg_confidence=round(avg_conf, 1),
            credits_used=required_credits,
            results=results_data,
        )

    except Exception as e:
        credit_service.release_reserve(
            user_id=user.id, amount=required_credits, reference_id=reference_id,
        )
        campaign.status = "failed"
        db.commit()

        raise HTTPException(
            500, f"Karşılaştırma sırasında hata: {str(e)}. Kredileriniz iade edildi."
        )


@router.post("/{campaign_id}/multi-compare", response_model=MultiCompareResultResponse)
async def multi_compare_campaigns(
    campaign_id: int,
    request: CampaignMultiCompareRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Multi karsilastirma — 3 veya 4 secenegi karsilastir.
    Auth -> Feature Gate (multi_compare) -> Kredi Reserve -> Persona Uret -> LLM -> DB Kaydet -> Confirm
    """
    start_time = time.time()

    # 1. Kampanya kontrolu
    campaign = _get_campaign_or_404(campaign_id, user.id, db)
    region = _validate_region(request.region or campaign.region)

    # 2. Secenek sayisi kontrolu (3 veya 4)
    if len(request.options) < 3:
        raise HTTPException(400, "Multi karsilastirma icin en az 3 secenek gerekli.")
    if len(request.options) > 4:
        raise HTTPException(400, "En fazla 4 secenek desteklenir.")

    # 3. Feature gate + kredi kontrolu
    credit_service, required_credits = _check_credits_and_features(
        user=user, db=db, persona_count=request.persona_count, test_type="multi_compare",
        campaign_count=len(request.options),
    )

    # 4. Kredi RESERVE
    reference_id = f"multi_{campaign_id}_{uuid.uuid4().hex[:8]}"
    reserve_result = credit_service.check_and_reserve(
        user_id=user.id, amount=required_credits, reference_id=reference_id,
    )
    if not reserve_result["success"]:
        raise HTTPException(402, reserve_result["message"])

    try:
        # 5. Persona uret (filtreli)
        config = PersonaConfig(
            region=Region(region),
            filters=_build_persona_filters(request.filters),
        )
        factory = PersonaFactory(config)
        personas = factory.generate_batch(request.persona_count)

        # 6. LLM multi karsilastirma
        llm = SimuTargetLLM()

        option_labels = list(request.options.keys())
        campaign.type = "multi"
        campaign.content = request.options
        campaign.status = "running"
        db.commit()

        votes = {label: 0 for label in option_labels}
        neither_votes = 0
        total_confidence = 0
        results_data = []

        # PARALEL Multi karşılaştırma
        import asyncio
        semaphore = asyncio.Semaphore(10)

        async def multi_compare_one(persona):
            async with semaphore:
                return persona, await llm.multi_compare_campaigns_async(
                    persona=persona,
                    campaigns=request.options,
                    lang=request.lang,
                )

        tasks = [multi_compare_one(p) for p in personas]
        comparisons = await asyncio.gather(*tasks)

        for persona, comparison in comparisons:
            if comparison.choice in option_labels:
                votes[comparison.choice] += 1
            else:
                neither_votes += 1

            total_confidence += comparison.confidence

            # DB'ye kaydet
            persona_response = CampaignPersonaResponse(
                campaign_id=campaign.id,
                persona_data=_build_persona_data(persona, lang=request.lang),
                decision=comparison.choice,
                confidence=comparison.confidence,
                reasoning=comparison.reasoning,
            )
            db.add(persona_response)

            results_data.append({
                "persona_name": persona.name,
                "persona_age": persona.age,
                "persona_gender": persona.gender.value if hasattr(persona.gender, 'value') else str(persona.gender),
                "persona_city": persona.city,
                "persona_occupation": persona.occupation,
                "choice": comparison.choice,
                "confidence": comparison.confidence,
                "reasoning": comparison.reasoning,
                "option_scores": comparison.option_scores,
                "influencing_factors": comparison.influencing_factors,
            })

        # Kampanya ozetini guncelle
        total = len(personas)
        elapsed_ms = int((time.time() - start_time) * 1000)

        percentages = {}
        for label in option_labels:
            percentages[label] = round((votes[label] / total * 100), 1) if total > 0 else 0

        campaign.status = "completed"
        campaign.persona_count = total
        campaign.credits_consumed = required_credits
        campaign.results = {
            "type": "multi_compare",
            "total_personas": total,
            "votes": votes,
            "percentages": percentages,
            "neither_votes": neither_votes,
            "avg_confidence": round(total_confidence / total, 1) if total > 0 else 0,
            "response_time_ms": elapsed_ms,
        }

        # Usage log
        usage_log = UsageLog(
            user_id=user.id,
            campaign_id=campaign.id,
            persona_count=total,
            credits_used=required_credits,
            region=region,
            response_time_ms=elapsed_ms,
        )
        db.add(usage_log)

        # Kredi CONFIRM
        credit_service.confirm_usage(
            user_id=user.id, amount=required_credits, reference_id=reference_id,
        )

        db.commit()

        return MultiCompareResultResponse(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            options={k: v[:200] for k, v in request.options.items()},
            total_personas=total,
            votes=votes,
            percentages=percentages,
            neither_votes=neither_votes,
            avg_confidence=round(total_confidence / total, 1) if total > 0 else 0,
            credits_used=required_credits,
            results=results_data,
        )

    except Exception as e:
        credit_service.release_reserve(
            user_id=user.id, amount=required_credits, reference_id=reference_id,
        )
        campaign.status = "failed"
        db.commit()

        raise HTTPException(
            500, f"Multi karsilastirma sirasinda hata: {str(e)}. Kredileriniz iade edildi."
        )

@router.get("/{campaign_id}/results")
async def get_campaign_results(
    campaign_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Kampanya test sonuçlarını DB'den getir."""
    campaign = _get_campaign_or_404(campaign_id, user.id, db)

    responses = (
        db.query(CampaignPersonaResponse)
        .filter(CampaignPersonaResponse.campaign_id == campaign.id)
        .order_by(CampaignPersonaResponse.id)
        .all()
    )

    persona_results = [
        {
            "persona_data": r.persona_data,
            "decision": r.decision,
            "confidence": r.confidence,
            "reasoning": r.reasoning,
            "created_at": r.created_at.isoformat(),
        }
        for r in responses
    ]

    return {
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "type": campaign.type,
        "status": campaign.status,
        "region": campaign.region,
        "summary": campaign.results,
        "credits_consumed": campaign.credits_consumed,
        "persona_count": campaign.persona_count,
        "created_at": campaign.created_at.isoformat(),
        "persona_responses": persona_results,
    }


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Kampanya ve ilişkili sonuçları sil."""
    campaign = _get_campaign_or_404(campaign_id, user.id, db)

    db.query(CampaignPersonaResponse).filter(
        CampaignPersonaResponse.campaign_id == campaign.id
    ).delete()

    db.delete(campaign)
    db.commit()

    return {"status": "deleted", "campaign_id": campaign_id}


# ============================================
# PDF RAPOR İNDİRME
# ============================================

PDF_ALLOWED_PLANS = ["pro", "business", "enterprise"]

@router.get("/{campaign_id}/download-pdf")
async def download_campaign_pdf(
    campaign_id: int,
    lang: str = "en",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Kampanya sonuçlarını PDF olarak indir.
    Pro: Temiz özet rapor
    Business/Enterprise: Detaylı infografik + grafikler + demografik analiz
    """
    # Plan kontrolü
    from src.database.models import Subscription
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).all()
    sub = next((s for s in sub if s.is_active), None)
    plan_slug = sub.plan.slug if sub and sub.plan else "disposable"

    if plan_slug not in PDF_ALLOWED_PLANS:
        raise HTTPException(
            status_code=403,
            detail="PDF export requires Pro plan or higher. Please upgrade your subscription."
        )

    # Kampanya ve sonuçları getir
    campaign = _get_campaign_or_404(campaign_id, user.id, db)

    if campaign.status != "completed":
        raise HTTPException(status_code=400, detail="Campaign must be completed before downloading PDF.")

    responses = (
        db.query(CampaignPersonaResponse)
        .filter(CampaignPersonaResponse.campaign_id == campaign.id)
        .order_by(CampaignPersonaResponse.id)
        .all()
    )

    if not responses:
        raise HTTPException(status_code=404, detail="No results found for this campaign.")

    # Kampanya türünü belirle
    campaign_type = campaign.type or "single"
    summary = campaign.results or {}
    content = campaign.content or {}

    # Persona sonuçlarını dönüştür
    results_list = []
    for r in responses:
        pd = r.persona_data or {}
        results_list.append({
            "persona_name": pd.get("name", "Unknown"),
            "persona_age": pd.get("age", 0),
            "persona_gender": pd.get("gender", ""),
            "persona_city": pd.get("city", ""),
            "persona_occupation": pd.get("occupation", ""),
            "decision": r.decision or "",
            "choice": r.decision or "",
            "confidence": r.confidence or 0,
            "reasoning": r.reasoning or "",
            "persona_data": pd,
        })

    # PDF report_data oluştur
    report_data = {
        "campaign_name": campaign.name,
        "test_type": campaign_type,
        "region": campaign.region or "TR",
        "created_at": campaign.created_at.isoformat() if campaign.created_at else datetime.now().isoformat(),
        "total_personas": campaign.persona_count or len(responses),
        "results": results_list,
    }

    # Türe göre ek veriler
    if campaign_type == "single":
        report_data["campaign_content"] = content.get("text", content.get("content", ""))
        report_data["approval_rate"] = summary.get("conversion_rate", 0)
        report_data["avg_confidence"] = summary.get("avg_confidence", 0)
        report_data["yes_count"] = summary.get("yes_count", 0)
        report_data["no_count"] = summary.get("no_count", 0)

    elif campaign_type == "ab_compare":
        report_data["content_a"] = content.get("content_a", content.get("text", ""))
        report_data["content_b"] = content.get("content_b", "")
        report_data["campaign_content"] = f"A: {report_data['content_a'][:200]}\n\nB: {report_data['content_b'][:200]}"
        report_data["a_votes"] = summary.get("a_votes", 0)
        report_data["b_votes"] = summary.get("b_votes", 0)
        report_data["neither_votes"] = summary.get("neither_votes", 0)
        report_data["avg_confidence"] = summary.get("avg_confidence", 0)

    elif campaign_type == "multi_compare":
        options = content if isinstance(content, dict) else {}
        report_data["options"] = options
        report_data["campaign_content"] = "\n".join([f"{k}: {v[:100]}" for k, v in options.items()])
        report_data["vote_distribution"] = summary.get("votes", {})
        report_data["avg_confidence"] = summary.get("avg_confidence", 0)

    # PDF üret
    from src.services.pdf_report import generate_report

    tier = plan_slug  # pro, business, enterprise
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in campaign.name)[:50]
    filename = f"SimuTarget_{safe_name}_{campaign.id}.pdf"

    # Geçici dosyaya yaz
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, filename)

    try:
        generate_report(report_data, tmp_path, tier=tier, lang=lang)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    return FileResponse(
        path=tmp_path,
        filename=filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )