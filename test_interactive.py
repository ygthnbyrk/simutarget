"""SimuTarget.ai - İnteraktif Kampanya Test Aracı

Bu dosya ile kendi reklamlarınızı test edebilirsiniz.
Sistem otomatik olarak hedef kitleyi belirler ve detaylı sonuçlar verir.
"""

from dotenv import load_dotenv
load_dotenv()

from src.personas import SmartTargeting, PersonaFactory, SEGMENTS
from src.inference import OpenAIClient

def print_header():
    print("\n" + "=" * 70)
    print("🎯 SimuTarget.ai - Kampanya Test Aracı")
    print("=" * 70)
    print("Reklamınızı test edin, hedef kitlenizin tepkisini görün!\n")

def get_campaign_from_user():
    """Kullanıcıdan reklam metnini al."""
    print("📝 REKLAM METNİNİZİ GİRİN:")
    print("-" * 40)
    print("(Birden fazla satır yazabilirsiniz. Bitirmek için boş satır bırakın)\n")
    
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    
    return "\n".join(lines)

def get_persona_count():
    """Kullanıcıdan test edilecek persona sayısını al."""
    while True:
        try:
            count = input("\n👥 Kaç kişi ile test edilsin? (10-100, varsayılan 20): ").strip()
            if count == "":
                return 20
            count = int(count)
            if 10 <= count <= 100:
                return count
            print("⚠️ 10-100 arası bir sayı girin.")
        except ValueError:
            print("⚠️ Geçerli bir sayı girin.")

def get_targeting_mode():
    """Kullanıcıdan hedefleme modunu al."""
    print("\n🎯 HEDEFLEME MODU SEÇİN:")
    print("-" * 40)
    print("1. Otomatik (AI reklamı analiz edip hedef kitle seçsin)")
    print("2. Tüm segmentler (genel Türkiye nüfusu)")
    print("3. Manuel segment seçimi")
    
    while True:
        choice = input("\nSeçiminiz (1/2/3, varsayılan 1): ").strip()
        if choice in ["", "1"]:
            return "auto"
        elif choice == "2":
            return "all"
        elif choice == "3":
            return "manual"
        print("⚠️ 1, 2 veya 3 girin.")

def select_manual_segments():
    """Manuel segment seçimi."""
    print("\n📋 MEVCUT SEGMENTLER:")
    print("-" * 40)
    
    segment_list = list(SEGMENTS.keys())
    for i, seg_name in enumerate(segment_list, 1):
        seg_info = SEGMENTS[seg_name]
        print(f"{i:2}. {seg_info['name']}: {seg_info['description']}")
    
    print("\nBirden fazla segment seçebilirsiniz (virgülle ayırın).")
    print("Örnek: 1,3,5")
    
    while True:
        selection = input("\nSeçimleriniz: ").strip()
        try:
            indices = [int(x.strip()) for x in selection.split(",")]
            selected = [segment_list[i-1] for i in indices if 1 <= i <= len(segment_list)]
            if selected:
                return selected
            print("⚠️ En az bir segment seçin.")
        except:
            print("⚠️ Geçerli sayılar girin (örn: 1,3,5)")

def run_test(campaign_content: str, persona_count: int, targeting_mode: str, manual_segments: list = None):
    """Kampanya testini çalıştır."""
    
    print("\n" + "=" * 70)
    print("🔄 TEST BAŞLIYOR...")
    print("=" * 70)
    
    # Hedefleme sistemi
    targeting = SmartTargeting()
    factory = PersonaFactory()
    
    # Analiz
    print("\n📊 REKLAM ANALİZİ:")
    print("-" * 40)
    
    analysis = targeting.analyze_campaign(campaign_content)
    print(f"   Ürün Kategorisi : {analysis.get('product_type', 'Belirlenemedi')}")
    print(f"   Fiyat Seviyesi  : {analysis.get('price_level', 'Belirlenemedi')}")
    if analysis.get('price_tl'):
        print(f"   Tespit Edilen Fiyat: {analysis['price_tl']:,.0f} TL")
    
    # Personaları üret
    print("\n👥 PERSONA ÜRETİMİ:")
    print("-" * 40)
    
    if targeting_mode == "auto":
        personas, _ = targeting.generate_targeted_personas(campaign_content, persona_count)
        segments_used = targeting.get_target_segments(campaign_content)
        print(f"   AI tarafından seçilen segmentler:")
        for seg in segments_used:
            print(f"   • {SEGMENTS[seg]['name']}")
    
    elif targeting_mode == "all":
        personas = factory.generate_batch(persona_count)
        print(f"   Genel Türkiye nüfusundan {persona_count} kişi seçildi.")
    
    else:  # manual
        from src.personas import SegmentedPersonaFactory
        seg_factory = SegmentedPersonaFactory()
        
        # Seçilen segmentlerden eşit dağılımlı üret
        segment_weights = {seg: 1.0 for seg in manual_segments}
        personas = seg_factory.generate_mixed(segment_weights, persona_count)
        print(f"   Manuel seçilen segmentler:")
        for seg in manual_segments:
            print(f"   • {SEGMENTS[seg]['name']}")
    
    # LLM ile test et
    print(f"\n🧠 {persona_count} KİŞİNİN KARARLARI:")
    print("=" * 70)
    
    try:
        client = OpenAIClient()
        
        results = {
            "evet": [],
            "hayir": []
        }
        
        for i, persona in enumerate(personas):
            karar = client.get_decision(persona, campaign_content, "user-test")
            
            # Detaylı çıktı
            emoji = "✅" if karar.decision else "❌"
            
            print(f"\n{emoji} {i+1}. {persona.name}")
            print(f"   📋 Profil: {persona.age} yaş, {persona.gender}, {persona.location}")
            print(f"   💼 Meslek: {persona.occupation}")
            print(f"   💰 Gelir: {persona.income_level}")
            print(f"   🎯 Karar: {'SATIN ALIR' if karar.decision else 'SATIN ALMAZ'} (Güven: {karar.confidence}/10)")
            print(f"   💬 Gerekçe: \"{karar.reasoning}\"")
            
            if karar.decision:
                results["evet"].append(persona)
            else:
                results["hayir"].append(persona)
        
        # Sonuç özeti
        evet_sayisi = len(results["evet"])
        toplam = len(personas)
        oran = (evet_sayisi / toplam) * 100
        
        print("\n" + "=" * 70)
        print("📈 SONUÇ ÖZETİ")
        print("=" * 70)
        
        print(f"\n   🎯 Dönüşüm Oranı: %{oran:.1f}")
        print(f"   ✅ Satın Alır: {evet_sayisi} kişi")
        print(f"   ❌ Satın Almaz: {toplam - evet_sayisi} kişi")
        
        # Demografik analiz
        print(f"\n   📊 SATIN ALANLARIN PROFİLİ:")
        if results["evet"]:
            # Yaş ortalaması
            yas_ort = sum(p.age for p in results["evet"]) / len(results["evet"])
            print(f"      Ortalama yaş: {yas_ort:.0f}")
            
            # Gelir dağılımı
            gelir_dag = {}
            for p in results["evet"]:
                gelir_dag[p.income_level] = gelir_dag.get(p.income_level, 0) + 1
            print(f"      Gelir dağılımı: {gelir_dag}")
            
            # Meslek dağılımı
            meslek_dag = {}
            for p in results["evet"]:
                meslek_dag[p.occupation] = meslek_dag.get(p.occupation, 0) + 1
            en_cok_meslek = max(meslek_dag, key=meslek_dag.get)
            print(f"      En çok alan meslek: {en_cok_meslek} ({meslek_dag[en_cok_meslek]} kişi)")
        else:
            print("      Hiç kimse satın almadı.")
        
        print(f"\n   📊 SATIN ALMAYANLARIN EN SIK GEREKÇELERİ:")
        if results["hayir"]:
            print("      (Yukarıdaki yanıtlara bakınız)")
        
        # Tavsiyeler
        print("\n" + "=" * 70)
        print("💡 TAVSİYELER")
        print("=" * 70)
        
        if oran < 20:
            print("   ⚠️ Dönüşüm oranı düşük. Şunları değerlendirin:")
            print("      • Fiyatı gözden geçirin")
            print("      • Hedef kitleyi daraltın")
            print("      • Değer önerisini güçlendirin")
        elif oran < 40:
            print("   📊 Ortalama bir dönüşüm oranı.")
            print("      • A/B test ile farklı mesajlar deneyin")
            print("      • Belirli segmentlere özelleştirilmiş kampanyalar yapın")
        else:
            print("   ✨ Yüksek dönüşüm oranı! Kampanya başarılı görünüyor.")
            print("      • Bu mesajı daha geniş kitleye yayabilirsiniz")
            print("      • Benzer kampanyalar planlayabilirsiniz")
        
    except Exception as e:
        print(f"\n⚠️ Hata oluştu: {e}")
        print("OpenAI API key'inizi kontrol edin.")

def main():
    """Ana program."""
    print_header()
    
    while True:
        # Reklam al
        campaign = get_campaign_from_user()
        
        if not campaign.strip():
            print("⚠️ Reklam metni boş olamaz. Tekrar deneyin.")
            continue
        
        print(f"\n📢 Reklamınız:\n\"{campaign}\"")
        
        # Persona sayısı
        count = get_persona_count()
        
        # Hedefleme modu
        mode = get_targeting_mode()
        
        manual_segments = None
        if mode == "manual":
            manual_segments = select_manual_segments()
        
        # Testi çalıştır
        run_test(campaign, count, mode, manual_segments)
        
        # Tekrar test?
        print("\n" + "-" * 70)
        again = input("🔄 Başka bir reklam test etmek ister misiniz? (e/h): ").strip().lower()
        if again != "e":
            print("\n👋 Görüşmek üzere! SimuTarget.ai'ı kullandığınız için teşekkürler.")
            break
        print("\n")

if __name__ == "__main__":
    main()