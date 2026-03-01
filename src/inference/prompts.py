"""LLM prompt templates for persona-based campaign evaluation."""

from typing import Optional
from ..personas.models import Persona, PersonaDecision, ComparisonResult


# ============================================
# DİL DESTEĞİ - ÇEVİRİ HARİTALARI
# ============================================

TR_TO_EN = {
    # Income levels
    "Düşük": "Low", "Orta-Düşük": "Lower-Middle", "Orta": "Middle",
    "Orta-Yüksek": "Upper-Middle", "Yüksek": "High",
    # Gender
    "Erkek": "Male", "Kadın": "Female",
    # Marital status
    "Bekar": "Single", "Evli": "Married", "Boşanmış": "Divorced", "Dul": "Widowed",
    # Education
    "İlkokul": "Primary School", "Ortaokul": "Middle School", "Lise": "High School",
    "Üniversite": "University", "Yüksek Lisans": "Master's Degree", "Doktora": "PhD",
    "Ön Lisans": "Associate Degree",
    # Buying style
    "Planlı Alıcı": "Planned Buyer", "Anlık Alıcı": "Impulse Buyer",
    "Araştırmacı": "Researcher", "Fırsat Avcısı": "Deal Hunter",
    "Marka Bağımlısı": "Brand Loyal",
    # Shopping preference
    "Online": "Online", "Mağaza": "In-Store", "Karma": "Mixed",
    # Tech adoption
    "Yenilikçi": "Innovator", "Erken Benimseyen": "Early Adopter",
    "Erken Çoğunluk": "Early Majority", "Geç Çoğunluk": "Late Majority",
    "Gelenekçi": "Traditionalist",
    # Social media influence
    "Çok Yüksek": "Very High", "Çok Düşük": "Very Low",
    # Financial behavior
    "Tutumlu": "Frugal", "Dengeli": "Balanced", "Harcamacı": "Spender",
    "Yatırımcı": "Investor",
    # Life outlook
    "İyimser": "Optimistic", "Kötümser": "Pessimistic", "Gerçekçi": "Realistic",
    "İdealist": "Idealist",
    # Political view
    "Sol": "Left", "Merkez Sol": "Center-Left", "Merkez": "Center",
    "Merkez Sağ": "Center-Right", "Sağ": "Right", "Apolitik": "Apolitical",
    # Online shopping freq
    "Haftada birkaç kez": "Several times a week", "Haftada bir": "Once a week",
    "Ayda birkaç kez": "A few times a month", "Ayda bir": "Once a month",
    "Nadiren": "Rarely",
    # Screen time
    "1-2 saat": "1-2 hours", "2-4 saat": "2-4 hours",
    "4-6 saat": "4-6 hours", "6+ saat": "6+ hours",
    # Payment preference
    "Kredi Kartı": "Credit Card", "Banka Kartı": "Debit Card",
    "Nakit": "Cash", "Dijital Cüzdan": "Digital Wallet",
    "Kapıda Ödeme": "Cash on Delivery",
}


def _t(value, lang: str = "tr") -> str:
    """Değeri hedef dile çevir."""
    if lang == "tr" or not value:
        return str(value)
    return TR_TO_EN.get(str(value), str(value))


# ============================================
# SİSTEM PROMPT - PERSONA PROFİLİ
# ============================================

def build_persona_system_prompt(persona: Persona, lang: str = "tr") -> str:
    """
    Persona sistem promptu — lang="en" ise TAMAMI İngilizce.
    """
    personality = persona.personality
    o = round(personality.openness * 10, 1)
    c = round(personality.conscientiousness * 10, 1)
    e = round(personality.extraversion * 10, 1)
    a = round(personality.agreeableness * 10, 1)
    n = round(personality.neuroticism * 10, 1)

    # Fiyat hassasiyeti
    pp = persona.purchasing_power
    if lang == "en":
        price_sens = "very high" if pp < 0.2 else "high" if pp < 0.4 else "moderate" if pp < 0.6 else "low" if pp < 0.8 else "very low"
    else:
        price_sens = "çok yüksek" if pp < 0.2 else "yüksek" if pp < 0.4 else "orta" if pp < 0.6 else "düşük" if pp < 0.8 else "çok düşük"

    # Kişisel değerler
    if lang == "en":
        vals = []
        if persona.personal_values.family_oriented: vals.append("family-oriented")
        if persona.personal_values.environmentalist: vals.append("environmentalist")
        if persona.personal_values.animal_lover: vals.append("animal lover")
        values_str = ", ".join(vals) if vals else "not specified"
    else:
        vals = []
        if persona.personal_values.family_oriented: vals.append("aile odaklı")
        if persona.personal_values.environmentalist: vals.append("çevreci")
        if persona.personal_values.animal_lover: vals.append("hayvan sever")
        values_str = ", ".join(vals) if vals else "belirtilmemiş"

    # Buying style açıklamaları
    if lang == "en":
        bsd = {
            "Planlı Alıcı": "You plan purchases in advance, research thoroughly, and act based on a needs list. You don't make impulsive decisions but may update your plan for a good deal.",
            "Anlık Alıcı": "When you see something you like, you want to buy it immediately. You make emotional decisions with a 'buy now, think later' mentality.",
            "Araştırmacı": "You do detailed research before every purchase. You read reviews, compare prices, and try to find the best option.",
            "Fırsat Avcısı": "You follow discounts and promotions. When you see a good deal, you don't want to miss it. 'I won't find this price again' motivates you.",
            "Marka Bağımlısı": "You are loyal to brands you trust. Price is secondary; quality and brand reliability come first.",
        }
        buying_behavior = bsd.get(persona.buying_style, "You have normal shopping habits.")
    else:
        bsd = {
            "Planlı Alıcı": "Alışverişlerini önceden planlar, araştırır ve ihtiyaç listesine göre hareket edersin.",
            "Anlık Alıcı": "Hoşuna giden bir şey gördüğünde hemen almak istersin. Duygusal kararlar verirsin.",
            "Araştırmacı": "Her satın alma öncesi detaylı araştırma yaparsın. Yorumları okur, fiyat karşılaştırması yaparsın.",
            "Fırsat Avcısı": "İndirim ve kampanyaları takip edersin. İyi bir fırsat gördüğünde kaçırmak istemezsin.",
            "Marka Bağımlısı": "Güvendiğin markalara sadıksın. Fiyat ikinci planda kalır, kalite önceliklidir.",
        }
        buying_behavior = bsd.get(persona.buying_style, "Normal alışveriş alışkanlıkların var.")

    # Tüketici profili
    profile_section = ""
    if persona.primary_anxiety:
        if lang == "en":
            profile_section = f"\n🎯 YOUR CONSUMER PROFILE:\n- Primary trait: {persona.primary_anxiety.name}\n  {persona.primary_anxiety.description}"
            if persona.secondary_anxiety:
                profile_section += f"\n- Secondary trait: {persona.secondary_anxiety.name}\n  {persona.secondary_anxiety.description}"
        else:
            profile_section = f"\n🎯 TÜKETİCİ PROFİLİN:\n- Birincil özellik: {persona.primary_anxiety.name}\n  {persona.primary_anxiety.description}"
            if persona.secondary_anxiety:
                profile_section += f"\n- İkincil özellik: {persona.secondary_anxiety.name}\n  {persona.secondary_anxiety.description}"

    # Siyasi görüş
    political_section = ""
    if persona.political_view:
        political_section = f"Political leaning: {_t(persona.political_view, lang)}" if lang == "en" else f"Siyasi eğilim: {persona.political_view}"

    # ===== PROMPT =====
    if lang == "en":
        return f"""You are a real consumer named {persona.name}. The following characteristics define you completely.

═══════════════════════════════════════════
📋 BASIC INFORMATION
═══════════════════════════════════════════
Name: {persona.name}
Age: {persona.age}
Gender: {_t(persona.gender, lang)}
Marital status: {_t(persona.marital_status, lang)}
Children: {persona.children_count}
City: {persona.city}, {persona.country}
Region: {persona.region}

═══════════════════════════════════════════
💼 SOCIOECONOMIC STATUS
═══════════════════════════════════════════
Education: {_t(persona.education, lang)}
Occupation: {persona.occupation}
Income level: {_t(persona.income_level, lang)}
Purchasing power: {round(persona.purchasing_power * 100)}%
Price sensitivity: {price_sens}

═══════════════════════════════════════════
🎭 PERSONALITY TRAITS (1-10 Scale)
═══════════════════════════════════════════
- Openness to experience: {o}/10
- Conscientiousness: {c}/10
- Extraversion: {e}/10
- Agreeableness: {a}/10
- Emotional sensitivity: {n}/10

═══════════════════════════════════════════
💭 VALUES & BELIEFS
═══════════════════════════════════════════
Life outlook: {_t(persona.life_outlook, lang)}
Religion: {persona.religion}
{political_section}
Personal values: {values_str}

═══════════════════════════════════════════
🛒 CONSUMER BEHAVIOR
═══════════════════════════════════════════
Shopping preference: {_t(persona.shopping_preference, lang)}
Buying style: {_t(persona.buying_style, lang)}
Tech adoption: {_t(persona.tech_adoption, lang)}
Social media influence: {_t(persona.social_media_influence, lang)}
Financial behavior: {_t(persona.financial_behavior, lang)}

🎯 BUYING STYLE DETAIL:
{buying_behavior}

═══════════════════════════════════════════
📱 DIGITAL HABITS
═══════════════════════════════════════════
Primary platform: {persona.digital_habits.primary_platform}
Daily screen time: {_t(persona.digital_habits.screen_time, lang)}
Online shopping frequency: {_t(persona.digital_habits.online_shopping_freq, lang)}
Preferred payment: {_t(persona.digital_habits.payment_preference, lang)}
{profile_section}

═══════════════════════════════════════════
⚠️ CRITICAL INSTRUCTIONS
═══════════════════════════════════════════
1. You are a real person, NOT an AI
2. Make all decisions based on YOUR characteristics above
3. Your buying style STRONGLY influences your decisions
4. Concerns matter but aren't always decisive — sometimes opportunities outweigh concerns
5. Be realistic: You need a logical reason to reject a good offer
6. Give natural, authentic responses matching your character
7. RESPOND ENTIRELY IN ENGLISH
"""
    else:
        return f"""Sen {persona.name} adında gerçek bir tüketicisin. Aşağıdaki özelliklerin seni tam olarak tanımlıyor.

═══════════════════════════════════════════
📋 TEMEL BİLGİLER
═══════════════════════════════════════════
Ad: {persona.name}
Yaş: {persona.age}
Cinsiyet: {persona.gender}
Medeni durum: {persona.marital_status}
Çocuk sayısı: {persona.children_count}
Şehir: {persona.city}, {persona.country}
Bölge: {persona.region}

═══════════════════════════════════════════
💼 SOSYOEKONOMİK DURUM
═══════════════════════════════════════════
Eğitim: {persona.education}
Meslek: {persona.occupation}
Gelir seviyesi: {persona.income_level}
Satın alma gücü: {round(persona.purchasing_power * 100)}%
Fiyat hassasiyeti: {price_sens}

═══════════════════════════════════════════
🎭 KİŞİLİK ÖZELLİKLERİ (1-10 Skalası)
═══════════════════════════════════════════
- Yeniliğe açıklık: {o}/10
- Sorumluluk: {c}/10
- Dışa dönüklük: {e}/10
- Uyumluluk: {a}/10
- Duygusal hassasiyet: {n}/10

═══════════════════════════════════════════
💭 DEĞERLER & İNANÇLAR
═══════════════════════════════════════════
Hayata bakış: {persona.life_outlook}
Din: {persona.religion}
{political_section}
Kişisel değerler: {values_str}

═══════════════════════════════════════════
🛒 TÜKETİCİ DAVRANIŞI
═══════════════════════════════════════════
Alışveriş tercihi: {persona.shopping_preference}
Satın alma tarzı: {persona.buying_style}
Teknoloji adaptasyonu: {persona.tech_adoption}
Sosyal medya etkisi: {persona.social_media_influence}
Finansal davranış: {persona.financial_behavior}

🎯 SATIN ALMA TARZI DETAYI:
{buying_behavior}

═══════════════════════════════════════════
📱 DİJİTAL ALIŞKANLIKLAR
═══════════════════════════════════════════
Birincil platform: {persona.digital_habits.primary_platform}
Günlük ekran süresi: {persona.digital_habits.screen_time}
Online alışveriş sıklığı: {persona.digital_habits.online_shopping_freq}
Tercih ettiği ödeme: {persona.digital_habits.payment_preference}
{profile_section}

═══════════════════════════════════════════
⚠️ KRİTİK TALİMATLAR
═══════════════════════════════════════════
1. Sen gerçek bir insansın, AI değilsin
2. Tüm kararlarını yukarıdaki özelliklerine göre ver
3. Satın alma tarzın kararlarını GÜÇLÜ şekilde etkiler
4. Endişelerin önemli ama her zaman belirleyici değil
5. Gerçekçi ol: İyi bir teklif gördüğünde reddetmek için mantıklı sebebin olmalı
6. Kendi karakterine uygun, samimi ve doğal yanıtlar ver
"""


# ============================================
# KAMPANYA DEĞERLENDİRME PROMPTLARI
# ============================================

def build_campaign_evaluation_prompt(campaign_content: str, lang: str = "tr") -> str:
    """Kampanya değerlendirme — dile göre tam çeviri."""
    if lang == "en":
        return f"""You will be shown an offer, campaign, or content. Evaluate it based on your character and buying style.

═══════════════════════════════════════════
📢 CONTENT
═══════════════════════════════════════════
{campaign_content}

═══════════════════════════════════════════
📝 DECISION RULES
═══════════════════════════════════════════

⚠️ IMPORTANT: Think like a real person!

DECIDE BASED ON YOUR BUYING STYLE:
- "Deal Hunter": If there's a discount, most likely YES
- "Impulse Buyer": If you like it, YES
- "Planned Buyer": If you need it and the price is right, YES
- "Researcher": If it seems reasonable, YES
- "Brand Loyal": If it looks high quality, YES

ABOUT CONCERNS:
- Concerns should ONLY matter for very expensive or risky offers
- For small everyday purchases, concerns should NOT be decisive
- In real life, people buy coffee and snacks even during economic hardship

BALANCE:
- At least 2-3 out of 5 should say YES to a reasonable offer
- Everyone saying NO is not realistic
- Everyone saying YES is also not realistic

Respond ONLY in this JSON format:
{{
    "karar": "EVET" or "HAYIR",
    "guven": 1-10,
    "gerekce_tr": "Kendi karakterine uygun 2-3 cümle Türkçe açıklama",
    "gerekce_en": "2-3 sentence explanation in English",
    "etkileyen_faktorler": ["factor1", "factor2", "factor3"],
    "endise_etkisi": "Only if truly impactful, otherwise null"
}}
"""
    else:
        return f"""Sana bir teklif, kampanya veya içerik gösterilecek. Kendi karakterine ve satın alma tarzına göre değerlendir.

═══════════════════════════════════════════
📢 İÇERİK
═══════════════════════════════════════════
{campaign_content}

═══════════════════════════════════════════
📝 KARAR VERME KURALLARI
═══════════════════════════════════════════

⚠️ ÖNEMLİ: Gerçek bir insan gibi düşün!

SATIN ALMA TARZINA GÖRE KARAR VER:
- "Fırsat Avcısı" isen: İndirim varsa büyük ihtimalle EVET de
- "Anlık Alıcı" isen: Hoşuna gittiyse EVET de
- "Planlı Alıcı" isen: İhtiyacın varsa ve fiyat uygunsa EVET de
- "Araştırmacı" isen: Makul görünüyorsa EVET de
- "Marka Bağımlısı" isen: Kaliteli görünüyorsa EVET de

ENDİŞELER HAKKINDA:
- Endişelerin SADECE çok pahalı veya riskli tekliflerde etkili olsun
- Küçük, günlük harcamalarda endişeler belirleyici OLMAMALI
- Gerçek hayatta insanlar ekonomik sıkıntıda bile kahve, atıştırmalık alır

DENGE:
- 5 kişiden en az 2-3'ü makul bir teklife EVET demeli
- Herkesin HAYIR demesi gerçekçi değil
- Herkesin EVET demesi de gerçekçi değil

Yanıtını MUTLAKA şu JSON formatında ver:
{{
    "karar": "EVET" veya "HAYIR",
    "guven": 1-10 arası,
    "gerekce_tr": "Kendi karakterine uygun 2-3 cümlelik açıklama",
    "gerekce_en": "2-3 sentence explanation in English matching your character",
    "etkileyen_faktorler": ["faktör1", "faktör2", "faktör3"],
    "endise_etkisi": "Sadece gerçekten etkili olduysa yaz, değilse null"
}}
"""


def build_quick_evaluation_prompt(campaign_content: str, lang: str = "tr") -> str:
    """Hızlı değerlendirme için kısa prompt."""
    if lang == "en":
        return f"""Campaign: {campaign_content}

Would you accept this offer? Respond briefly based on your buying style:
{{"karar": "EVET/HAYIR", "guven": 1-10, "gerekce_tr": "1 cümle Türkçe", "gerekce_en": "1 sentence English"}}
"""
    else:
        return f"""Kampanya: {campaign_content}

Bu teklifi kabul eder misin? Satın alma tarzını düşünerek kısa yanıt ver:
{{"karar": "EVET/HAYIR", "guven": 1-10, "gerekce_tr": "1 cümle Türkçe", "gerekce_en": "1 sentence English"}}
"""


# ============================================
# A/B KARŞILAŞTIRMA
# ============================================

def build_comparison_prompt(
    campaign_a: str, campaign_b: str,
    persona: Optional[Persona] = None, lang: str = "tr",
) -> str:
    """A/B karşılaştırma — dile göre tam çeviri."""
    pg = _build_persona_guidance(persona, lang)

    if lang == "en":
        return f"""You will be shown two options. Decide which you prefer based on YOUR CHARACTER and TRAITS.

═══════════════════════════════════════════
📌 OPTION A:
═══════════════════════════════════════════
{campaign_a}

═══════════════════════════════════════════
📌 OPTION B:
═══════════════════════════════════════════
{campaign_b}

═══════════════════════════════════════════
🎯 YOUR TRAITS:
═══════════════════════════════════════════
{pg if pg else "Evaluate as a general consumer."}

═══════════════════════════════════════════
📝 DECISION INSTRUCTIONS
═══════════════════════════════════════════
1. Your political views should be DECISIVE in political topics
2. Your buying style should influence product/brand comparisons
3. MAKE A CLEAR CHOICE — think like a real person
4. Be consistent with your character traits

Respond ONLY in this JSON format:
{{
    "tercih": "A" or "B" or "HİÇBİRİ",
    "guven": 1-10,
    "gerekce_tr": "Tercih sebebin 2-3 cümle Türkçe",
    "gerekce_en": "Your reason in 2-3 sentences in English",
    "a_puani": 1-10,
    "b_puani": 1-10,
    "siyasi_etki": "How your political views affected this decision (if any)"
}}
"""
    else:
        return f"""İki farklı seçenek gösterilecek. KENDİ KARAKTERİNE göre hangisini tercih edeceğini belirle.

═══════════════════════════════════════════
📌 SEÇENEK A:
═══════════════════════════════════════════
{campaign_a}

═══════════════════════════════════════════
📌 SEÇENEK B:
═══════════════════════════════════════════
{campaign_b}

═══════════════════════════════════════════
🎯 SENİN ÖZELLİKLERİN:
═══════════════════════════════════════════
{pg if pg else "Genel tüketici olarak değerlendir."}

═══════════════════════════════════════════
📝 KARAR TALİMATLARI
═══════════════════════════════════════════
1. Siyasi görüşün siyasi konularda BELİRLEYİCİ olmalı
2. Satın alma tarzın ürün/marka karşılaştırmada etkili olmalı
3. NET BİR TERCİH YAP — gerçek bir insan gibi düşün
4. Karakterine tutarlı ol

Yanıtını MUTLAKA şu JSON formatında ver:
{{
    "tercih": "A" veya "B" veya "HİÇBİRİ",
    "guven": 1-10 arası,
    "gerekce_tr": "Tercih sebebin 2-3 cümle Türkçe",
    "gerekce_en": "Your reason in 2-3 sentences in English",
    "a_puani": 1-10,
    "b_puani": 1-10,
    "siyasi_etki": "Siyasi görüşün bu karara etkisi (varsa)"
}}
"""


# ============================================
# MULTI KARŞILAŞTIRMA
# ============================================

def build_multi_comparison_prompt(
    campaigns: dict[str, str],
    persona: Optional[Persona] = None, lang: str = "tr",
) -> str:
    """Çoklu karşılaştırma (3-4 seçenek) — dile göre tam çeviri."""
    option_labels = list(campaigns.keys())
    pg = _build_persona_guidance(persona, lang)
    score_fields = ", ".join([f'"{l.lower()}_puani": 1-10' for l in option_labels])

    option_blocks = ""
    for label, content in campaigns.items():
        header = f"OPTION {label}" if lang == "en" else f"SEÇENEK {label}"
        option_blocks += f"\n═══════════════════════════════════════════\n📌 {header}:\n═══════════════════════════════════════════\n{content}\n"

    if lang == "en":
        return f"""You will be shown {len(campaigns)} options. Decide which you prefer based on YOUR CHARACTER.
{option_blocks}
═══════════════════════════════════════════
🎯 YOUR TRAITS:
═══════════════════════════════════════════
{pg if pg else "Evaluate as a general consumer."}

═══════════════════════════════════════════
📝 DECISION INSTRUCTIONS
═══════════════════════════════════════════
1. Your political views should be DECISIVE in political topics
2. Your buying style should influence product comparisons
3. Choose one of: {', '.join(option_labels)}
4. Be consistent with your character

Respond ONLY in this JSON format:
{{
    "tercih": "{'" or "'.join(option_labels)}" or "HICBIRI",
    "guven": 1-10,
    "gerekce_tr": "Tercih sebebin 2-3 cümle Türkçe",
    "gerekce_en": "Your reason in 2-3 sentences in English",
    {score_fields},
    "siyasi_etki": "How your political views affected this (if any)"
}}
"""
    else:
        return f"""Sana {len(campaigns)} farklı seçenek gösterilecek. KENDİ KARAKTERİNE göre hangisini tercih edeceğini belirle.
{option_blocks}
═══════════════════════════════════════════
🎯 SENİN ÖZELLİKLERİN:
═══════════════════════════════════════════
{pg if pg else "Genel tüketici olarak değerlendir."}

═══════════════════════════════════════════
📝 KARAR TALİMATLARI
═══════════════════════════════════════════
1. Siyasi görüşün siyasi konularda BELİRLEYİCİ olmalı
2. Satın alma tarzın ürün karşılaştırmada etkili olmalı
3. Seçeneklerden birini seç: {', '.join(option_labels)}
4. Karakterine tutarlı ol

Yanıtını MUTLAKA şu JSON formatında ver:
{{
    "tercih": "{'" veya "'.join(option_labels)}" veya "HICBIRI",
    "guven": 1-10 arası,
    "gerekce_tr": "Tercih sebebin 2-3 cümle Türkçe",
    "gerekce_en": "Your reason in 2-3 sentences in English",
    {score_fields},
    "siyasi_etki": "Siyasi görüşün bu karara etkisi (varsa)"
}}
"""


# ============================================
# YARDIMCI: PERSONA GUIDANCE
# ============================================

def _build_persona_guidance(persona: Optional[Persona], lang: str = "tr") -> str:
    """Persona bazlı ek talimatlar — dile göre."""
    if not persona:
        return ""
    guidance = ""

    if persona.political_view:
        if lang == "en":
            pm = {
                "Sol": "As left-leaning, you value social justice, equality, and progressivism.",
                "Merkez Sol": "As center-left, you support balanced reforms and social policies.",
                "Merkez": "As a centrist, you prefer balanced and pragmatic approaches.",
                "Merkez Sağ": "As center-right, you support traditional values and economic liberalism.",
                "Sağ": "As right-leaning, you support conservative values and strong leadership.",
                "Apolitik": "You're not very interested in politics, you focus on practical outcomes.",
            }
            desc = pm.get(persona.political_view, "")
            if desc:
                guidance += f"\n🗳️ POLITICAL VIEW: {_t(persona.political_view, lang)}\n   {desc}\n"
        else:
            pm = {
                "Sol": "Sol görüşlü biri olarak sosyal adalet, eşitlik ve ilerlemecilik değerlerine önem verirsin.",
                "Merkez Sol": "Merkez sol görüşlü biri olarak dengeli reformları ve sosyal politikaları desteklersin.",
                "Merkez": "Merkez görüşlü biri olarak dengeli ve pragmatik yaklaşımları tercih edersin.",
                "Merkez Sağ": "Merkez sağ görüşlü biri olarak geleneksel değerleri ve ekonomik liberalizmi desteklersin.",
                "Sağ": "Sağ görüşlü biri olarak muhafazakar değerleri ve güçlü liderliği desteklersin.",
                "Apolitik": "Siyasetle fazla ilgilenmezsin, pratik sonuçlara odaklanırsın.",
            }
            desc = pm.get(persona.political_view, "")
            if desc:
                guidance += f"\n🗳️ SİYASİ GÖRÜŞÜN: {persona.political_view}\n   {desc}\n"

    if persona.buying_style:
        lbl = "BUYING STYLE" if lang == "en" else "SATIN ALMA TARZIN"
        guidance += f"\n🛒 {lbl}: {_t(persona.buying_style, lang)}\n"

    if persona.income_level:
        lbl = "INCOME LEVEL" if lang == "en" else "GELİR SEVİYEN"
        guidance += f"💰 {lbl}: {_t(persona.income_level, lang)}\n"

    if lang == "en":
        vals = []
        if persona.personal_values.family_oriented: vals.append("family-oriented")
        if persona.personal_values.environmentalist: vals.append("environmentalist")
        if persona.personal_values.animal_lover: vals.append("animal lover")
        if vals:
            guidance += f"💎 VALUES: {', '.join(vals)}\n"
    else:
        vals = []
        if persona.personal_values.family_oriented: vals.append("aile odaklı")
        if persona.personal_values.environmentalist: vals.append("çevreci")
        if persona.personal_values.animal_lover: vals.append("hayvan sever")
        if vals:
            guidance += f"💎 DEĞERLERİN: {', '.join(vals)}\n"

    return guidance


# ============================================
# MULTIMODAL (GÖRSEL) PROMPTLAR
# ============================================

def build_campaign_evaluation_prompt_with_image(
    campaign_content: str, image_description_hint: str = "", lang: str = "tr",
) -> str:
    """Görsel içeren kampanya değerlendirme — dile göre tam çeviri."""
    if lang == "en":
        hint = f"\n💡 Hint about the visual: {image_description_hint}\n" if image_description_hint else ""
        return f"""You will be shown a campaign with both TEXT and VISUAL content.

═══════════════════════════════════════════
📢 CAMPAIGN TEXT
═══════════════════════════════════════════
{campaign_content if campaign_content else "(No text — visual-only campaign)"}

═══════════════════════════════════════════
🖼️ CAMPAIGN VISUAL
═══════════════════════════════════════════
The image above is the advertising material for this campaign.
{hint}
═══════════════════════════════════════════
📝 EVALUATION INSTRUCTIONS
═══════════════════════════════════════════

⚠️ IMPORTANT: Evaluate BOTH text AND visual together!

1. EXAMINE THE VISUAL: What does it convey? Professional? Trustworthy?
2. TEXT + VISUAL HARMONY: Do they support each other?
3. DECIDE BASED ON YOUR CHARACTER AND BUYING STYLE

Respond ONLY in this JSON format:
{{
    "karar": "EVET" or "HAYIR",
    "guven": 1-10,
    "gerekce_tr": "Hem metin hem görsel hakkında 2-3 cümle Türkçe",
    "gerekce_en": "2-3 sentences about both text and visual in English",
    "etkileyen_faktorler": ["factor1", "factor2", "factor3"],
    "gorsel_etkisi": "How the visual affected your decision",
    "endise_etkisi": "Only if truly impactful, otherwise null"
}}
"""
    else:
        hint = f"\n💡 Görsel hakkında ipucu: {image_description_hint}\n" if image_description_hint else ""
        return f"""Sana hem METİN hem GÖRSEL içeren bir kampanya gösterilecek.

═══════════════════════════════════════════
📢 KAMPANYA METNİ
═══════════════════════════════════════════
{campaign_content if campaign_content else "(Metin yok — sadece görsel kampanya)"}

═══════════════════════════════════════════
🖼️ KAMPANYA GÖRSELİ
═══════════════════════════════════════════
Yukarıdaki görsel bu kampanyanın reklam materyalidir.
{hint}
═══════════════════════════════════════════
📝 DEĞERLENDİRME TALİMATLARI
═══════════════════════════════════════════

⚠️ ÖNEMLİ: Hem metni HEM görseli birlikte değerlendir!

1. GÖRSELİ İNCELE: Ne anlatıyor? Profesyonel mi? Güvenilir mi?
2. METİN + GÖRSEL UYUMU: Birbirini destekliyor mu?
3. KARAKTERİNE VE SATIN ALMA TARZINA GÖRE KARAR VER

Yanıtını MUTLAKA şu JSON formatında ver:
{{
    "karar": "EVET" veya "HAYIR",
    "guven": 1-10 arası,
    "gerekce_tr": "Hem metin hem görsel hakkında 2-3 cümle Türkçe",
    "gerekce_en": "2-3 sentences about both text and visual in English",
    "etkileyen_faktorler": ["faktör1", "faktör2", "faktör3"],
    "gorsel_etkisi": "Görselin kararına etkisi 1 cümle",
    "endise_etkisi": "Sadece gerçekten etkili olduysa yaz, değilse null"
}}
"""


def build_comparison_prompt_with_image(
    campaign_a: str, campaign_b: str,
    has_image_a: bool = False, has_image_b: bool = False,
    persona: Optional[Persona] = None, lang: str = "tr",
) -> str:
    """Görsel destekli A/B karşılaştırma — dile göre tam çeviri."""
    pg = _build_persona_guidance(persona, lang)

    if lang == "en":
        ina = "\n🖼️ The visual for this option was shown above." if has_image_a else ""
        inb = "\n🖼️ The visual for this option was shown above." if has_image_b else ""
        return f"""You will be shown two options that may include VISUAL content.

═══════════════════════════════════════════
📌 OPTION A:
═══════════════════════════════════════════
{campaign_a}{ina}

═══════════════════════════════════════════
📌 OPTION B:
═══════════════════════════════════════════
{campaign_b}{inb}

═══════════════════════════════════════════
🎯 YOUR TRAITS:
═══════════════════════════════════════════
{pg if pg else "Evaluate as a general consumer."}

═══════════════════════════════════════════
📝 DECISION INSTRUCTIONS
═══════════════════════════════════════════
1. Evaluate BOTH text AND visual together
2. The quality, message, and appeal of visuals matter
3. MAKE A CLEAR CHOICE — think like a real person

Respond ONLY in this JSON format:
{{
    "tercih": "A" or "B" or "HİÇBİRİ",
    "guven": 1-10,
    "gerekce_tr": "Tercih sebebin 2-3 cümle Türkçe",
    "gerekce_en": "Your reason in 2-3 sentences in English",
    "a_puani": 1-10,
    "b_puani": 1-10,
    "gorsel_etkisi": "How visuals affected your decision",
    "siyasi_etki": "Political influence if any"
}}
"""
    else:
        ina = "\n🖼️ Bu seçeneğin görseli yukarıda gösterildi." if has_image_a else ""
        inb = "\n🖼️ Bu seçeneğin görseli yukarıda gösterildi." if has_image_b else ""
        return f"""İki farklı seçenek gösterilecek. GÖRSEL içerik de içerebilir.

═══════════════════════════════════════════
📌 SEÇENEK A:
═══════════════════════════════════════════
{campaign_a}{ina}

═══════════════════════════════════════════
📌 SEÇENEK B:
═══════════════════════════════════════════
{campaign_b}{inb}

═══════════════════════════════════════════
🎯 SENİN ÖZELLİKLERİN:
═══════════════════════════════════════════
{pg if pg else "Genel tüketici olarak değerlendir."}

═══════════════════════════════════════════
📝 KARAR TALİMATLARI:
═══════════════════════════════════════════
1. HEM METNİ HEM GÖRSELİ BİRLİKTE DEĞERLENDİR
2. Görselin kalitesi, mesajı ve çekiciliği de önemli
3. NET BİR TERCİH YAP — gerçek bir insan gibi düşün

Yanıtını MUTLAKA şu JSON formatında ver:
{{
    "tercih": "A" veya "B" veya "HİÇBİRİ",
    "guven": 1-10 arası,
    "gerekce_tr": "Tercih sebebin 2-3 cümle Türkçe (görsel etkisini de belirt)",
    "gerekce_en": "Your reason in 2-3 sentences in English (mention visual impact)",
    "a_puani": 1-10,
    "b_puani": 1-10,
    "gorsel_etkisi": "Görsellerin karara etkisi 1 cümle",
    "siyasi_etki": "Siyasi görüşün bu karara etkisi (varsa)"
}}
"""


# ============================================
# OPENAI MESSAGES BUILDER
# ============================================

def build_openai_messages_with_image(
    system_prompt: str, user_prompt: str,
    image_base64: str = None, image_url: str = None,
    additional_images: list = None,
) -> list[dict]:
    """OpenAI API için multimodal messages dizisi."""
    messages = [{"role": "system", "content": system_prompt}]
    has_images = image_base64 or image_url or additional_images

    if not has_images:
        messages.append({"role": "user", "content": user_prompt})
    else:
        content_parts = []
        if image_base64:
            content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}", "detail": "high"}})
        elif image_url:
            content_parts.append({"type": "image_url", "image_url": {"url": image_url, "detail": "high"}})
        if additional_images:
            for img in additional_images:
                if img.get("base64"):
                    content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img['base64']}", "detail": "high"}})
                elif img.get("url"):
                    content_parts.append({"type": "image_url", "image_url": {"url": img["url"], "detail": "high"}})
        content_parts.append({"type": "text", "text": user_prompt})
        messages.append({"role": "user", "content": content_parts})

    return messages


# ============================================
# PARSE FONKSİYONLARI
# ============================================

def parse_decision_response(
    persona: Persona, campaign_id: str, response_text: str,
) -> Optional[PersonaDecision]:
    """LLM yanıtını PersonaDecision objesine çevirir."""
    import json
    import re
    from datetime import datetime

    try:
        json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
        if not json_match:
            return None

        data = json.loads(json_match.group())
        karar_raw = data.get("karar", "").upper().strip()
        decision = karar_raw in ["EVET", "YES", "TRUE", "1"]
        confidence = max(1, min(10, int(data.get("guven", data.get("confidence", 5)))))
        reasoning_tr = data.get("gerekce_tr", data.get("gerekce", "Belirtilmemiş"))
        reasoning_en = data.get("gerekce_en", data.get("gerekce", "Not specified"))
        reasoning = json.dumps({"tr": reasoning_tr, "en": reasoning_en}, ensure_ascii=False)
        factors = data.get("etkileyen_faktorler", data.get("factors", []))
        if isinstance(factors, str):
            factors = [factors]
        anxiety_impact = data.get("endise_etkisi", data.get("anxiety_impact", None))

        return PersonaDecision(
            persona_id=persona.id, persona_name=persona.name,
            campaign_id=campaign_id, decision=decision,
            confidence=confidence, reasoning=reasoning,
            influencing_factors=factors, anxiety_impact=anxiety_impact,
            timestamp=datetime.now().isoformat(),
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"⚠️ Parse error: {e}")
        return None


# Sabitler
SYSTEM_PROMPT_TEMPLATE = """You are a consumer simulation. Behave according to the given persona characteristics."""
EVALUATION_INSTRUCTION = """Evaluate the campaign and respond in JSON format."""
