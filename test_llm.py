"""SimuTarget LLM Test - İlk Kampanya Testi"""

from dotenv import load_dotenv
load_dotenv()

from src.personas import PersonaFactory
from src.inference import OpenAIClient

# Başlat
factory = PersonaFactory()
client = OpenAIClient()

# Test reklamı
reklam = "Migros'ta bu hafta: 1 kg çay sadece 179 TL! Üstelik %20 indirim kuponu hediye."


print("=" * 60)
print("SimuTarget.ai - İlk LLM Testi")
print(f"Reklam: {reklam}")
print("=" * 60)

# 10 persona test et
evet_sayisi = 0
for i in range(10):
    p = factory.generate_one()
    k = client.get_decision(p, reklam, "test-iphone")
    
    sonuc = "✓ EVET" if k.decision else "✗ HAYIR"
    if k.decision:
        evet_sayisi += 1
    
    print(f"\n{i+1}. {p.name}")
    print(f"   Profil: {p.age} yaş, {p.gender}, {p.location}, {p.income_level}")
    print(f"   Karar: {sonuc} (Güven: {k.confidence}/10)")
    print(f"   Gerekçe: {k.reasoning}")

# Özet
print("\n" + "=" * 60)
print(f"SONUÇ: {evet_sayisi}/10 kişi satın alır (%{evet_sayisi * 10} dönüşüm)")
print("=" * 60)