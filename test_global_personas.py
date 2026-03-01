"""SimuTarget.ai - Global Persona Test"""

from src.personas import PersonaFactory, PersonaConfig, Region

def print_persona(p, index: int):
    """Persona'yı detaylı yazdır."""
    print(f"\n{'='*70}")
    print(f"👤 PERSONA #{index}")
    print(f"{'='*70}")
    
    print(f"\n📋 TEMEL BİLGİLER")
    print(f"   İsim           : {p.name}")
    print(f"   Bölge          : {p.region}")
    print(f"   Ülke           : {p.country}")
    print(f"   Şehir          : {p.city}")
    print(f"   Yaş            : {p.age}")
    print(f"   Cinsiyet       : {p.gender}")
    print(f"   Medeni Hali    : {p.marital_status}")
    print(f"   Çocuk Sayısı   : {p.children_count}")
    
    print(f"\n💼 SOSYOEKONOMİK")
    print(f"   Eğitim         : {p.education}")
    print(f"   Meslek         : {p.occupation}")
    print(f"   Gelir          : {p.income_level}")
    print(f"   Satın Alma Gücü: {p.purchasing_power:.2f}")
    
    print(f"\n🎭 DEĞERLER & İNANÇLAR")
    print(f"   Hayata Bakış   : {p.life_outlook}")
    print(f"   Siyasi Görüş   : {p.political_view or 'Belirtilmemiş'}")
    print(f"   Din            : {p.religion}")
    print(f"   Hayvansever    : {'Evet' if p.personal_values.animal_lover else 'Hayır'}")
    print(f"   Çevreci        : {'Evet' if p.personal_values.environmentalist else 'Hayır'}")
    print(f"   Aile Odaklı    : {'Evet' if p.personal_values.family_oriented else 'Hayır'}")
    
    print(f"\n🛒 TÜKETİCİ DAVRANIŞI")
    print(f"   Alışveriş      : {p.shopping_preference}")
    print(f"   Satın Alma     : {p.buying_style}")
    print(f"   Teknoloji      : {p.tech_adoption}")
    print(f"   Sosyal Medya   : {p.social_media_influence}")
    print(f"   Finansal       : {p.financial_behavior}")
    
    print(f"\n📱 DİJİTAL ALIŞKANLIKLAR")
    print(f"   Ana Platform   : {p.digital_habits.primary_platform}")
    print(f"   Ekran Süresi   : {p.digital_habits.screen_time}")
    print(f"   Online Alışveriş: {p.digital_habits.online_shopping_freq}")
    print(f"   Ödeme Tercihi  : {p.digital_habits.payment_preference}")
    
    print(f"\n😰 GİZLİ ENDİŞELER")
    if p.primary_anxiety:
        print(f"   Birincil       : {p.primary_anxiety.name}")
        print(f"                    \"{p.primary_anxiety.description}\"")
    if p.secondary_anxiety:
        print(f"   İkincil        : {p.secondary_anxiety.name}")
        print(f"                    \"{p.secondary_anxiety.description}\"")
    
    print(f"\n🧠 KİŞİLİK (Big Five)")
    print(f"   Yeniliğe Açık  : {p.personality.openness:.2f}")
    print(f"   Sorumluluk     : {p.personality.conscientiousness:.2f}")
    print(f"   Dışa Dönüklük  : {p.personality.extraversion:.2f}")
    print(f"   Uyumluluk      : {p.personality.agreeableness:.2f}")
    print(f"   Duygusal Denge : {p.personality.neuroticism:.2f}")


def test_region(region_code: str, region_name: str, count: int = 3):
    """Belirli bir bölge için test."""
    print(f"\n\n{'#'*70}")
    print(f"# 🌍 {region_name} ({region_code}) - {count} Persona")
    print(f"{'#'*70}")
    
    config = PersonaConfig(region=Region(region_code))
    factory = PersonaFactory(config)
    
    personas = factory.generate_batch(count)
    
    for i, p in enumerate(personas, 1):
        print_persona(p, i)
    
    # İstatistikler
    print(f"\n📊 {region_name} İSTATİSTİKLERİ")
    print(f"   Erkek: {sum(1 for p in personas if p.gender == 'Erkek')}")
    print(f"   Kadın: {sum(1 for p in personas if p.gender == 'Kadın')}")
    print(f"   Ort. Yaş: {sum(p.age for p in personas) / len(personas):.1f}")
    
    return personas


if __name__ == "__main__":
    print("=" * 70)
    print("🎯 SimuTarget.ai - Global Persona Test")
    print("=" * 70)
    print("4 Bölge x 3 Persona = 12 Toplam Persona")
    
    # Her bölge için test
    tr_personas = test_region("TR", "TÜRKİYE", 3)
    us_personas = test_region("US", "ABD", 3)
    eu_personas = test_region("EU", "AVRUPA", 3)
    mena_personas = test_region("MENA", "MENA", 3)
    
    print("\n\n" + "=" * 70)
    print("✅ TEST TAMAMLANDI!")
    print("=" * 70)
    print(f"Toplam üretilen persona: {len(tr_personas) + len(us_personas) + len(eu_personas) + len(mena_personas)}")
