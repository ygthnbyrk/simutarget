"""Tek persona, tek kampanya — ham API yanıtını göster"""
import asyncio, os, sys, json
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import openai
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.agent_mining.models import Persona, SegmentType
from src.agent_mining.prompts import build_prompts, parse_tr_response

async def main():
    engine = create_engine(os.environ["DATABASE_URL"])
    session = sessionmaker(bind=engine)()
    personas = session.query(Persona).filter(Persona.segment == SegmentType.TR).limit(5).all()
    session.close()

    client = openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

    campaign = "LC Waikiki Su Geçirmez Mont — 899 TL. Şişme dolgulu, çıkarılabilir kapüşon. 2 alana %20 indirim."

    for p in personas[:3]:
        system, user = build_prompts(p.to_prompt_dict(), campaign, language="tr")
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.7,
            max_tokens=150,
            response_format={"type": "json_object"},
        )
        
        raw = response.choices[0].message.content
        parsed = parse_tr_response(raw)
        
        print(f"Persona: {p.name} | {p.age}y | {p.income_level} | fiyat_hass={p.price_sensitivity:.2f}")
        print(f"Ham yanıt: {raw}")
        print(f"Parse:     {parsed}")
        print()

asyncio.run(main())
