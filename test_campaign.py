"""
SimuTarget.ai - İnteraktif Kampanya Test Aracı
==============================================

Kullanım:
    python test_campaign.py

Gereksinimler:
    - OPENAI_API_KEY environment variable
    - pip install openai pydantic python-dotenv
"""

from dotenv import load_dotenv
load_dotenv()

import os
import sys

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.personas import PersonaFactory, Region, PersonaConfig
from src.inference import SimuTargetLLM, CampaignTestResult


def print_banner():
    """Başlık yazdır."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                    🎯 SimuTarget.ai                           ║
║              AI-Powered Campaign Testing                       ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def select_test_type() -> str:
    """Test türü seçimi."""
    print("\n📋 TEST TÜRÜ SEÇİMİ")
    print("-" * 40)
    print("  1. 📊 Tek Kampanya Testi (EVET/HAYIR)")
    print("  2. ⚔️  A/B Karşılaştırma (A vs B)")
    
    while True:
        choice = input("\nSeçiminiz (1-2) [varsayılan: 1]: ").strip() or "1"
        if choice in ["1", "2"]:
            return "single" if choice == "1" else "ab"
        print("⚠️ Geçersiz seçim!")


def select_region() -> Region:
    """Bölge seçimi."""
    print("\n📍 BÖLGE SEÇİMİ")
    print("-" * 40)
    regions = {
        "1": ("TR", "🇹🇷 Türkiye"),
        "2": ("US", "🇺🇸 Amerika"),
        "3": ("EU", "🇪🇺 Avrupa"),
        "4": ("MENA", "🌙 Orta Doğu & Kuzey Afrika"),
    }
    
    for key, (code, name) in regions.items():
        print(f"  {key}. {name}")
    
    while True:
        choice = input("\nSeçiminiz (1-4) [varsayılan: 1]: ").strip() or "1"
        if choice in regions:
            region_code = regions[choice][0]
            return Region(region_code)
        print("⚠️ Geçersiz seçim!")


def get_persona_count() -> int:
    """Persona sayısı al."""
    while True:
        try:
            count = input("\n👥 Kaç persona ile test edilsin? [varsayılan: 5]: ").strip() or "5"
            count = int(count)
            if 1 <= count <= 100:
                return count
            print("⚠️ 1-100 arası bir sayı girin!")
        except ValueError:
            print("⚠️ Geçerli bir sayı girin!")


def get_campaign_content() -> str:
    """Kampanya içeriği al."""
    print("\n📢 KAMPANYA İÇERİĞİ")
    print("-" * 40)
    print("Reklam metninizi girin (bitirmek için boş satır + Enter):")
    print()
    
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    
    content = "\n".join(lines)
    
    if not content.strip():
        content = """
🎉 SÜPER FIRSATI KAÇIRMA! 🎉

iPhone 15 Pro - Şimdi %30 İNDİRİMLİ!
Sadece 3 gün süreyle geçerli bu muhteşem fırsat!

✅ 12 aya varan taksit imkanı
✅ Ücretsiz kargo
✅ 2 yıl garanti

Normal fiyat: 89.999 TL
ŞİMDİ: 62.999 TL
        """
        print(f"\n💡 Örnek kampanya kullanılıyor")
    
    return content


def get_ab_content() -> tuple:
    """A/B içerikleri al."""
    print("\n" + "=" * 60)
    print("📌 SEÇENEK A")
    print("=" * 60)
    print("İlk seçeneği girin (bitirmek için boş satır + Enter):")
    print()
    
    lines_a = []
    while True:
        line = input()
        if line == "":
            break
        lines_a.append(line)
    
    content_a = "\n".join(lines_a)
    
    if not content_a.strip():
        content_a = """
Aday: Recep Tayyip Erdoğan (AKP)
- 22 yıldır iktidarda
- Muhafazakar/sağ politikalar
- Güçlü liderlik vurgusu
- Mega projeler (köprüler, havalimanı)
        """
        print("💡 Örnek A kullanılıyor")
    
    print("\n" + "=" * 60)
    print("📌 SEÇENEK B")
    print("=" * 60)
    print("İkinci seçeneği girin (bitirmek için boş satır + Enter):")
    print()
    
    lines_b = []
    while True:
        line = input()
        if line == "":
            break
        lines_b.append(line)
    
    content_b = "\n".join(lines_b)
    
    if not content_b.strip():
        content_b = """
Aday: Ekrem İmamoğlu (CHP)
- İstanbul Büyükşehir Belediye Başkanı
- Sosyal demokrat/merkez sol politikalar
- Değişim ve yenilik vurgusu
- Belediyecilik deneyimi
        """
        print("💡 Örnek B kullanılıyor")
    
    return content_a, content_b


def display_detailed_results(result: CampaignTestResult):
    """Detaylı sonuçları göster."""
    print("\n" + "=" * 60)
    print("📊 DETAYLI SONUÇLAR")
    print("=" * 60)
    
    print(f"""
┌─────────────────────────────────────────────────────────────┐
│ 📈 GENEL İSTATİSTİKLER                                      │
├─────────────────────────────────────────────────────────────┤
│ Toplam Persona:        {result.total_personas:>5}                              │
│ Başarılı Değerlendirme:{result.successful_evaluations:>5}                              │
│ Başarısız:             {result.failed_evaluations:>5}                              │
├─────────────────────────────────────────────────────────────┤
│ ✅ EVET Oyu:           {result.yes_count:>5}                              │
│ ❌ HAYIR Oyu:          {result.no_count:>5}                              │
│ 📊 Dönüşüm Oranı:      {result.conversion_rate:>5.1f}%                            │
│ 💯 Ortalama Güven:     {result.avg_confidence:>5.1f}/10                           │
└─────────────────────────────────────────────────────────────┘
    """)
    
    print("\n📋 KİŞİ BAZLI SONUÇLAR")
    print("-" * 60)
    
    for i, eval_result in enumerate(result.results, 1):
        persona = eval_result.persona
        decision = eval_result.decision
        
        if decision:
            emoji = "✅" if decision.decision else "❌"
            karar = "EVET" if decision.decision else "HAYIR"
            
            print(f"""
[{i}] {persona.name}
    👤 {persona.age} yaş, {persona.gender}, {persona.occupation}
    📍 {persona.city}, {persona.country}
    💰 Gelir: {persona.income_level}
    🛒 Alışveriş: {persona.buying_style}
    """, end="")
            
            if persona.primary_anxiety:
                print(f"    🎯 Profil: {persona.primary_anxiety.name}")
            
            print(f"""
    ─────────────────────────────────────
    {emoji} Karar: {karar} (Güven: {decision.confidence}/10)
    💬 "{decision.reasoning}"
    """, end="")
            
            if decision.influencing_factors:
                print(f"    📌 Faktörler: {', '.join(decision.influencing_factors)}")
            
            if decision.anxiety_impact:
                print(f"    🎯 Profil Etkisi: {decision.anxiety_impact}")
            
            print()
        else:
            print(f"\n[{i}] {persona.name} - ⚠️ Değerlendirme başarısız")
            if eval_result.error:
                print(f"    Hata: {eval_result.error}")
    
    # Segmentasyon
    display_segmentation(result)


def display_segmentation(result: CampaignTestResult):
    """Segmentasyon analizi göster."""
    print("\n📊 SEGMENTASYON ANALİZİ")
    print("-" * 60)
    
    # Yaş grupları
    age_groups = {"18-25": [], "26-35": [], "36-45": [], "46-55": [], "56+": []}
    for r in result.results:
        if r.success and r.decision:
            age = r.persona.age
            if age <= 25:
                age_groups["18-25"].append(r.decision.decision)
            elif age <= 35:
                age_groups["26-35"].append(r.decision.decision)
            elif age <= 45:
                age_groups["36-45"].append(r.decision.decision)
            elif age <= 55:
                age_groups["46-55"].append(r.decision.decision)
            else:
                age_groups["56+"].append(r.decision.decision)
    
    print("\n📅 Yaş Gruplarına Göre Dönüşüm:")
    for group, decisions in age_groups.items():
        if decisions:
            rate = (sum(decisions) / len(decisions)) * 100
            bar = "█" * int(rate / 5) + "░" * (20 - int(rate / 5))
            print(f"  {group:>6}: {bar} {rate:.0f}% ({sum(decisions)}/{len(decisions)})")
    
    # Cinsiyet
    print("\n👥 Cinsiyete Göre Dönüşüm:")
    gender_results = {"Erkek": [], "Kadın": []}
    for r in result.results:
        if r.success and r.decision:
            gender = r.persona.gender
            if gender in gender_results:
                gender_results[gender].append(r.decision.decision)
    
    for gender, decisions in gender_results.items():
        if decisions:
            rate = (sum(decisions) / len(decisions)) * 100
            bar = "█" * int(rate / 5) + "░" * (20 - int(rate / 5))
            print(f"  {gender:>6}: {bar} {rate:.0f}% ({sum(decisions)}/{len(decisions)})")


def display_ab_results(results: list, content_a: str, content_b: str):
    """A/B test sonuçlarını göster."""
    print("\n" + "=" * 60)
    print("📊 A/B KARŞILAŞTIRMA SONUÇLARI")
    print("=" * 60)
    
    a_votes = sum(1 for r in results if r.choice == "A")
    b_votes = sum(1 for r in results if r.choice == "B")
    none_votes = sum(1 for r in results if r.choice == "HİÇBİRİ")
    total = len(results)
    
    a_pct = (a_votes / total * 100) if total > 0 else 0
    b_pct = (b_votes / total * 100) if total > 0 else 0
    none_pct = (none_votes / total * 100) if total > 0 else 0
    
    avg_a_score = sum(r.option_scores.get("A", 0) for r in results) / total if total > 0 else 0
    avg_b_score = sum(r.option_scores.get("B", 0) for r in results) / total if total > 0 else 0
    
    print(f"""
┌─────────────────────────────────────────────────────────────┐
│ 📈 GENEL SONUÇLAR                                           │
├─────────────────────────────────────────────────────────────┤
│ 🔵 SEÇENEK A:     {a_votes:>3} oy  ({a_pct:>5.1f}%)  [Puan: {avg_a_score:.1f}/10]       │
│ 🔴 SEÇENEK B:     {b_votes:>3} oy  ({b_pct:>5.1f}%)  [Puan: {avg_b_score:.1f}/10]       │
│ ⚪ KARARSIZ:      {none_votes:>3} oy  ({none_pct:>5.1f}%)                          │
├─────────────────────────────────────────────────────────────┤
│ 🏆 KAZANAN: {"SEÇENEK A" if a_votes > b_votes else "SEÇENEK B" if b_votes > a_votes else "BERABERE":^15}                              │
└─────────────────────────────────────────────────────────────┘
    """)
    
    # Kişi bazlı sonuçlar
    print("\n📋 KİŞİ BAZLI SONUÇLAR")
    print("-" * 60)
    
    for i, r in enumerate(results, 1):
        emoji = "🔵" if r.choice == "A" else "🔴" if r.choice == "B" else "⚪"
        political = r.persona_political_view or "Belirtilmemiş"
        
        print(f"""
[{i}] {r.persona_name}
    👤 {r.persona_age} yaş, {r.persona_gender}, {r.persona_occupation}
    🗳️  Siyasi Görüş: {political}
    ─────────────────────────────────────
    {emoji} Tercih: {r.choice} (Güven: {r.confidence}/10)
    📊 Puanlar: A={r.option_scores.get('A', 0)}/10, B={r.option_scores.get('B', 0)}/10
    💬 "{r.reasoning[:100]}..."
    """, end="")
        
        if r.political_influence:
            print(f"    🗳️  Siyasi Etki: {r.political_influence}")
        print()
    
    # Siyasi görüşe göre segmentasyon
    display_ab_segmentation(results)


def display_ab_segmentation(results: list):
    """A/B segmentasyon analizi."""
    print("\n📊 SEGMENTASYON ANALİZİ")
    print("-" * 60)
    
    # Siyasi görüşe göre
    print("\n🗳️  Siyasi Görüşe Göre:")
    political_results = {}
    for r in results:
        pv = r.persona_political_view or "Belirtilmemiş"
        if pv not in political_results:
            political_results[pv] = {"A": 0, "B": 0, "HİÇBİRİ": 0}
        political_results[pv][r.choice] += 1
    
    for pv, votes in political_results.items():
        total = votes["A"] + votes["B"] + votes["HİÇBİRİ"]
        if total > 0:
            a_pct = votes["A"] / total * 100
            b_pct = votes["B"] / total * 100
            print(f"  {pv:>12}: 🔵 A %{a_pct:.0f} | 🔴 B %{b_pct:.0f} ({total} kişi)")
    
    # Yaş gruplarına göre
    print("\n📅 Yaş Gruplarına Göre:")
    age_results = {"18-30": {"A": 0, "B": 0}, "31-45": {"A": 0, "B": 0}, "46-60": {"A": 0, "B": 0}, "61+": {"A": 0, "B": 0}}
    for r in results:
        age = r.persona_age
        if age <= 30:
            group = "18-30"
        elif age <= 45:
            group = "31-45"
        elif age <= 60:
            group = "46-60"
        else:
            group = "61+"
        
        if r.choice in ["A", "B"]:
            age_results[group][r.choice] += 1
    
    for group, votes in age_results.items():
        total = votes["A"] + votes["B"]
        if total > 0:
            a_pct = votes["A"] / total * 100
            b_pct = votes["B"] / total * 100
            print(f"  {group:>6}: 🔵 A %{a_pct:.0f} | 🔴 B %{b_pct:.0f} ({total} kişi)")
    
    # Cinsiyete göre
    print("\n👥 Cinsiyete Göre:")
    gender_results = {"Erkek": {"A": 0, "B": 0}, "Kadın": {"A": 0, "B": 0}}
    for r in results:
        gender = r.persona_gender
        if gender in gender_results and r.choice in ["A", "B"]:
            gender_results[gender][r.choice] += 1
    
    for gender, votes in gender_results.items():
        total = votes["A"] + votes["B"]
        if total > 0:
            a_pct = votes["A"] / total * 100
            b_pct = votes["B"] / total * 100
            print(f"  {gender:>6}: 🔵 A %{a_pct:.0f} | 🔴 B %{b_pct:.0f} ({total} kişi)")


def run_single_test(llm, personas):
    """Tek kampanya testi çalıştır."""
    campaign_content = get_campaign_content()
    
    print("\n" + "=" * 60)
    print("🚀 KAMPANYA TESTİ BAŞLIYOR")
    print("=" * 60)
    
    result = llm.test_campaign(
        personas=personas,
        campaign_content=campaign_content,
        campaign_id="interactive_test",
        verbose=True,
    )
    
    display_detailed_results(result)
    return result


def run_ab_test(llm, personas):
    """A/B karşılaştırma testi çalıştır."""
    content_a, content_b = get_ab_content()
    
    print("\n" + "=" * 60)
    print("🚀 A/B KARŞILAŞTIRMA TESTİ BAŞLIYOR")
    print("=" * 60)
    print(f"👥 Persona sayısı: {len(personas)}")
    print("=" * 60)
    
    results = []
    for i, persona in enumerate(personas, 1):
        print(f"\n[{i}/{len(personas)}] Değerlendiriliyor...")
        result = llm.compare_campaigns(
            persona=persona,
            campaign_a=content_a,
            campaign_b=content_b,
            verbose=True,
        )
        results.append(result)
    
    display_ab_results(results, content_a, content_b)
    return results


def main():
    """Ana fonksiyon."""
    print_banner()
    
    # API key kontrolü
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY bulunamadı!")
        print("Lütfen şu komutu çalıştırın:")
        print('  export OPENAI_API_KEY="sk-..."')
        print("veya")
        print('  set OPENAI_API_KEY=sk-...')
        return
    
    print("✅ OpenAI API key bulundu")
    
    # Test türü seçimi
    test_type = select_test_type()
    
    # Bölge seçimi
    region = select_region()
    print(f"\n✅ Seçilen bölge: {region.value}")
    
    # Persona sayısı
    persona_count = get_persona_count()
    
    # Personaları oluştur
    print(f"\n🔄 {persona_count} persona oluşturuluyor...")
    config = PersonaConfig(region=region)
    factory = PersonaFactory(config=config)
    personas = factory.generate_batch(persona_count)
    print(f"✅ {len(personas)} persona hazır!")
    
    # Personaları göster
    print("\n👥 OLUŞTURULAN PERSONALAR:")
    print("-" * 40)
    for i, p in enumerate(personas, 1):
        political = f" 🗳️{p.political_view}" if p.political_view else ""
        profile = f" 🎯{p.primary_anxiety.name}" if p.primary_anxiety else ""
        print(f"  {i}. {p.name} ({p.age}, {p.gender}) - {p.occupation}{political}{profile}")
    
    # LLM client
    print("\n🤖 LLM başlatılıyor...")
    llm = SimuTargetLLM(
        model="gpt-4o-mini",
        temperature=1.0,
    )
    print("✅ LLM hazır!")
    
    # Test türüne göre çalıştır
    if test_type == "single":
        run_single_test(llm, personas)
    else:
        run_ab_test(llm, personas)
    
    # Tekrar test
    while True:
        again = input("\n🔄 Yeni bir test yapmak ister misiniz? (e/h) [h]: ").strip().lower()
        if again == "e":
            test_type = select_test_type()
            if test_type == "single":
                run_single_test(llm, personas)
            else:
                run_ab_test(llm, personas)
        else:
            break
    
    print("\n👋 Teşekkürler! SimuTarget.ai")


if __name__ == "__main__":
    main()