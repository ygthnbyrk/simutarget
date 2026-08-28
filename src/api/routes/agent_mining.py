"""
Agent Mining API Routes

POST /api/v1/agent-mining/campaigns          → Yeni kampanya oluştur + çalıştır
GET  /api/v1/agent-mining/campaigns          → Kampanya listesi
GET  /api/v1/agent-mining/campaigns/{id}     → Kampanya detayı + sonuçlar
GET  /api/v1/agent-mining/analytics          → Genel segment analizi
GET  /api/v1/agent-mining/rules              → Kural motoru verisi
"""

import os
import json
import asyncio
import random
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.database.connection import get_db
from src.database.models import User
from src.api.auth import get_current_admin
from src.agent_mining.models import (
    Persona, ReferenceCampaign, AgentDecision,
    SegmentType, CampaignStatus, DecisionType,
)
from src.agent_mining.runner import CampaignRunner

router = APIRouter()

# ===========================================================================
# YARDIMCI
# ===========================================================================

RULES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "agent_mining_rules.json"
)

SEGMENT_MAP = {
    "TR": SegmentType.TR,
    "EU": SegmentType.EU,
    "USA": SegmentType.USA,
    "MENA": SegmentType.MENA,
}

def now_utc():
    return datetime.now(timezone.utc)


# ===========================================================================
# REQUEST / RESPONSE MODELLERİ
# ===========================================================================

class AgentCampaignCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    content: str = Field(..., min_length=10)
    category: str = Field(default="Genel")
    product_name: str = Field(default="")
    price_tl: Optional[float] = None
    price_usd: Optional[float] = None
    segment: str = Field(default="TR", description="TR | EU | USA | MENA")
    persona_count: int = Field(default=100, ge=10, le=500)


class AgentCampaignResponse(BaseModel):
    id: str
    name: str
    category: str
    segment: str
    persona_count: int
    status: str
    buy_rate: Optional[float] = None
    buy_count: int = 0
    no_buy_count: int = 0
    created_at: str


class AgentDecisionDetail(BaseModel):
    persona_name: str
    persona_age: int
    persona_income: str
    persona_city: str
    decision: str
    confidence: int
    reasoning: str


class AgentCampaignDetail(BaseModel):
    id: str
    name: str
    content: str
    category: str
    segment: str
    persona_count: int
    status: str
    buy_rate: Optional[float] = None
    buy_count: int
    no_buy_count: int
    avg_confidence: Optional[float] = None
    created_at: str
    decisions: list[AgentDecisionDetail] = []


# ===========================================================================
# ARKA PLAN GÖREVI — kampanya çalıştırma
# ===========================================================================

async def _run_campaign_task(
    campaign_id: str,
    persona_count: int,
    segment: SegmentType,
    db_url: str,
    openai_key: str,
):
    """FastAPI BackgroundTask olarak çalışır."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    session = sessionmaker(bind=create_engine(db_url))()

    try:
        campaign = session.query(ReferenceCampaign).filter(
            ReferenceCampaign.id == campaign_id
        ).first()

        if not campaign:
            return

        campaign.status = CampaignStatus.RUNNING
        session.commit()

        # Persona çek
        personas = (
            session.query(Persona)
            .filter(Persona.segment == segment)
            .limit(persona_count)
            .all()
        )

        if not personas:
            campaign.status = CampaignStatus.FAILED
            session.commit()
            return

        random.shuffle(personas)

        runner = CampaignRunner(
            openai_api_key=openai_key,
            model="gpt-4o-mini",
            max_concurrent=8,
            session=session,
        )

        await runner.run_campaign(campaign, personas)
        session.merge(campaign)
        campaign.status = CampaignStatus.COMPLETED
        session.commit()

    except Exception as e:
        try:
            campaign = session.query(ReferenceCampaign).filter(
                ReferenceCampaign.id == campaign_id
            ).first()
            if campaign:
                campaign.status = CampaignStatus.FAILED
                session.commit()
        except Exception:
            pass
    finally:
        session.close()


# ===========================================================================
# ENDPOINT'LER
# ===========================================================================

@router.post("/campaigns", response_model=AgentCampaignResponse)
async def create_and_run_campaign(
    data: AgentCampaignCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Yeni Agent Mining kampanyası oluşturur ve arka planda çalıştırır.
    Hemen döner — sonucu GET /campaigns/{id} ile takip et.
    """
    segment = SEGMENT_MAP.get(data.segment.upper())
    if not segment:
        raise HTTPException(400, f"Geçersiz segment: {data.segment}. Geçerli: TR, EU, USA, MENA")

    campaign = ReferenceCampaign(
        id=str(uuid4()),
        name=data.name,
        content=data.content,
        category=data.category,
        product_name=data.product_name or data.name,
        price_tl=data.price_tl,
        price_usd=data.price_usd,
        status=CampaignStatus.PENDING,
        total_personas_run=0,
        buy_count=0,
        no_buy_count=0,
        created_at=now_utc(),
    )
    db.add(campaign)
    db.commit()

    # Arka planda çalıştır
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    db_url = os.environ.get("DATABASE_URL", "")

    background_tasks.add_task(
        _run_campaign_task,
        campaign_id=str(campaign.id),
        persona_count=data.persona_count,
        segment=segment,
        db_url=db_url,
        openai_key=openai_key,
    )

    return AgentCampaignResponse(
        id=str(campaign.id),
        name=campaign.name,
        category=campaign.category,
        segment=data.segment.upper(),
        persona_count=data.persona_count,
        status="pending",
        buy_count=0,
        no_buy_count=0,
        created_at=campaign.created_at.isoformat(),
    )


@router.get("/campaigns", response_model=list[AgentCampaignResponse])
async def list_campaigns(
    segment: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Tüm Agent Mining kampanyalarını listele."""
    query = db.query(ReferenceCampaign).order_by(ReferenceCampaign.created_at.desc())

    if segment:
        seg_enum = SEGMENT_MAP.get(segment.upper())
        if not seg_enum:
            raise HTTPException(400, f"Geçersiz segment: {segment}")

    campaigns = query.limit(limit).all()

    result = []
    for c in campaigns:
        buy_rate = None
        if c.total_personas_run and c.total_personas_run > 0:
            buy_rate = round(c.buy_count / c.total_personas_run * 100, 1)

        result.append(AgentCampaignResponse(
            id=str(c.id),
            name=c.name,
            category=c.category or "Genel",
            segment="TR",  # segment bilgisi campaign'da yok, persona'da var
            persona_count=c.total_personas_run or 0,
            status=c.status.value if hasattr(c.status, "value") else str(c.status),
            buy_rate=buy_rate,
            buy_count=c.buy_count or 0,
            no_buy_count=c.no_buy_count or 0,
            created_at=c.created_at.isoformat(),
        ))

    return result


@router.get("/campaigns/{campaign_id}", response_model=AgentCampaignDetail)
async def get_campaign(
    campaign_id: str,
    limit_decisions: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Kampanya detayı ve karar örneklerini getir."""
    campaign = db.query(ReferenceCampaign).filter(
        ReferenceCampaign.id == campaign_id
    ).first()

    if not campaign:
        raise HTTPException(404, "Kampanya bulunamadı.")

    # Karar örnekleri
    decisions_q = (
        db.query(AgentDecision, Persona)
        .join(Persona, AgentDecision.persona_id == Persona.id)
        .filter(AgentDecision.campaign_id == campaign_id)
        .limit(limit_decisions)
        .all()
    )

    decisions = [
        AgentDecisionDetail(
            persona_name=p.name,
            persona_age=p.age,
            persona_income=p.income_level,
            persona_city=p.city,
            decision=d.decision.value if hasattr(d.decision, "value") else str(d.decision),
            confidence=d.confidence,
            reasoning=d.reasoning or "",
        )
        for d, p in decisions_q
    ]

    # Ortalama güven
    avg_conf = None
    if decisions:
        avg_conf = round(sum(d.confidence for d in decisions) / len(decisions), 1)

    buy_rate = None
    if campaign.total_personas_run and campaign.total_personas_run > 0:
        buy_rate = round(campaign.buy_count / campaign.total_personas_run * 100, 1)

    return AgentCampaignDetail(
        id=str(campaign.id),
        name=campaign.name,
        content=campaign.content,
        category=campaign.category or "Genel",
        segment="TR",
        persona_count=campaign.total_personas_run or 0,
        status=campaign.status.value if hasattr(campaign.status, "value") else str(campaign.status),
        buy_rate=buy_rate,
        buy_count=campaign.buy_count or 0,
        no_buy_count=campaign.no_buy_count or 0,
        avg_confidence=avg_conf,
        created_at=campaign.created_at.isoformat(),
        decisions=decisions,
    )


@router.get("/analytics")
async def get_analytics(
    segment: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Genel segment analizi — toplam kararlar, satın alma oranları,
    kategori bazlı dağılım.
    """
    # Toplam karar sayısı
    total_q = db.query(func.count(AgentDecision.id))
    buy_q = db.query(func.count(AgentDecision.id)).filter(
        AgentDecision.decision == DecisionType.BUY
    )

    if segment:
        seg_enum = SEGMENT_MAP.get(segment.upper())
        if seg_enum:
            total_q = total_q.join(Persona, AgentDecision.persona_id == Persona.id).filter(
                Persona.segment == seg_enum
            )
            buy_q = buy_q.join(Persona, AgentDecision.persona_id == Persona.id).filter(
                Persona.segment == seg_enum
            )

    total = total_q.scalar() or 0
    buy = buy_q.scalar() or 0

    # Segment bazlı özet
    segment_stats = []
    for seg_key, seg_enum in SEGMENT_MAP.items():
        seg_total = (
            db.query(func.count(AgentDecision.id))
            .join(Persona, AgentDecision.persona_id == Persona.id)
            .filter(Persona.segment == seg_enum)
            .scalar() or 0
        )
        seg_buy = (
            db.query(func.count(AgentDecision.id))
            .join(Persona, AgentDecision.persona_id == Persona.id)
            .filter(
                Persona.segment == seg_enum,
                AgentDecision.decision == DecisionType.BUY,
            )
            .scalar() or 0
        )
        if seg_total > 0:
            segment_stats.append({
                "segment": seg_key,
                "total_decisions": seg_total,
                "buy_count": seg_buy,
                "buy_rate": round(seg_buy / seg_total * 100, 1),
            })

    # Top kampanyalar
    top_campaigns = (
        db.query(ReferenceCampaign)
        .filter(ReferenceCampaign.total_personas_run > 0)
        .order_by(ReferenceCampaign.buy_count.desc())
        .limit(10)
        .all()
    )

    top_camp_data = []
    for c in top_campaigns:
        if c.total_personas_run and c.total_personas_run > 0:
            top_camp_data.append({
                "id": str(c.id),
                "name": c.name,
                "category": c.category,
                "buy_rate": round(c.buy_count / c.total_personas_run * 100, 1),
                "total_personas": c.total_personas_run,
            })

    return {
        "total_decisions": total,
        "total_buy": buy,
        "overall_buy_rate": round(buy / total * 100, 1) if total > 0 else 0,
        "segment_breakdown": segment_stats,
        "top_campaigns": top_camp_data,
    }


@router.get("/rules")
async def get_rules(
    current_user: User = Depends(get_current_admin),
):
    """Kural motoru verisi — agent_mining_rules.json"""
    if not os.path.exists(RULES_FILE):
        raise HTTPException(
            404,
            "Kural motoru henüz oluşturulmamış. "
            "Önce `python analyze_decisions.py` çalıştırın."
        )

    with open(RULES_FILE, "r", encoding="utf-8") as f:
        rules = json.load(f)

    return {"rules": rules, "rule_count": len(rules)}


@router.post("/campaigns/{campaign_id}/rerun")
async def rerun_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    persona_count: int = 100,
    segment: str = "TR",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Mevcut bir kampanyayı yeniden çalıştır."""
    campaign = db.query(ReferenceCampaign).filter(
        ReferenceCampaign.id == campaign_id
    ).first()

    if not campaign:
        raise HTTPException(404, "Kampanya bulunamadı.")

    seg_enum = SEGMENT_MAP.get(segment.upper())
    if not seg_enum:
        raise HTTPException(400, f"Geçersiz segment: {segment}")

    # Sıfırla
    campaign.status = CampaignStatus.PENDING
    campaign.total_personas_run = 0
    campaign.buy_count = 0
    campaign.no_buy_count = 0
    db.commit()

    openai_key = os.environ.get("OPENAI_API_KEY", "")
    db_url = os.environ.get("DATABASE_URL", "")

    background_tasks.add_task(
        _run_campaign_task,
        campaign_id=str(campaign.id),
        persona_count=persona_count,
        segment=seg_enum,
        db_url=db_url,
        openai_key=openai_key,
    )

    return {
        "status": "rerun_started",
        "campaign_id": campaign_id,
        "segment": segment,
        "persona_count": persona_count,
    }
