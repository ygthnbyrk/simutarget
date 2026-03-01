"""Persona API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from ...personas import PersonaFactory, Persona, PersonaConfig

router = APIRouter()

# In-memory storage for MVP (replace with database later)
_personas_store: dict[str, Persona] = {}
_factory = PersonaFactory()


class GenerateRequest(BaseModel):
    """Request to generate personas."""
    count: int = 10
    config: Optional[PersonaConfig] = None


class GenerateResponse(BaseModel):
    """Response with generated personas."""
    count: int
    personas: list[Persona]


@router.post("/generate", response_model=GenerateResponse)
async def generate_personas(request: GenerateRequest):
    """Generate new synthetic personas."""
    
    if request.count < 1 or request.count > 1000:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 1000")
    
    factory = PersonaFactory(config=request.config) if request.config else _factory
    personas = factory.generate_batch(request.count)
    
    # Store generated personas
    for p in personas:
        _personas_store[p.id] = p
    
    return GenerateResponse(count=len(personas), personas=personas)


@router.get("/", response_model=list[Persona])
async def list_personas(
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """List all stored personas."""
    
    all_personas = list(_personas_store.values())
    return all_personas[offset:offset + limit]


@router.get("/{persona_id}", response_model=Persona)
async def get_persona(persona_id: str):
    """Get a specific persona by ID."""
    
    if persona_id not in _personas_store:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    return _personas_store[persona_id]


@router.delete("/{persona_id}")
async def delete_persona(persona_id: str):
    """Delete a persona."""
    
    if persona_id not in _personas_store:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    del _personas_store[persona_id]
    return {"status": "deleted", "persona_id": persona_id}


@router.get("/stats/summary")
async def get_stats():
    """Get persona statistics."""
    
    total = len(_personas_store)
    
    if total == 0:
        return {"total": 0}
    
    personas = list(_personas_store.values())
    
    # Calculate distributions
    age_sum = sum(p.age for p in personas)
    gender_dist = {}
    location_dist = {}
    income_dist = {}
    
    for p in personas:
        gender_dist[p.gender] = gender_dist.get(p.gender, 0) + 1
        location_dist[p.location] = location_dist.get(p.location, 0) + 1
        income_dist[p.income_level] = income_dist.get(p.income_level, 0) + 1
    
    return {
        "total": total,
        "average_age": age_sum / total,
        "gender_distribution": gender_dist,
        "top_locations": dict(sorted(location_dist.items(), key=lambda x: -x[1])[:5]),
        "income_distribution": income_dist,
    }
