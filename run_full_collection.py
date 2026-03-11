"""
Agent Mining - 4 Segment Tam Veri Toplama Pipeline'ı

TR   → 500 persona × 6 kampanya  = 3,000 karar
EU   → 500 persona × 6 kampanya  = 3,000 karar
USA  → 500 persona × 6 kampanya  = 3,000 karar
MENA → 200 persona × 6 kampanya  = 1,200 karar
TOPLAM: ~10,200 karar → DB'ye kaydedilir

Tahmini maliyet: ~$1.50
Tahmini süre:    ~8-12 dakika

Çalıştırma:
  python run_full_collection.py

Sadece belirli segment:
  python run_full_collection.py --segment TR
"""

import asyncio
import argparse
import os
import sys
from uuid import uuid4
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agent_mining.models import (
    Persona, ReferenceCampaign, AgentDecision,
    SegmentType, CampaignStatus, Base
)
from src.agent_mining.runner import CampaignRunner

# ===========================================================================
# KAMPANYA TANIMLAMALARI — 4 SEGMENT
# ===========================================================================

def now():
    return datetime.now(timezone.utc)

TR_CAMPAIGNS = [
    ReferenceCampaign(
        id=uuid4(), name="Xiaomi Telefon - Orta Segment", category="Teknoloji",
        content="""Xiaomi Redmi Note 13 Pro — Orta Segment Şampiyonu
✓ 6.67" 120Hz AMOLED ekran
✓ 200MP ana kamera, gelişmiş gece modu
✓ 5000mAh batarya, 67W hızlı şarj
Fiyat: 12.999 TL — 12 ay taksit: 1.083 TL/ay
Türkiye garantisi. Ücretsiz kargo. GSMArena notu: 8.5/10""",
        product_name="Xiaomi Redmi Note 13 Pro", price_tl=12999,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="LC Waikiki Kışlık Mont", category="Tekstil/Giyim",
        content="""LC Waikiki Kışlık Mont — En Çok Satan Model
✓ Su geçirmez dış kumaş, -10°C'ye kadar sıcak
✓ Şişme dolgulu, çıkarılabilir kapüşon, 5 renk
Fiyat: 899 TL (normal 1.299 TL — %30 indirim)
Ücretsiz kargo. 30 gün iade. Trendyol 4.7/5 — 8.400+ değerlendirme.""",
        product_name="LCW Kışlık Mont", price_tl=899,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Udemy Python Kursu", category="Eğitim",
        content="""Python ile Sıfırdan İleri Seviye — Türkiye'nin En Çok Satan Kursu
✓ 52 saat video, 12 proje, bitirme sertifikası
✓ Ömür boyu erişim, mobil uyumlu
Fiyat: 279 TL (normal 1.499 TL — %81 indirim)
30 gün iade garantisi. 47.000+ öğrenci.""",
        product_name="Udemy Python", price_tl=279,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Arçelik Çamaşır Makinesi", category="Beyaz Eşya",
        content="""Arçelik 8kg A+++ Çamaşır Makinesi — Sessiz & Akıllı
✓ WiFi bağlantı, uygulama kontrolü
✓ Sessize Al teknolojisi, 1400 devir
✓ 10 yıl yedek parça garantisi
Fiyat: 24.999 TL — 36 ay taksit: 694 TL/ay
Ücretsiz kurulum ve kargo.""",
        product_name="Arçelik Çamaşır Makinesi", price_tl=24999,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Ülker Aile Çikolata Paketi", category="FMCG/Gıda",
        content="""Ülker Çikolatalı Aile Paketi — 5 Çeşit, 750g
✓ Sütlü, bitter, fındıklı, karamelli, fıstıklı
✓ Özel ambalaj, hediye seçeneği
Fiyat: 189 TL — Migros'ta geçerli.
Stoklar sınırlı. Üye kartıyla %10 ek indirim.""",
        product_name="Ülker Aile Paketi", price_tl=189,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Trendyol Premium Üyelik", category="Abonelik/Dijital",
        content="""Trendyol Premium — Yıllık Üyelik
✓ Tüm siparişlerde ücretsiz kargo
✓ Erken erişim indirimleri, özel kampanyalar
✓ Öncelikli müşteri hizmetleri
Fiyat: 299 TL/yıl (aylık sadece 24.9 TL)
İlk 30 gün ücretsiz deneyin.""",
        product_name="Trendyol Premium", price_tl=299,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
]

EU_CAMPAIGNS = [
    ReferenceCampaign(
        id=uuid4(), name="Spotify Premium Annual", category="Subscription/Entertainment",
        content="""Spotify Premium — Annual Plan
✓ Ad-free music & podcasts, unlimited skips
✓ Offline downloads, high quality audio (320kbps)
✓ Available on all devices
Price: €99/year (save 2 months vs monthly €10.99)
Cancel anytime. Family plan available.""",
        product_name="Spotify Premium", price_usd=99,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="IKEA Standing Desk", category="Furniture/Home",
        content="""IKEA BEKANT Standing Desk — Work Smarter
✓ Sit/stand electric height adjustment
✓ 160x80cm surface, cable management
✓ 10-year guarantee
Price: €489 — Free delivery over €100
Available in 3 colors. In stock.""",
        product_name="IKEA BEKANT Desk", price_usd=489,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Nike Running Shoes", category="Apparel/Sports",
        content="""Nike Air Zoom Pegasus 41 — Your Daily Trainer
✓ React foam midsole for responsive cushioning
✓ Breathable engineered mesh upper
✓ Available in 8 colorways, sizes 36-48
Price: €130 — Free shipping & 60-day returns
Nike Member price: €110""",
        product_name="Nike Pegasus 41", price_usd=130,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="HelloFresh Meal Kit", category="Food/Subscription",
        content="""HelloFresh — Weekly Meal Kit Delivery
✓ Chef-designed recipes, fresh pre-portioned ingredients
✓ 20+ recipes/week, vegetarian options
✓ No commitment, skip or cancel anytime
Price: from €8.99/serving — First box 60% off
Rated 4.4/5 by 500,000+ customers""",
        product_name="HelloFresh", price_usd=8.99,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Dyson V15 Vacuum Cleaner", category="Home Appliances",
        content="""Dyson V15 Detect — See What You're Cleaning
✓ Laser detects microscopic dust particles
✓ 60 min runtime, HEPA filtration
✓ LCD screen shows real-time particle count
Price: €699 — 2-year warranty
Free next-day delivery. 35-day trial.""",
        product_name="Dyson V15", price_usd=699,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Duolingo Plus Subscription", category="Education/App",
        content="""Duolingo Plus — Learn a Language Faster
✓ Ad-free learning, unlimited hearts
✓ Offline access, progress tracking
✓ 40+ languages available
Price: €6.99/month or €59.99/year
7-day free trial. Cancel anytime.""",
        product_name="Duolingo Plus", price_usd=6.99,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
]

USA_CAMPAIGNS = [
    ReferenceCampaign(
        id=uuid4(), name="Amazon Echo Show 10", category="Smart Home/Tech",
        content="""Amazon Echo Show 10 (3rd Gen) — Smart Display That Moves With You
✓ 10.1" HD screen that rotates to face you
✓ Built-in Alexa, video calling, smart home hub
✓ 13MP camera with auto-framing
Price: $249.99 — Free shipping with Prime
Works with Ring, Philips Hue, and 100,000+ devices""",
        product_name="Echo Show 10", price_usd=249.99,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Netflix Premium Plan", category="Streaming/Entertainment",
        content="""Netflix Premium — Watch Anywhere, Anytime
✓ 4K Ultra HD + HDR streaming
✓ Watch on 4 screens simultaneously
✓ Download on 6 devices for offline viewing
Price: $22.99/month
30-day money back. Cancel anytime.""",
        product_name="Netflix Premium", price_usd=22.99,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Yeti Rambler Tumbler", category="Lifestyle/Accessories",
        content="""YETI Rambler 30 oz Tumbler — Built for the Wild
✓ Double-wall vacuum insulation keeps drinks cold 8hrs
✓ MagSlider lid, dishwasher safe
✓ Stainless steel, dent-resistant
Price: $38.00 — Free shipping over $50
Rated 4.8/5 by 12,000+ buyers. Lifetime warranty.""",
        product_name="YETI Rambler 30oz", price_usd=38,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Peloton App Membership", category="Fitness/Subscription",
        content="""Peloton App — World-Class Fitness Anywhere
✓ 1,000s of classes: cycling, running, yoga, strength
✓ No equipment needed for most classes
✓ Live & on-demand, all fitness levels
Price: $12.99/month (App One) or $24/month (App+)
60-day free trial. Cancel anytime.""",
        product_name="Peloton App", price_usd=12.99,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Levi's 501 Original Jeans", category="Apparel",
        content="""Levi's 501 Original Fit Jeans — The Original Since 1873
✓ Straight leg, button fly, classic 5-pocket
✓ 100% cotton denim, pre-washed
✓ Available in 20+ washes, sizes 28-44
Price: $79.50 — Free shipping & returns
Buy 2, get 20% off.""",
        product_name="Levi's 501", price_usd=79.50,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Instacart+ Membership", category="Grocery/Subscription",
        content="""Instacart+ — Grocery Delivery in Under an Hour
✓ Free delivery on orders $35+
✓ 5% credit back on eligible pickups
✓ Family sharing for up to 5 accounts
Price: $9.99/month or $99/year
14-day free trial. Shop from 1,400+ retailers.""",
        product_name="Instacart+", price_usd=9.99,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
]

MENA_CAMPAIGNS = [
    ReferenceCampaign(
        id=uuid4(), name="iPhone 15 Pro", category="Technology",
        content="""iPhone 15 Pro — Titanium. So strong. So light. So Pro.
✓ A17 Pro chip, 48MP main camera system
✓ Action button, USB-C with USB 3 speeds
✓ All-day battery, up to 23hrs video
Price: AED 4,299 (~$1,170)
Available at Apple Store Dubai Mall & online.
0% installment plan available.""",
        product_name="iPhone 15 Pro", price_usd=1170,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Noon Daily Grocery Subscription", category="Grocery/Subscription",
        content="""Noon Daily — Fresh Groceries Delivered in 2 Hours
✓ 10,000+ products from local & international brands
✓ Temperature-controlled delivery
✓ Express 2-hour delivery slots
Price: AED 29/month for free delivery
First order: 20% off with code NOONFRESH
Available in Dubai, Abu Dhabi, Riyadh.""",
        product_name="Noon Daily", price_usd=8,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Emirates Business Class Upgrade", category="Travel/Luxury",
        content="""Emirates Business Class — Fly Better
✓ Lie-flat private suite, direct aisle access
✓ Gourmet dining, premium bar service
✓ Dubai–London from AED 8,500 (~$2,315)
Book 30 days ahead for best price.
Skywards Miles eligible. Chauffeur-drive included.""",
        product_name="Emirates Business Class", price_usd=2315,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Talabat Pro Subscription", category="Food Delivery/Subscription",
        content="""Talabat Pro — Unlimited Free Delivery
✓ Free delivery from 1,000+ restaurants
✓ Exclusive Pro deals & early access
✓ Priority customer support
Price: AED 19/month or AED 169/year
First month free. Available in UAE, Kuwait, Qatar, Egypt.""",
        product_name="Talabat Pro", price_usd=5,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Adidas Ultraboost 23", category="Sports/Apparel",
        content="""Adidas Ultraboost 23 — Energy Return Like Never Before
✓ BOOST midsole: 20% more energy return
✓ Primeknit+ upper for adaptive fit
✓ Continental rubber outsole
Price: AED 750 (~$204)
Free delivery in UAE. 30-day returns.
Available at Dubai Mall & adidas.com/ae""",
        product_name="Adidas Ultraboost 23", price_usd=204,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
    ReferenceCampaign(
        id=uuid4(), name="Careem Plus Subscription", category="Mobility/Subscription",
        content="""Careem Plus — Everything You Need, One Subscription
✓ Unlimited rides with capped fares
✓ Free food delivery on orders AED 50+
✓ Grocery & pharmacy delivery included
Price: AED 19/month
Cancel anytime. Available in UAE, Egypt, Saudi Arabia.""",
        product_name="Careem Plus", price_usd=5,
        status=CampaignStatus.PENDING, total_personas_run=0, buy_count=0, no_buy_count=0,
        created_at=now(),
    ),
]

ALL_CAMPAIGNS = {
    "TR":   TR_CAMPAIGNS,
    "EU":   EU_CAMPAIGNS,
    "USA":  USA_CAMPAIGNS,
    "MENA": MENA_CAMPAIGNS,
}

# Segment başına kaç persona çalıştırılsın
PERSONA_COUNTS = {
    "TR":   500,
    "EU":   500,
    "USA":  500,
    "MENA": 200,
}

# ===========================================================================
# ANA FONKSİYON
# ===========================================================================

async def run_segment(
    segment: str,
    runner: CampaignRunner,
    session,
    persona_count: int,
):
    """Bir segmentin tüm kampanyalarını çalıştırır ve kararları DB'ye kaydeder."""
    campaigns = ALL_CAMPAIGNS[segment]
    seg_enum = SegmentType(segment)

    print(f"\n{'='*60}")
    print(f"  SEGMENT: {segment} — {persona_count} persona × {len(campaigns)} kampanya")
    print(f"{'='*60}")

    # DB'den persona'ları çek
    personas = (
        session.query(Persona)
        .filter(Persona.segment == seg_enum)
        .limit(persona_count)
        .all()
    )

    if len(personas) == 0:
        print(f"  ⚠️ {segment} segmentinde persona bulunamadı, atlanıyor.")
        return []

    print(f"  ✅ {len(personas)} persona DB'den yüklendi")

    # Kampanyaları DB'ye kaydet
    for camp in campaigns:
        session.merge(camp)
    session.commit()

    # Her kampanyayı çalıştır
    all_decisions = []
    for camp in campaigns:
        decisions = await runner.run_campaign(camp, personas, save_batch_size=200)
        all_decisions.extend(decisions)

        # Karar özetini DB'ye kaydet
        session.merge(camp)
        session.commit()

    return all_decisions


async def main(segments_to_run: list[str]):
    api_key = os.environ.get("OPENAI_API_KEY")
    db_url = os.environ.get("DATABASE_URL")

    if not api_key or not db_url:
        print("❌ OPENAI_API_KEY veya DATABASE_URL eksik!")
        sys.exit(1)

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Tahmini maliyet hesapla
    total_requests = sum(
        PERSONA_COUNTS[s] * len(ALL_CAMPAIGNS[s])
        for s in segments_to_run
    )
    est_cost = total_requests * 500 * (0.15 + 0.60 * 0.2) / 1_000_000

    print("\n" + "=" * 60)
    print("  AGENT MINING — TAM VERİ TOPLAMA")
    print("=" * 60)
    for seg in segments_to_run:
        pc = PERSONA_COUNTS[seg]
        cc = len(ALL_CAMPAIGNS[seg])
        print(f"  {seg:6} → {pc} persona × {cc} kampanya = {pc*cc:,} karar")
    print(f"  {'TOPLAM':6} → {total_requests:,} istek")
    print(f"  Tahmini maliyet: ${est_cost:.2f}")
    print("=" * 60)

    confirm = input("\nBaşlamak istiyor musun? [y/N]: ")
    if confirm.lower() != "y":
        print("İptal edildi.")
        session.close()
        return

    runner = CampaignRunner(
        openai_api_key=api_key,
        model="gpt-4o-mini",
        max_concurrent=8,
        session=session,
    )

    import time
    start = time.time()
    grand_total_decisions = 0

    for segment in segments_to_run:
        decisions = await run_segment(
            segment, runner, session, PERSONA_COUNTS[segment]
        )
        grand_total_decisions += len(decisions)

    elapsed = time.time() - start
    session.close()

    # Final rapor
    print("\n" + "=" * 60)
    print("  🎉 TAM VERİ TOPLAMA TAMAMLANDI")
    print("=" * 60)
    print(f"  Toplam karar: {grand_total_decisions:,}")
    print(f"  Başarılı istek: {runner.stats['successful']:,}")
    print(f"  Başarısız: {runner.stats['failed']}")
    total_tokens = runner.stats['total_input_tokens'] + runner.stats['total_output_tokens']
    print(f"  Toplam token: {total_tokens:,}")
    print(f"  Gerçek maliyet: ${runner._estimate_cost():.4f}")
    print(f"  Toplam süre: {elapsed:.0f}s ({elapsed/60:.1f} dakika)")
    print("=" * 60)
    print("\n✅ Tüm kararlar DB'ye kaydedildi.")
    print("   Sonraki adım: Kural motoru ve fine-tune için veri hazır!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent Mining - Tam Veri Toplama")
    parser.add_argument(
        "--segment",
        choices=["TR", "EU", "USA", "MENA"],
        help="Sadece belirli bir segment çalıştır (varsayılan: hepsi)"
    )
    args = parser.parse_args()

    segments = [args.segment] if args.segment else ["TR", "EU", "USA", "MENA"]
    asyncio.run(main(segments))
