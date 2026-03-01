"""Tests for persona generation."""

import pytest
from src.personas import PersonaFactory, Persona, PersonaConfig


class TestPersonaFactory:
    """Tests for PersonaFactory."""
    
    def test_generate_one_persona(self):
        """Test generating a single persona."""
        factory = PersonaFactory()
        persona = factory.generate_one()
        
        assert isinstance(persona, Persona)
        assert persona.id is not None
        assert persona.name is not None
        assert 18 <= persona.age <= 80
    
    def test_generate_batch(self):
        """Test generating multiple personas."""
        factory = PersonaFactory()
        personas = factory.generate_batch(10)
        
        assert len(personas) == 10
        assert all(isinstance(p, Persona) for p in personas)
        
        # Check all IDs are unique
        ids = [p.id for p in personas]
        assert len(ids) == len(set(ids))
    
    def test_persona_has_required_fields(self):
        """Test that persona has all required fields."""
        factory = PersonaFactory()
        persona = factory.generate_one()
        
        # Demographics
        assert persona.gender is not None
        assert persona.location is not None
        assert persona.income_level is not None
        assert persona.education is not None
        assert persona.occupation is not None
        assert persona.marital_status is not None
        
        # Personality
        assert persona.personality is not None
        assert 0 <= persona.personality.openness <= 1
        assert 0 <= persona.personality.conscientiousness <= 1
        assert 0 <= persona.personality.extraversion <= 1
        assert 0 <= persona.personality.agreeableness <= 1
        assert 0 <= persona.personality.neuroticism <= 1
        
        # Preferences
        assert isinstance(persona.values, list)
        assert isinstance(persona.interests, list)
        assert 0 <= persona.price_sensitivity <= 1
    
    def test_custom_config(self):
        """Test persona generation with custom config."""
        config = PersonaConfig(
            min_age=25,
            max_age=40,
            location_weights={"İstanbul": 1.0},  # Only Istanbul
        )
        factory = PersonaFactory(config=config)
        
        personas = factory.generate_batch(20)
        
        for p in personas:
            assert 25 <= p.age <= 40
            assert p.location == "İstanbul"


class TestPersona:
    """Tests for Persona model."""
    
    def test_persona_serialization(self):
        """Test persona can be serialized to dict."""
        factory = PersonaFactory()
        persona = factory.generate_one()
        
        data = persona.model_dump()
        
        assert isinstance(data, dict)
        assert "id" in data
        assert "name" in data
        assert "personality" in data
    
    def test_persona_json(self):
        """Test persona can be serialized to JSON."""
        factory = PersonaFactory()
        persona = factory.generate_one()
        
        json_str = persona.model_dump_json()
        
        assert isinstance(json_str, str)
        assert persona.id in json_str
