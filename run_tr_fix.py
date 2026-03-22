"""
TR Kampanya Düzeltmesi — Gelir segmentine göre hedefli kampanyalar

Sorun: TR'de %15.9 satın alma — çünkü kampanyalar gelir dağılımına uymuyordu
Çözüm: 3 gelir katmanı × ayrı kampanyalar

Düşük/Orta-Düşük → BİM, A101, Şok ürünleri (50-500 TL)
Orta/Orta-Yüksek  → Mango, Zara, orta segment (500-5000 TL)
Yüksek            → Apple, Dyson, lüks (5000 TL+)
"""

import asyncio, os, sys, random
from uuid import uuid4
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.agent_mining.models import Persona, ReferenceCampaign, SegmentType, CampaignStatus
from src.agent_mining.runner import CampaignRunner

def now(): return datetime.now(timezone.utc)
def camp(name, category, content, product_name, price_tl):
    return ReferenceCampaign(
        id=uuid4(), name=name, category=category, content=content,
        product_name=product_name, price_tl=price_tl,
        status=CampaignStatus.PENDING, total_personas_run=0,
        buy_count=0, no_buy_count=0, created_at=now(),
    )

# ===========================================================================
# DÜŞÜK / ORTA-DÜŞÜK GELİR (50-500 TL)
# ===========================================================================
LOW_INCOME_CAMPAIGNS = [
    camp("BİM Haftalık Market Fırsatları", "FMCG/Market", """
BİM Bu Hafta — Fiyatlar Yarı Yarıya!
✓ Zeytinyağı 1L: 89 TL (normal 149 TL)
✓ Tavuk Göğsü 1kg: 119 TL
✓ Deterjan 5kg: 79 TL
✓ Peynir 500g: 49 TL
Sadece bu hafta geçerli. En yakın BİM'de.""",
        "BİM Market", price_tl=89),

    camp("A101 Tekstil Kampanyası", "Tekstil/Uygun", """
A101'de Giyim Festivali — 3 Al 2 Öde!
✓ Erkek/Kadın sweatshirt: 149 TL
✓ Çocuk mont: 199 TL
✓ Spor ayakkabı: 249 TL
3 ürün al, en ucuzunu hediye.
Stoklar sınırlı.""",
        "A101 Tekstil", price_tl=149),

    camp("Şok Market Elektronik", "Elektronik/Uygun", """
Şok'ta Teknoloji Fırsatı
✓ Bluetooth kulaklık: 199 TL
✓ Şarj aleti 20W: 89 TL
✓ USB kablo seti: 49 TL
✓ Powerbank 10.000mAh: 299 TL
Kampanya süresi sınırlı.""",
        "Şok Elektronik", price_tl=199),

    camp("Migros Para Puan Kampanyası", "Market/Uygun", """
Migros Money Card — Her Alışverişte Para Kazan
✓ 500 TL alışverişe 50 TL para puan
✓ Kişisel bakım %30 indirim
✓ Meyve-sebze tazelik garantisi
Kart üyelerine özel. Tüm Migros'larda.""",
        "Migros Money", price_tl=500),

    camp("Netflix Temel Plan", "Streaming/Uygun", """
Netflix Temel — Uygun Fiyata Eğlence
✓ Binlerce dizi ve film
✓ Mobil ve tablet uyumlu
✓ Reklamsız izleme
Fiyat: 79.99 TL/ay
İlk ay ücretsiz. İstediğinde iptal et.""",
        "Netflix Temel", price_tl=79),

    camp("Yemeksepeti Gold Üyelik", "Yemek/Abonelik", """
Yemeksepeti Gold — Ücretsiz Teslimat Her Zaman
✓ Tüm restoranlarda ücretsiz teslimat
✓ Aylık 100 TL indirim kuponu
✓ Öncelikli destek
Fiyat: 59.99 TL/ay
İlk 30 gün ücretsiz.""",
        "Yemeksepeti Gold", price_tl=59),
]

# ===========================================================================
# ORTA / ORTA-YÜKSEK GELİR (500-8000 TL)
# ===========================================================================
MID_INCOME_CAMPAIGNS = [
    camp("Zara Sonbahar/Kış Koleksiyonu", "Moda/Orta", """
Zara Yeni Sezon — Şimdi Online'da
✓ Kadın blazer ceket: 1.299 TL
✓ Erkek slim fit pantolon: 899 TL
✓ Deri çanta: 1.899 TL
Ücretsiz kargo 500 TL üzeri.
30 gün ücretsiz iade.""",
        "Zara Koleksiyon", price_tl=1299),

    camp("Samsung Galaxy A55 5G", "Teknoloji/Orta", """
Samsung Galaxy A55 5G — Akıllı Seçim
✓ 6.6" Super AMOLED, 120Hz
✓ 50MP üçlü kamera sistemi
✓ 5.000mAh batarya, 5G
Fiyat: 19.999 TL — 12 ay taksit: 1.666 TL/ay
Samsung Türkiye garantisi. Ücretsiz kargo.""",
        "Samsung Galaxy A55", price_tl=19999),

    camp("Karcher Yüksek Basınçlı Yıkama", "Ev/Bahçe", """
Kärcher K4 — Evinizi & Arabanızı Pırıl Pırıl Yapın
✓ 130 bar basınç, 420L/saat
✓ Sessiz motor teknolojisi
✓ 8m hortum, aksesuarlar dahil
Fiyat: 4.299 TL (normal 5.999 TL — %28 indirim)
3 yıl garanti. Ücretsiz kargo.""",
        "Kärcher K4", price_tl=4299),

    camp("Mango Premium Üyelik + Alışveriş", "Moda/Orta", """
Mango — Yeni Sezon %30 İndirim
✓ Kadın/Erkek günlük & ofis giyim
✓ Trençkot: 2.499 TL → 1.749 TL
✓ Blazer takım: 3.299 TL → 2.309 TL
Üye ol, ek %10 kupon kazan.
Kargo ücretsiz, 30 gün iade.""",
        "Mango Yeni Sezon", price_tl=1749),

    camp("Spotify Premium 6 Ay", "Müzik/Abonelik", """
Spotify Premium — 6 Ay Öde, 8 Ay Kullan
✓ Reklamsız müzik, offline dinleme
✓ Yüksek kalite ses, tüm cihazlarda
Fiyat: 6 ay = 539 TL (aylık sadece 89 TL)
Hemen başla, istediğinde iptal et.""",
        "Spotify 6 Ay", price_tl=539),

    camp("Tefal Fritöz & Izgara Seti", "Mutfak/Orta", """
Tefal ActiFry Genius XL — Airfryer & Izgara Kombini
✓ 1.7kg kapasiteli airfryer
✓ Yapışmaz grill tavası dahil
✓ 8 program, otomatik karıştırıcı
Fiyat: 3.499 TL — 6 ay taksit mevcut
2 yıl garanti. Bugün sipariş ver.""",
        "Tefal ActiFry", price_tl=3499),
]

# ===========================================================================
# YÜKSEK GELİR (8000 TL+)
# ===========================================================================
HIGH_INCOME_CAMPAIGNS = [
    camp("Apple iPhone 15 Pro", "Teknoloji/Premium", """
Apple iPhone 15 Pro — Titanium
✓ A17 Pro çip, 48MP ProRAW kamera
✓ Action Button, USB-C
✓ Tüm gün pil ömrü
Fiyat: 64.999 TL — 24 ay taksit: 2.708 TL/ay
Apple Türkiye garantisi. Ücretsiz teslimat.
Trade-in ile 15.000 TL'ye varan değer.""",
        "iPhone 15 Pro", price_tl=64999),

    camp("Dyson Airwrap Complete", "Güzellik/Premium", """
Dyson Airwrap Complete — Saçını Hasar Vermeden Şekillendir
✓ Coanda etkisi, ısı kontrolü
✓ 6 ataşman, tüm saç tiplerine uygun
✓ 2 yıl garanti
Fiyat: 17.999 TL
Ücretsiz kargo. Orijinal kutu, Türkiye garantili.""",
        "Dyson Airwrap", price_tl=17999),

    camp("Garmin Fenix 7 Pro Smartwatch", "Teknoloji/Premium", """
Garmin Fenix 7 Pro — Üst Segment GPS Saat
✓ Solar şarj, 22 gün pil
✓ Topografik harita, kalp ritmi, oksijen
✓ Askeri dayanıklılık standardı
Fiyat: 24.999 TL
Garmin Türkiye garantisi. Ücretsiz kargo.""",
        "Garmin Fenix 7 Pro", price_tl=24999),

    camp("Breville Espresso Makinesi", "Mutfak/Premium", """
Breville Barista Express — Ev Barista Deneyimi
✓ Dahili conical burr öğütücü
✓ 15 bar İtalyan pompası
✓ PID sıcaklık kontrolü
Fiyat: 22.999 TL (normal 27.999 TL)
2 yıl garanti. Ücretsiz kurulum eğitimi.""",
        "Breville Barista Express", price_tl=22999),

    camp("Turkish Airlines Business Class", "Seyahat/Lüks", """
Türk Hava Yolları Business Class — İstanbul–Dubai
✓ Yatay yatar koltuk, özel suite
✓ Chef tarafından hazırlanmış menü
✓ Lounge erişimi, şoförlü transfer
Fiyat: 42.500 TL (tek yön)
Miles&Smiles puan kazanın. Erken rezervasyon indirimi.""",
        "THY Business Class", price_tl=42500),

    camp("Nespresso Vertuo Next Premium", "Mutfak/Premium", """
Nespresso Vertuo Next — Her Gün Mükemmel Kahve
✓ Barcode teknolojisi, 5 bardak boyutu
✓ 11 saniyede ısınma, sessiz motor
✓ 12 kapsül hediye
Fiyat: 4.999 TL (normal 6.999 TL)
+2.000 TL'ye varan Nespresso Club avantajı.""",
        "Nespresso Vertuo", price_tl=4999),
]

# ===========================================================================
# GELİR SEGMENTİ FİLTRESİ
# ===========================================================================
LOW_INCOME_LEVELS = ["Düşük", "Orta-Düşük"]
MID_INCOME_LEVELS = ["Orta", "Orta-Yüksek"]
HIGH_INCOME_LEVELS = ["Yüksek"]

PERSONA_PER_CAMP = 120  # Her kampanya farklı 120 persona

async def run_income_segment(name, campaigns, income_levels, session, runner):
    print(f"\n{'='*60}")
    print(f"  GELİR GRUBU: {name} — {len(campaigns)} kampanya × {PERSONA_PER_CAMP} persona")
    print(f"{'='*60}")

    needed = PERSONA_PER_CAMP * len(campaigns)
    personas = (
        session.query(Persona)
        .filter(
            Persona.segment == SegmentType.TR,
            Persona.income_level.in_(income_levels)
        )
        .limit(needed)
        .all()
    )

    if len(personas) < PERSONA_PER_CAMP:
        print(f"  ⚠️ Yeterli persona yok ({len(personas)}), atlanıyor.")
        return

    random.shuffle(personas)
    print(f"  ✅ {len(personas)} persona yüklendi")

    for i, campaign in enumerate(campaigns):
        slice_start = (i * PERSONA_PER_CAMP) % len(personas)
        camp_personas = personas[slice_start:slice_start + PERSONA_PER_CAMP]
        if len(camp_personas) < PERSONA_PER_CAMP:
            camp_personas += personas[:PERSONA_PER_CAMP - len(camp_personas)]

        session.merge(campaign)
        session.commit()

        print(f"  [{i+1}/{len(campaigns)}] '{campaign.name}'")
        decisions = await runner.run_campaign(campaign, camp_personas)
        session.merge(campaign)
        session.commit()

        buy = sum(1 for d in decisions if d.decision.value == "BUY")
        rate = buy / len(decisions) * 100 if decisions else 0
        print(f"        → %{rate:.1f} satın alma ({buy}/{len(decisions)})")

async def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    db_url = os.environ.get("DATABASE_URL")

    total = (len(LOW_INCOME_CAMPAIGNS) + len(MID_INCOME_CAMPAIGNS) + len(HIGH_INCOME_CAMPAIGNS)) * PERSONA_PER_CAMP
    print(f"\n{'='*60}")
    print(f"  TR KAMPANYA DÜZELTMESİ — GELİR SEGMENTLI")
    print(f"{'='*60}")
    print(f"  Düşük/Orta-Düşük  → {len(LOW_INCOME_CAMPAIGNS)} kampanya × {PERSONA_PER_CAMP} = {len(LOW_INCOME_CAMPAIGNS)*PERSONA_PER_CAMP} karar")
    print(f"  Orta/Orta-Yüksek  → {len(MID_INCOME_CAMPAIGNS)} kampanya × {PERSONA_PER_CAMP} = {len(MID_INCOME_CAMPAIGNS)*PERSONA_PER_CAMP} karar")
    print(f"  Yüksek            → {len(HIGH_INCOME_CAMPAIGNS)} kampanya × {PERSONA_PER_CAMP} = {len(HIGH_INCOME_CAMPAIGNS)*PERSONA_PER_CAMP} karar")
    print(f"  TOPLAM            → {total} karar")
    print(f"  Tahmini maliyet   → ${total * 0.0001:.2f}")
    print(f"{'='*60}")

    confirm = input("\nBaşlamak istiyor musun? [y/N]: ")
    if confirm.lower() != "y":
        print("İptal.")
        return

    session = sessionmaker(bind=create_engine(db_url))()
    runner = CampaignRunner(openai_api_key=api_key, model="gpt-4o-mini",
                            max_concurrent=8, session=session)

    import time; start = time.time()

    await run_income_segment("Düşük / Orta-Düşük", LOW_INCOME_CAMPAIGNS,
                             LOW_INCOME_LEVELS, session, runner)
    await run_income_segment("Orta / Orta-Yüksek", MID_INCOME_CAMPAIGNS,
                             MID_INCOME_LEVELS, session, runner)
    await run_income_segment("Yüksek", HIGH_INCOME_CAMPAIGNS,
                             HIGH_INCOME_LEVELS, session, runner)

    elapsed = time.time() - start
    session.close()

    print(f"\n{'='*60}")
    print(f"  ✅ TAMAMLANDI")
    print(f"  Toplam karar:   {runner.stats['successful']:,}")
    print(f"  Gerçek maliyet: ${runner._estimate_cost():.4f}")
    print(f"  Süre:           {elapsed:.0f}s ({elapsed/60:.1f} dk)")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())
