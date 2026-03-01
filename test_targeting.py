"""SimuTarget Smart Targeting Test - Akıllı Hedefleme Testi"""

from dotenv import load_dotenv
load_dotenv()

from src.personas import SmartTargeting, auto_target, SegmentedPersonaFactory, SEGMENTS
from src.inference import OpenAIClient

print("=" * 60)
print("SimuTarget.ai - Akıllı Hedefleme Testi")
print("=" * 60)

# Farklı reklamlar test edelim
test_campaigns = [
    {
        "name": "Ucuz Dürüm",
        "content": "Dönerci Baba'da Mega Dürüm sadece 75 TL! Öğrenci kartına %10 indirim. Gel, doyurucu ye!"
    },
    {
        "name": "Pahalı Telefon", 
        "content": "Yeni iPhone 16 Pro Max - 94.999 TL. Titanium kasa, 5x optik zoom. Apple Store'da şimdi."
    },
    {
        "name": "Orta Segment Telefon",
        "content": "Xiaomi Redmi Note 13 Pro - 12.999 TL! 200MP kamera, 5000mAh batarya. Trendyol'da hemen al."
    },
    {
        "name": "Lüks Araba",
        "content": "Yeni BMW 5 Serisi. 3.500.000 TL'den başlayan fiyatlarla. Driving pleasure redefined."
    },
]

targeting = SmartTargeting()

for campaign in test_campaigns:
    print(f"\n{'='*60}")
    print(f"📢 REKLAM: {campaign['name']}")
    print(f"{'='*60}")
    print(f"İçerik: {campaign['content'][:80]}...")
    
    # Analiz yap
    analysis = targeting.analyze_campaign(campaign['content'])
    segments = targeting.get_target_segments(campaign['content'])
    
    print(f"\n🔍 ANALİZ:")
    print(f"   Ürün: {analysis.get('product_type')}")
    print(f"   Fiyat Seviyesi: {analysis.get('price_level')}")
    if analysis.get('price_tl'):
        print(f"   Fiyat: {analysis['price_tl']:,.0f} TL")
    
    print(f"\n🎯 HEDEF SEGMENTLER:")
    for seg in segments:
        seg_info = SEGMENTS.get(seg, {})
        print(f"   • {seg_info.get('name', seg)}")

print("\n" + "=" * 60)
print("DETAYLI TEST: Dürüm Reklamı")
print("=" * 60)

# Dürüm reklamı için detaylı test
durum_reklam = "Dönerci Baba'da Mega Dürüm sadece 75 TL! Öğrenci kartına %10 indirim."

# Açıklama al
explanation = targeting.explain_targeting(durum_reklam)
print(explanation)

# 20 persona üret ve test et
print("\n🧪 20 PERSONA İLE TEST:")
print("-" * 40)

personas, analysis = targeting.generate_targeted_personas(durum_reklam, total_count=20)

# OpenAI client
try:
    client = OpenAIClient()
    
    evet_sayisi = 0
    for i, persona in enumerate(personas[:20]):
        karar = client.get_decision(persona, durum_reklam, "durum-test")
        sonuc = "✓" if karar.decision else "✗"
        if karar.decision:
            evet_sayisi += 1
        
        print(f"{sonuc} {persona.name} ({persona.age}, {persona.occupation}, {persona.income_level})")
    
    print(f"\n📊 SONUÇ: {evet_sayisi}/20 kişi satın alır (%{evet_sayisi * 5} dönüşüm)")

except Exception as e:
    print(f"⚠️ LLM testi atlandı: {e}")
    print("\nÜretilen personalar:")
    for p in personas[:10]:
        print(f"  • {p.name} ({p.age}, {p.occupation}, {p.income_level})")