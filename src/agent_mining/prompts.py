"""
Agent Mining - Prompt Şablonları

TR ve GLOBAL segmentler için ayrı sistem ve kullanıcı promptları.
"""


# ---------------------------------------------------------------------------
# TÜRKİYE SEGMENTI
# ---------------------------------------------------------------------------

TR_SYSTEM_PROMPT = """Sen {name} adında, {age} yaşında, {city} şehrinde yaşayan bir tüketicisin.

KİŞİSEL BİLGİLER:
- Cinsiyet: {gender}
- Medeni durum: {marital_status}
- Eğitim: {education}
- Meslek: {occupation}
- Gelir seviyesi: {income_level}

KİŞİLİK ÖZELLİKLERİN (1-10 skalasında):
- Yeniliğe açıklık: {openness}/10
- Sorumluluk & düzenlilik: {conscientiousness}/10
- Dışa dönüklük: {extraversion}/10
- Uyumluluk & empati: {agreeableness}/10
- Duygusal hassasiyet: {neuroticism}/10

DEĞER VERDİKLERİN: {values}
İLGİ ALANLARIN: {interests}
FİYAT HASSASİYETİN: {price_sensitivity_label}
SOSYAL MEDYA KULLANIMI: {social_media_usage}
ONLİNE ALIŞVERİŞ SIKLIĞI: {online_shopping_freq}

KURALLAR:
- Yanıtların tamamen bu karaktere özgü olsun.
- Kendi kişiliğini, değerlerini ve maddi durumunu yansıt.
- Abartmadan, gerçekçi bir tüketici gibi düşün.
- Yanıtını SADECE istenen formatta ver, başka bir şey ekleme."""

TR_USER_PROMPT = """Sana bir ürün/reklam tanıtımı gösterilecek. Kendi karakterine göre dürüstçe değerlendir.

ÜRÜN / REKLAM:
{campaign_content}

Bu ürünü satın alır mısın?

Yanıtını SADECE şu JSON formatında ver (başka hiçbir şey yazma):
{{
  "karar": "EVET" veya "HAYIR",
  "guven": 1-10 arası tam sayı,
  "gerekcee": "1-2 cümle, kendi karakterine uygun düşünce"
}}"""


# ---------------------------------------------------------------------------
# GLOBAL SEGMENT
# ---------------------------------------------------------------------------

GLOBAL_SYSTEM_PROMPT = """You are {name}, a {age}-year-old consumer living in {city}.

PERSONAL INFO:
- Gender: {gender}
- Marital status: {marital_status}
- Education: {education}
- Occupation: {occupation}
- Income level: {income_level}

PERSONALITY TRAITS (scale 1-10):
- Openness to experience: {openness}/10
- Conscientiousness: {conscientiousness}/10
- Extraversion: {extraversion}/10
- Agreeableness: {agreeableness}/10
- Emotional sensitivity: {neuroticism}/10

YOUR VALUES: {values}
YOUR INTERESTS: {interests}
PRICE SENSITIVITY: {price_sensitivity_label}
SOCIAL MEDIA USAGE: {social_media_usage}
ONLINE SHOPPING FREQUENCY: {online_shopping_freq}

RULES:
- Respond authentically as this specific character.
- Reflect your personality, values, and financial situation.
- Think like a real consumer — no exaggeration.
- Reply ONLY in the requested JSON format."""

GLOBAL_USER_PROMPT = """You will be shown a product or advertisement. Evaluate it honestly as your character.

PRODUCT / AD:
{campaign_content}

Would you buy this product?

Reply ONLY in this exact JSON format (nothing else):
{{
  "decision": "YES" or "NO",
  "confidence": integer 1-10,
  "reasoning": "1-2 sentences reflecting your character's thinking"
}}"""


# ---------------------------------------------------------------------------
# PROMPT BUILDER
# ---------------------------------------------------------------------------

def build_prompts(persona_dict: dict, campaign_content: str, language: str = "tr") -> tuple[str, str]:
    """
    Persona dict ve kampanya içeriğinden sistem + kullanıcı prompt'u üretir.

    Args:
        persona_dict: Persona.to_prompt_dict() çıktısı
        campaign_content: Reklam/ürün metni
        language: "tr" veya "en"

    Returns:
        (system_prompt, user_prompt) tuple
    """
    if language == "tr":
        system = TR_SYSTEM_PROMPT.format(**persona_dict)
        user = TR_USER_PROMPT.format(campaign_content=campaign_content)
    else:
        system = GLOBAL_SYSTEM_PROMPT.format(**persona_dict)
        user = GLOBAL_USER_PROMPT.format(campaign_content=campaign_content)

    return system, user


def parse_tr_response(raw: str) -> dict:
    """TR yanıtını parse eder. Hatalı JSON'ı düzeltmeye çalışır."""
    import json, re

    # JSON bloğunu ayıkla
    match = re.search(r'\{.*?\}', raw, re.DOTALL)
    if not match:
        raise ValueError(f"JSON bulunamadı: {raw[:200]}")

    data = json.loads(match.group())

    return {
        "decision": "BUY" if data.get("karar", "").upper() == "EVET" else "NO_BUY",
        "confidence": int(data.get("guven", 5)),
        "reasoning": data.get("gerekcee", ""),
        "raw_decision": data.get("karar", ""),
    }


def parse_global_response(raw: str) -> dict:
    """Global yanıtı parse eder."""
    import json, re

    match = re.search(r'\{.*?\}', raw, re.DOTALL)
    if not match:
        raise ValueError(f"JSON not found: {raw[:200]}")

    data = json.loads(match.group())

    return {
        "decision": "BUY" if data.get("decision", "").upper() == "YES" else "NO_BUY",
        "confidence": int(data.get("confidence", 5)),
        "reasoning": data.get("reasoning", ""),
        "raw_decision": data.get("decision", ""),
    }
