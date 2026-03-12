"""
Agent Mining - Bölge & Ülke Bazlı Veri Toplama Pipeline'ı

Strateji:
  - Her kampanya FARKLI 100 persona ile çalışır (overlap yok)
  - Her bölgeye özgü kampanyalar (yerel marka, dil, fiyat)
  - Günlük 10K limit içinde ~6,000-8,000 karar

Kullanım:
  python run_full_collection.py              # Tüm bölgeler
  python run_full_collection.py --region TR  # Sadece Türkiye
  python run_full_collection.py --list       # Tüm bölgeleri listele
"""

import asyncio
import argparse
import os
import sys
import random
from uuid import uuid4
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agent_mining.models import (
    Persona, ReferenceCampaign, SegmentType,
    CampaignStatus
)
from src.agent_mining.runner import CampaignRunner


def now():
    return datetime.now(timezone.utc)


def camp(name, category, content, product_name, price_tl=None, price_usd=None):
    return ReferenceCampaign(
        id=uuid4(), name=name, category=category, content=content,
        product_name=product_name, price_tl=price_tl, price_usd=price_usd,
        status=CampaignStatus.PENDING, total_personas_run=0,
        buy_count=0, no_buy_count=0, created_at=now(),
    )


# ===========================================================================
# KAMPANYA KÜTÜPHANESİ
# ===========================================================================

CAMPAIGNS = {

    # -----------------------------------------------------------------------
    "TR": [
        camp("Xiaomi Redmi Note 13 Pro", "Teknoloji", """
Xiaomi Redmi Note 13 Pro — Orta Segment Şampiyonu
✓ 6.67" 120Hz AMOLED ekran, 200MP kamera
✓ 5000mAh batarya, 67W hızlı şarj
Fiyat: 12.999 TL — 12 ay taksit: 1.083 TL/ay
Türkiye garantisi. Ücretsiz kargo. GSMArena notu: 8.5/10""",
            "Xiaomi Redmi Note 13 Pro", price_tl=12999),

        camp("LC Waikiki Kışlık Mont", "Tekstil", """
LC Waikiki Kışlık Mont — En Çok Satan Model
✓ Su geçirmez, -10°C'ye kadar sıcak, çıkarılabilir kapüşon
✓ 5 renk seçeneği
Fiyat: 899 TL (normal 1.299 TL — %30 indirim)
Trendyol 4.7/5 — 8.400+ değerlendirme. 30 gün iade.""",
            "LCW Kışlık Mont", price_tl=899),

        camp("Udemy Python Kursu", "Eğitim", """
Python ile Sıfırdan İleri Seviye — Türkiye'nin En Çok Satan Kursu
✓ 52 saat video, 12 proje, bitirme sertifikası
✓ Ömür boyu erişim, mobil uyumlu
Fiyat: 279 TL (normal 1.499 TL — %81 indirim)
47.000+ öğrenci. 30 gün iade garantisi.""",
            "Udemy Python", price_tl=279),

        camp("Arçelik Çamaşır Makinesi", "Beyaz Eşya", """
Arçelik 8kg A+++ Çamaşır Makinesi — Sessiz & Akıllı
✓ WiFi bağlantı, uygulama kontrolü, 1400 devir
✓ 10 yıl yedek parça garantisi
Fiyat: 24.999 TL — 36 ay taksit: 694 TL/ay
Ücretsiz kurulum ve kargo.""",
            "Arçelik Çamaşır Makinesi", price_tl=24999),

        camp("Ülker Çikolata Aile Paketi", "FMCG/Gıda", """
Ülker Çikolatalı Aile Paketi — 5 Çeşit, 750g
✓ Sütlü, bitter, fındıklı, karamelli, fıstıklı
✓ Özel ambalaj, hediye seçeneği
Fiyat: 189 TL — Migros'ta geçerli.
Üye kartıyla %10 ek indirim.""",
            "Ülker Aile Paketi", price_tl=189),

        camp("Trendyol Premium Üyelik", "Abonelik", """
Trendyol Premium — Yıllık Üyelik
✓ Tüm siparişlerde ücretsiz kargo
✓ Erken erişim indirimleri, öncelikli destek
Fiyat: 299 TL/yıl (aylık sadece 24.9 TL)
İlk 30 gün ücretsiz deneyin.""",
            "Trendyol Premium", price_tl=299),

        camp("Philips Airfryer XXL", "Mutfak/Ev", """
Philips Airfryer XXL — 1.2kg Kapasite, %90 Az Yağ
✓ Rapid Air teknolojisi, 7 ön ayar
✓ Dijital dokunmatik panel, dishwasher-safe
Fiyat: 4.999 TL (normal 6.999 TL)
2 yıl garanti. Ücretsiz kargo.""",
            "Philips Airfryer XXL", price_tl=4999),

        camp("Hepsiburada Premium Üyelik", "Abonelik", """
Hepsiburada Premium — Sınırsız Ücretsiz Kargo
✓ 5 dakikada kargo seçeneği, öncelikli müşteri hizmetleri
✓ Özel indirimler ve erken erişim
Fiyat: 249 TL/yıl
İlk ay ücretsiz. 10 milyon+ ürün.""",
            "Hepsiburada Premium", price_tl=249),
    ],

    # -----------------------------------------------------------------------
    "EU_DE": [  # Almanya
        camp("Spotify Premium Jahresabo", "Musik/Abo", """
Spotify Premium — Jahresabo
✓ Werbefreie Musik, offline Downloads, 320kbps
✓ Alle Geräte, keine Bindung
Preis: 99€/Jahr (spare 2 Monate vs. 9,99€/Monat)
Jetzt 3 Monate gratis testen.""",
            "Spotify Premium", price_usd=99),

        camp("IKEA BEKANT Stehschreibtisch", "Möbel", """
IKEA BEKANT Stehschreibtisch — Elektrisch höhenverstellbar
✓ 160x80cm, Kabelmanagement, 10 Jahre Garantie
✓ 3 Farben, leise Motoren
Preis: 489€ — Kostenlose Lieferung ab 100€
Auf Lager. Direkt ab IKEA.de.""",
            "IKEA BEKANT", price_usd=489),

        camp("Nike Air Zoom Pegasus 41", "Sport", """
Nike Air Zoom Pegasus 41 — Dein täglicher Trainingsschuh
✓ React Schaum, atmungsaktives Mesh-Obermaterial
✓ 8 Farbvarianten, Gr. 36-48
Preis: 130€ — Kostenloser Versand & 60 Tage Rückgabe
Nike Member Preis: 110€""",
            "Nike Pegasus 41", price_usd=130),

        camp("HelloFresh Kochbox", "Essen/Abo", """
HelloFresh — Wöchentliche Kochbox
✓ Frische Zutaten, Chefrezepte, 20+ Gerichte/Woche
✓ Vegetarische Optionen, kein Vertrag
Preis: ab 8,99€/Portion — Erste Box 60% Rabatt
4.4/5 von 500.000+ Kunden""",
            "HelloFresh", price_usd=8.99),

        camp("Dyson V15 Detect Staubsauger", "Haushaltsgeräte", """
Dyson V15 Detect — Sehen Sie was Sie saugen
✓ Laser erkennt mikroskopischen Staub
✓ 60 Min Laufzeit, HEPA-Filter, LCD-Display
Preis: 699€ — 2 Jahre Garantie, 35-Tage-Test
Kostenlose Lieferung am nächsten Tag.""",
            "Dyson V15", price_usd=699),

        camp("Duolingo Plus Abo", "Bildung", """
Duolingo Plus — Schneller eine Sprache lernen
✓ Werbefrei, unbegrenzte Herzen, Offline-Zugriff
✓ 40+ Sprachen, Fortschritts-Tracking
Preis: 6,99€/Monat oder 59,99€/Jahr
7 Tage gratis. Jederzeit kündbar.""",
            "Duolingo Plus", price_usd=6.99),
    ],

    # -----------------------------------------------------------------------
    "EU_FR": [  # Fransa
        camp("Fnac Adhérent Premium", "Abonnement", """
Carte Fnac Adhérent — Avantages toute l'année
✓ -5% sur tous les achats, invitations exclusives
✓ Remboursement sur achats culturels
Prix: 49€/an
Valable en magasin et sur fnac.com""",
            "Fnac Adhérent", price_usd=49),

        camp("Free Mobile Forfait 5G", "Télécom", """
Free Mobile — Forfait 5G Illimité
✓ Appels/SMS illimités, 300Go 5G
✓ Appels illimités vers 110 pays
Prix: 19,99€/mois (sans engagement)
Carte SIM gratuite. Livraison en 48h.""",
            "Free Mobile 5G", price_usd=19.99),

        camp("Décathlon Vélo Électrique", "Sport/Mobilité", """
Décathlon B'TWIN E-BIKE — Vélo Électrique Urbain
✓ Moteur 250W, autonomie 100km
✓ Frein hydraulique, éclairage intégré
Prix: 1.299€ — Financement 0% sur 24 mois
Click & Collect disponible.""",
            "Décathlon E-Bike", price_usd=1299),

        camp("Boulanger TV OLED 55\"", "Électronique", """
LG OLED55C4 — Télé OLED 55 pouces
✓ Processeur α9, Dolby Vision IQ, 120Hz
✓ Compatible PS5/Xbox Series X
Prix: 1.299€ (au lieu de 1.799€) — Économisez 500€
Livraison offerte + installation à domicile.""",
            "LG OLED 55", price_usd=1299),

        camp("BlaBlaCar Premium", "Mobilité/Abo", """
BlaBlaCar Premium — Voyagez mieux
✓ Réservation prioritaire, badge de confiance
✓ Annulations flexibles, support prioritaire
Prix: 2,99€/mois ou 29,99€/an
Essai gratuit 30 jours.""",
            "BlaBlaCar Premium", price_usd=2.99),

        camp("Canal+ Abonnement", "Streaming", """
Canal+ — Le meilleur du cinéma et sport
✓ Films en avant-première, Ligue 1, Champions League
✓ Streaming illimité, 4K disponible
Prix: 26,99€/mois (engagement 12 mois)
Premier mois offert. Résiliable en ligne.""",
            "Canal+", price_usd=26.99),
    ],

    # -----------------------------------------------------------------------
    "EU_UK": [  # Birleşik Krallık
        camp("Amazon Prime Annual", "Subscription", """
Amazon Prime — Annual Membership
✓ Free next-day delivery, Prime Video, Prime Music
✓ Amazon Photos unlimited storage, Prime Gaming
Price: £95/year (£8.99/month)
30-day free trial. Cancel anytime.""",
            "Amazon Prime", price_usd=95),

        camp("Marks & Spencer Winter Coat", "Fashion", """
M&S Padded Winter Coat — Warmth Without the Bulk
✓ Recycled polyester fill, water-repellent
✓ Hidden zip pockets, detachable hood
✓ Sizes 6-24, 4 colours
Price: £89 (was £129) — Free delivery on £60+
Free returns. M&S Sparks points.""",
            "M&S Winter Coat", price_usd=89),

        camp("Octopus Energy Switch", "Utilities", """
Octopus Energy — Switch & Save
✓ 100% renewable electricity
✓ Agile tariff: pay less when grid is green
✓ Smart meter included free
Switch in 15 minutes. No exit fees.
Rated #1 energy supplier by Which? 2024""",
            "Octopus Energy", price_usd=0),

        camp("Deliveroo Plus Membership", "Food/Subscription", """
Deliveroo Plus — Unlimited Free Delivery
✓ No delivery fees on orders £25+
✓ 50+ exclusive restaurant deals
Price: £3.99/month or £35/year
First month free. 1,000+ restaurants.""",
            "Deliveroo Plus", price_usd=3.99),

        camp("Gymshark Lifting Set", "Sportswear", """
Gymshark Vital Seamless Set — Training Redefined
✓ Seamless knit, 4-way stretch
✓ Leggings + sports bra, 8 colourways
Price: £65 (leggings £40 + bra £25)
Free delivery over £45. 90-day returns.
4.7/5 from 18,000+ reviews""",
            "Gymshark Set", price_usd=65),

        camp("Headspace App Annual", "Wellness/App", """
Headspace — Meditation & Sleep Made Simple
✓ 500+ guided meditations, sleep sounds
✓ Stress & anxiety courses, focus music
Price: £49.99/year (£4.17/month)
14-day free trial. No commitment.
Used by 70M+ people worldwide""",
            "Headspace", price_usd=49.99),
    ],

    # -----------------------------------------------------------------------
    "USA": [
        camp("Amazon Echo Show 10", "Smart Home", """
Amazon Echo Show 10 (3rd Gen) — Smart Display That Moves With You
✓ 10.1" HD screen, auto-rotating, built-in Alexa
✓ 13MP camera, video calling, smart home hub
Price: $249.99 — Free shipping with Prime
Works with 100,000+ smart home devices""",
            "Echo Show 10", price_usd=249.99),

        camp("Netflix Premium Plan", "Streaming", """
Netflix Premium — Watch Anywhere, Anytime
✓ 4K Ultra HD + HDR, 4 screens simultaneously
✓ Download on 6 devices for offline viewing
Price: $22.99/month
Cancel anytime. 30-day money back.""",
            "Netflix Premium", price_usd=22.99),

        camp("YETI Rambler 30oz Tumbler", "Lifestyle", """
YETI Rambler 30 oz — Built for the Wild
✓ Double-wall vacuum insulation (cold 8hrs)
✓ MagSlider lid, dishwasher safe, stainless steel
Price: $38.00 — Free shipping over $50
4.8/5 from 12,000+ buyers. Lifetime warranty.""",
            "YETI Rambler", price_usd=38),

        camp("Peloton App Membership", "Fitness", """
Peloton App — World-Class Fitness Anywhere
✓ 1,000s of classes: cycling, yoga, strength
✓ No equipment needed, live & on-demand
Price: $12.99/month or $24/month (App+)
60-day free trial. Cancel anytime.""",
            "Peloton App", price_usd=12.99),

        camp("Levi's 501 Original Jeans", "Apparel", """
Levi's 501 Original Fit — The Original Since 1873
✓ Straight leg, button fly, 100% cotton
✓ 20+ washes, sizes 28-44
Price: $79.50 — Free shipping & returns
Buy 2, save 20%""",
            "Levi's 501", price_usd=79.50),

        camp("Instacart+ Annual", "Grocery/Sub", """
Instacart+ — Grocery Delivery in Under an Hour
✓ Free delivery on orders $35+
✓ 5% credit back, family sharing (5 accounts)
Price: $99/year ($8.25/month)
14-day free trial. 1,400+ retailers.""",
            "Instacart+", price_usd=99),

        camp("Theragun Mini Massager", "Wellness", """
Theragun Mini — Powerful Quiet Percussive Therapy
✓ 3 speeds, 150 min battery, travel-ready
✓ Relieves muscle soreness in 30 seconds
Price: $179 (was $229) — Save $50
Free shipping. 2-year warranty.""",
            "Theragun Mini", price_usd=179),

        camp("Allbirds Wool Runners", "Footwear", """
Allbirds Wool Runners — Ridiculously Comfortable
✓ ZQ Merino wool, carbon-negative materials
✓ Machine washable, 9 colors
Price: $130 — Free shipping & returns
60-day trial. If not in love, full refund.""",
            "Allbirds Runners", price_usd=130),
    ],

    # -----------------------------------------------------------------------
    "MENA_UAE": [  # BAE
        camp("iPhone 15 Pro", "Technology", """
iPhone 15 Pro — Titanium. So strong. So light. So Pro.
✓ A17 Pro chip, 48MP camera system, Action button
✓ USB-C, all-day battery (up to 23hrs)
Price: AED 4,299 (~$1,170)
0% installment plan. Available at Apple Store Dubai Mall.""",
            "iPhone 15 Pro", price_usd=1170),

        camp("Noon Daily Grocery", "Grocery/Sub", """
Noon Daily — Fresh Groceries Delivered in 2 Hours
✓ 10,000+ products, temperature-controlled delivery
Price: AED 29/month for free delivery
First order: 20% off with code NOONFRESH
Available in Dubai, Abu Dhabi""",
            "Noon Daily", price_usd=8),

        camp("Talabat Pro", "Food Delivery", """
Talabat Pro — Unlimited Free Delivery
✓ Free delivery from 1,000+ restaurants
✓ Exclusive Pro deals, priority support
Price: AED 19/month or AED 169/year
First month free.""",
            "Talabat Pro", price_usd=5),

        camp("Careem Plus", "Mobility/Sub", """
Careem Plus — Everything in One Subscription
✓ Unlimited rides with capped fares
✓ Free food delivery on AED 50+ orders
Price: AED 19/month
Cancel anytime. UAE, Egypt, Saudi Arabia.""",
            "Careem Plus", price_usd=5),

        camp("Adidas Ultraboost 23", "Sports", """
Adidas Ultraboost 23 — Energy Return Like Never Before
✓ BOOST midsole, Primeknit+ upper
✓ Continental rubber outsole
Price: AED 750 (~$204)
Free delivery in UAE. 30-day returns.""",
            "Adidas Ultraboost 23", price_usd=204),

        camp("Emirates Business Class Upgrade", "Travel/Luxury", """
Emirates Business Class — Fly Better
✓ Lie-flat private suite, gourmet dining
✓ Dubai–London from AED 8,500 (~$2,315)
Book 30 days ahead. Skywards Miles eligible.
Chauffeur-drive included.""",
            "Emirates Business Class", price_usd=2315),
    ],

    # -----------------------------------------------------------------------
    "MENA_EG": [  # Mısır
        camp("Vodafone Egypt 5G Plan", "Telecom", """
Vodafone Egypt — خطة 5G اللانهائية
✓ مكالمات ورسائل غير محدودة، 100GB 5G
✓ تطبيقات سوشيال ميديا مجانية
السعر: 299 جنيه/شهر (بدون عقد)
شريحة SIM مجانية. التوصيل في 24 ساعة.""",
            "Vodafone 5G EG", price_usd=6),

        camp("Jumia Electronics Sale", "Electronics", """
Jumia Egypt — Samsung Galaxy A55
✓ شاشة Super AMOLED 6.6 بوصة، كاميرا 50MP
✓ بطارية 5000mAh، شحن سريع 25W
السعر: 18,999 جنيه (بدلاً من 22,999 جنيه)
شحن مجاني. 7 أيام للإرجاع.""",
            "Samsung Galaxy A55", price_usd=380),

        camp("Shahid VIP Subscription", "Streaming", """
Shahid VIP — أفضل المسلسلات والأفلام العربية
✓ محتوى حصري، مسلسلات رمضان
✓ بدون إعلانات، جودة 4K
السعر: 35 جنيه/شهر أو 299 جنيه/سنة
جرب مجاناً لمدة 7 أيام""",
            "Shahid VIP", price_usd=1.10),

        camp("Otlob Pro Subscription", "Food Delivery", """
Otlob Pro — توصيل مجاني لا محدود
✓ توصيل مجاني من 500+ مطعم
✓ خصومات حصرية يومية
السعر: 49 جنيه/شهر
أول شهر مجاناً. متاح في القاهرة والإسكندرية""",
            "Otlob Pro", price_usd=1.60),

        camp("Levis 501 Egypt", "Fashion", """
Levi's 501 Original — متوفر في Namshi Egypt
✓ جينز أصلي، قصة مستقيمة، قطن 100%
✓ 10+ ألوان، مقاسات متنوعة
السعر: 2,499 جنيه — شحن مجاني
إرجاع مجاني 30 يوماً""",
            "Levi's 501 EG", price_usd=50),

        camp("Swvl Monthly Pass", "Mobility", """
Swvl — اشتراك شهري للتنقل
✓ رحلات يومية بأسعار ثابتة
✓ حافلات مكيفة، مسارات محددة
السعر: 599 جنيه/شهر (وفر 40%)
احجز من التطبيق. متاح في القاهرة""",
            "Swvl Monthly", price_usd=12),
    ],
}


# ===========================================================================
# SEGMENT AYARLARI — her kampanya FARKLI persona grubu alır
# ===========================================================================

REGION_CONFIG = {
    #  region   segment_enum   persona_per_campaign
    "TR":       (SegmentType.TR,   100),
    "EU_DE":    (SegmentType.EU,   100),
    "EU_FR":    (SegmentType.EU,   100),
    "EU_UK":    (SegmentType.EU,   100),
    "USA":      (SegmentType.USA,  100),
    "MENA_UAE": (SegmentType.MENA, 80),
    "MENA_EG":  (SegmentType.MENA, 80),
}

# Gün içinde toplam istek tahmini
def estimate_total(regions):
    total = 0
    for r in regions:
        _, n = REGION_CONFIG[r]
        total += n * len(CAMPAIGNS[r])
    return total


# ===========================================================================
# ANA ÇALIŞTIRICI
# ===========================================================================

async def run_region(region, runner, session):
    segment_enum, personas_per_camp = REGION_CONFIG[region]
    campaigns = CAMPAIGNS[region]
    n_camps = len(campaigns)

    print(f"\n{'='*60}")
    print(f"  BÖLGE: {region} — {n_camps} kampanya × {personas_per_camp} persona (her biri farklı)")
    print(f"{'='*60}")

    # DB'den yeterli sayıda persona çek (tüm kampanyalar için)
    needed = personas_per_camp * n_camps
    all_personas = (
        session.query(Persona)
        .filter(Persona.segment == segment_enum)
        .limit(needed)
        .all()
    )

    if len(all_personas) < personas_per_camp:
        print(f"  ⚠️  Yeterli persona yok ({len(all_personas)} < {personas_per_camp}), atlanıyor.")
        return []

    # Persona listesini karıştır
    random.shuffle(all_personas)

    # Her kampanyaya benzersiz dilim ver
    available = all_personas
    if len(available) >= needed:
        # Tam dilim — overlap yok
        persona_slices = [
            available[i * personas_per_camp: (i + 1) * personas_per_camp]
            for i in range(n_camps)
        ]
    else:
        # Yeterli yoksa tekrar örnekle (nadiren olur)
        persona_slices = [
            random.sample(available, min(personas_per_camp, len(available)))
            for _ in range(n_camps)
        ]

    print(f"  ✅ {len(all_personas)} persona DB'den yüklendi, {n_camps} gruba bölündü")

    # Kampanyaları DB'ye kaydet
    for c in campaigns:
        session.merge(c)
    session.commit()

    all_decisions = []
    for i, (campaign, personas) in enumerate(zip(campaigns, persona_slices)):
        print(f"  [{i+1}/{n_camps}] '{campaign.name}' — {len(personas)} farklı persona")
        decisions = await runner.run_campaign(campaign, personas)
        all_decisions.extend(decisions)
        session.merge(campaign)
        session.commit()

        buy = sum(1 for d in decisions if d.decision.value == "BUY")
        rate = buy / len(decisions) * 100 if decisions else 0
        print(f"        → Satın alma: %{rate:.1f} ({buy}/{len(decisions)})")

    return all_decisions


async def main(regions_to_run):
    api_key = os.environ.get("OPENAI_API_KEY")
    db_url = os.environ.get("DATABASE_URL")
    if not api_key or not db_url:
        print("❌ OPENAI_API_KEY veya DATABASE_URL eksik!")
        sys.exit(1)

    total_req = estimate_total(regions_to_run)
    print("\n" + "=" * 60)
    print("  AGENT MINING — BÖLGE BAZLI VERİ TOPLAMA")
    print("  (Her kampanya farklı persona grubu)")
    print("=" * 60)
    for r in regions_to_run:
        _, n = REGION_CONFIG[r]
        c = len(CAMPAIGNS[r])
        print(f"  {r:12} → {c} kampanya × {n} persona = {c*n:,} karar")
    print(f"  {'TOPLAM':12} → {total_req:,} istek")
    print(f"  Tahmini maliyet: ${total_req * 0.0001:.2f}")
    print("=" * 60)

    confirm = input("\nBaşlamak istiyor musun? [y/N]: ")
    if confirm.lower() != "y":
        print("İptal edildi.")
        return

    session = sessionmaker(bind=create_engine(db_url))()
    runner = CampaignRunner(
        openai_api_key=api_key,
        model="gpt-4o-mini",
        max_concurrent=8,
        session=session,
    )

    import time
    start = time.time()
    grand_total = 0

    for region in regions_to_run:
        decisions = await run_region(region, runner, session)
        grand_total += len(decisions)

    elapsed = time.time() - start
    session.close()

    print("\n" + "=" * 60)
    print("  🎉 VERİ TOPLAMA TAMAMLANDI")
    print("=" * 60)
    buy_total = sum(1 for d in [])  # decisions birleşik listede değil, log'dan oku
    tokens = runner.stats['total_input_tokens'] + runner.stats['total_output_tokens']
    print(f"  Toplam karar:  {runner.stats['successful']:,}")
    print(f"  Başarısız:     {runner.stats['failed']}")
    print(f"  Toplam token:  {tokens:,}")
    print(f"  Gerçek maliyet: ${runner._estimate_cost():.4f}")
    print(f"  Süre:          {elapsed:.0f}s ({elapsed/60:.1f} dakika)")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", choices=list(REGION_CONFIG.keys()),
                        help="Tek bölge çalıştır")
    parser.add_argument("--list", action="store_true",
                        help="Tüm bölgeleri ve kampanya sayılarını listele")
    args = parser.parse_args()

    if args.list:
        print("\nMevcut bölgeler:")
        for r, (seg, n) in REGION_CONFIG.items():
            c = len(CAMPAIGNS[r])
            print(f"  {r:12} → segment={seg.value}, {c} kampanya × {n} persona = {c*n} karar")
        sys.exit(0)

    regions = [args.region] if args.region else list(REGION_CONFIG.keys())
    asyncio.run(main(regions))