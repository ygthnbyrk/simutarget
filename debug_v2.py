"""Debug v2 - zengin kampanya içeriği + düzeltilmiş fiyat hassasiyeti"""
import asyncio, os, sys
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import openai
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.agent_mining.models import Persona, SegmentType
from src.agent_mining.prompts import build_prompts, parse_tr_response

CAMPAIGNS = {
    "LC Waikiki Mont (899 TL)": """
LC Waikiki Kışlık Mont — En Çok Satan Model
✓ Su geçirmez dış kumaş, rüzgar tutmaz
✓ Şişme dolgulu, -10°C'ye kadar sıcak tutar
✓ Çıkarılabilir kapüşon, 5 renk seçeneği
Fiyat: 899 TL (normal 1.299 TL — %30 indirim)
Kargo ücretsiz. 30 gün iade garantisi.
Trendyol'da 4.7/5 puan, 8.400+ değerlendirme.
""",
    "Xiaomi Telefon (12.999 TL)": """
Xiaomi Redmi Note 13 Pro — Orta Segment Şampiyonu
✓ 6.67" 120Hz AMOLED ekran
✓ 200MP ana kamera, gece modu
✓ 5000mAh batarya, 67W hızlı şarj
Fiyat: 12.999 TL — 12 ay taksit: 1.083 TL/ay
Türkiye garantisi. Ücretsiz kargo.
GSMArena editör notu: 8.5/10
""",
}

async def main():
    engine = create_engine(os.environ["DATABASE_URL"])
    session = sessionmaker(bind=engine)()
    personas = session.query(Persona).filter(Persona.segment == SegmentType.TR).limit(5).all()
    session.close()

    client = openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

    for camp_name, camp_content in CAMPAIGNS.items():
        print(f"\n{'='*60}")
        print(f"KAMPANYA: {camp_name}")
        print(f"{'='*60}")
        
        for p in personas:
            d = p.to_prompt_dict()
            system, user = build_prompts(d, camp_content, language="tr")
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.7, max_tokens=150,
                response_format={"type": "json_object"},
            )
            
            raw = response.choices[0].message.content
            parsed = parse_tr_response(raw)
            
            karar_icon = "✅" if parsed["decision"] == "BUY" else "❌"
            print(f"{karar_icon} {p.name} | {p.age}y | {p.income_level} | hass={p.price_sensitivity:.2f}")
            print(f"   → {parsed['reasoning']}")

asyncio.run(main())
