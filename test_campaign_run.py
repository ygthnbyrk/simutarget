"""Agent Mining - Test Koşusu v3 — zengin kampanya içeriği + DB personalar"""
import asyncio, os, sys
from uuid import uuid4
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.agent_mining.models import Persona, ReferenceCampaign, SegmentType, CampaignStatus
from src.agent_mining.runner import CampaignRunner

TEST_CAMPAIGNS = [
    ReferenceCampaign(
        id=uuid4(), name="Xiaomi Telefon - Orta Segment", category="Teknoloji",
        content="""Xiaomi Redmi Note 13 Pro — Orta Segment Şampiyonu
✓ 6.67" 120Hz AMOLED ekran
✓ 200MP ana kamera, gelişmiş gece modu
✓ 5000mAh batarya, 67W hızlı şarj
Fiyat: 12.999 TL — 12 ay taksit: 1.083 TL/ay
Türkiye garantisi. Ücretsiz kargo.
GSMArena editör notu: 8.5/10""",
        product_name="Xiaomi Redmi Note 13 Pro", price_tl=12999,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=datetime.now(timezone.utc),
    ),
    ReferenceCampaign(
        id=uuid4(), name="LC Waikiki Kışlık Mont", category="Tekstil/Giyim",
        content="""LC Waikiki Kışlık Mont — En Çok Satan Model
✓ Su geçirmez dış kumaş, rüzgar tutmaz
✓ Şişme dolgulu, -10°C'ye kadar sıcak tutar
✓ Çıkarılabilir kapüşon, 5 renk seçeneği
Fiyat: 899 TL (normal 1.299 TL — %30 indirim)
Ücretsiz kargo. 30 gün iade garantisi.
Trendyol'da 4.7/5 puan, 8.400+ değerlendirme.""",
        product_name="LCW Kışlık Mont", price_tl=899,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=datetime.now(timezone.utc),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Udemy Python Kursu", category="Eğitim",
        content="""Python ile Sıfırdan İleri Seviye — Türkiye'nin En Çok Satan Kursu
✓ 52 saat video ders, 12 proje
✓ Bitirme sertifikası (CV'ye eklenebilir)
✓ Ömür boyu erişim, mobil uyumlu
Fiyat: 279 TL (normal 1.499 TL — %81 indirim)
30 gün iade garantisi. 47.000+ öğrenci.""",
        product_name="Udemy Python", price_tl=279,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=datetime.now(timezone.utc),
    ),
]

async def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    db_url = os.environ.get("DATABASE_URL")
    if not api_key or not db_url:
        print("❌ OPENAI_API_KEY veya DATABASE_URL eksik!")
        sys.exit(1)

    session = sessionmaker(bind=create_engine(db_url))()
    print("=" * 55)
    print("  AGENT MINING — TEST KOŞUSU v3")
    print("  (DB personalar + zengin kampanya içeriği)")
    print("=" * 55)

    print("\n📂 DB'den 100 TR persona çekiliyor...")
    personas = session.query(Persona).filter(Persona.segment == SegmentType.TR).limit(100).all()
    print(f"  ✅ {len(personas)} persona yüklendi")
    session.close()

    runner = CampaignRunner(openai_api_key=api_key, model="gpt-4o-mini", max_concurrent=15)
    all_decisions = []
    for campaign in TEST_CAMPAIGNS:
        decisions = await runner.run_campaign(campaign, personas)
        all_decisions.extend(decisions)

    print("\n" + "=" * 55)
    print("  SONUÇ RAPORU")
    print("=" * 55)
    for campaign in TEST_CAMPAIGNS:
        buy_rate = campaign.buy_rate or 0
        print(f"\n📦 {campaign.name}")
        print(f"   Fiyat: {campaign.price_tl:,.0f} TL  |  Satın alma: %{buy_rate*100:.1f}")
        print(f"   ✅ {campaign.buy_count} aldı  /  ❌ {campaign.no_buy_count} almadı")
        camp_dec = [d for d in all_decisions if d.campaign_id == campaign.id]
        for d in [x for x in camp_dec if x.decision.value == "BUY"][:2]:
            print(f"   💚 (güven={d.confidence}): {d.reasoning[:85]}")
        for d in [x for x in camp_dec if x.decision.value == "NO_BUY"][:1]:
            print(f"   ❌ (güven={d.confidence}): {d.reasoning[:85]}")

    total_tokens = runner.stats['total_input_tokens'] + runner.stats['total_output_tokens']
    buy_total = sum(1 for d in all_decisions if d.decision.value == "BUY")
    print(f"\n  Token: {total_tokens:,}  |  Maliyet: ${runner._estimate_cost():.4f}")
    if all_decisions:
        print(f"  Genel satın alma: %{buy_total/len(all_decisions)*100:.1f}")
        print(f"  Ort. güven: {sum(d.confidence for d in all_decisions)/len(all_decisions):.1f}/10")
    print(f"{'=' * 55}\n✅ Test tamamlandı!")

if __name__ == "__main__":
    asyncio.run(main())