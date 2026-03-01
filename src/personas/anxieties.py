"""Consumer profile anxieties/concerns by region."""


def get_anxieties(region: str) -> dict:
    """Get regional consumer anxieties/concerns."""
    anxiety_map = {
        "TR": TURKEY_ANXIETIES,
        "US": USA_ANXIETIES,
        "EU": EUROPE_ANXIETIES,
        "MENA": MENA_ANXIETIES,
    }
    return anxiety_map.get(region, {})


TURKEY_ANXIETIES = {
    "price_value": {
        "id": "tr_price_value",
        "name": "Fiyat-Değer Odaklı",
        "description": "Alışverişlerinde fiyat-performans dengesine çok dikkat eder. İndirimleri ve kampanyaları yakından takip eder.",
        "weight": 0.25,
        "conditions": {"income_levels": ["Düşük", "Orta-Düşük", "Orta"]},
    },
    "future_planning": {
        "id": "tr_future",
        "name": "Geleceği Planlayan",
        "description": "Tasarruf ve yatırım konusunda bilinçli. Gereksiz harcamalardan kaçınır, uzun vadeli düşünür.",
        "weight": 0.20,
        "conditions": {"age_range": [30, 65]},
    },
    "quality_seeker": {
        "id": "tr_quality",
        "name": "Kalite Arayanı",
        "description": "Ucuz ama kalitesiz ürünler yerine kaliteli ürünlere yatırım yapmayı tercih eder.",
        "weight": 0.15,
        "conditions": {"income_levels": ["Orta-Yüksek", "Yüksek"]},
    },
    "family_protector": {
        "id": "tr_family",
        "name": "Aile Koruyucusu",
        "description": "Ailesi için en iyi ürünleri ve hizmetleri araştırır. Çocuklarının geleceği önceliklidir.",
        "weight": 0.20,
        "conditions": {"has_children": True},
    },
    "tech_cautious": {
        "id": "tr_tech",
        "name": "Teknoloji Temkinlisi",
        "description": "Yeni teknolojilere karşı temkinli yaklaşır, güvenilirlik ve kullanım kolaylığı arar.",
        "weight": 0.10,
        "conditions": {"age_range": [45, 80]},
    },
    "status_conscious": {
        "id": "tr_status",
        "name": "Statü Bilinçli",
        "description": "Marka ve prestij önemlidir. Sosyal çevresinde iyi bir imaj çizmek ister.",
        "weight": 0.10,
        "conditions": {"age_range": [25, 45]},
    },
}

USA_ANXIETIES = {
    "healthcare_cost": {
        "id": "us_healthcare",
        "name": "Sağlık Maliyeti Bilinçli",
        "description": "Sağlık harcamaları konusunda hassas. Sigorta kapsamını ve cepten çıkan maliyetleri göz önünde bulundurur.",
        "weight": 0.20,
        "conditions": {"age_range": [30, 80]},
    },
    "debt_aware": {
        "id": "us_debt",
        "name": "Borç Bilinçli",
        "description": "Kredi kartı borcu ve öğrenci kredisi gibi borçları yönetmeye çalışır.",
        "weight": 0.20,
        "conditions": {"age_range": [22, 45]},
    },
    "convenience_seeker": {
        "id": "us_convenience",
        "name": "Kolaylık Arayanı",
        "description": "Zaman tasarrufu ve kolaylık her şeyin önünde. Hızlı teslimat ve kolay iade önemli.",
        "weight": 0.20,
        "conditions": {},
    },
    "eco_conscious": {
        "id": "us_eco",
        "name": "Çevre Bilinçli",
        "description": "Sürdürülebilir ve çevre dostu ürünleri tercih eder. Karbon ayak izi önemli.",
        "weight": 0.15,
        "conditions": {"age_range": [18, 40]},
    },
    "privacy_focused": {
        "id": "us_privacy",
        "name": "Gizlilik Odaklı",
        "description": "Kişisel verilerinin korunmasına önem verir. Veri toplayan uygulamalara karşı temkinli.",
        "weight": 0.15,
        "conditions": {},
    },
    "retirement_planner": {
        "id": "us_retirement",
        "name": "Emeklilik Planlayıcı",
        "description": "401K ve yatırım portföyünü düşünür. Uzun vadeli finansal güvenlik öncelikli.",
        "weight": 0.10,
        "conditions": {"age_range": [35, 65]},
    },
}

EUROPE_ANXIETIES = {
    "energy_cost": {
        "id": "eu_energy",
        "name": "Enerji Maliyeti Bilinçli",
        "description": "Enerji fiyatlarını takip eder. Enerji tasarruflu ürünleri tercih eder.",
        "weight": 0.20,
        "conditions": {},
    },
    "sustainability": {
        "id": "eu_sustain",
        "name": "Sürdürülebilirlik Odaklı",
        "description": "Çevreci ve sürdürülebilir ürünlere yönelir. Organik, yerel ve adil ticaret ürünlerini tercih eder.",
        "weight": 0.25,
        "conditions": {},
    },
    "data_privacy": {
        "id": "eu_privacy",
        "name": "GDPR Bilinçli",
        "description": "Kişisel veri güvenliğine çok önem verir. GDPR haklarını bilir ve korur.",
        "weight": 0.15,
        "conditions": {},
    },
    "work_life_balance": {
        "id": "eu_balance",
        "name": "İş-Yaşam Dengecisi",
        "description": "İş-yaşam dengesini korumayı önemser. Tatil, hobi ve kişisel gelişime yatırım yapar.",
        "weight": 0.20,
        "conditions": {"age_range": [25, 55]},
    },
    "quality_tradition": {
        "id": "eu_quality",
        "name": "Kalite ve Gelenek Odaklı",
        "description": "Geleneksel kaliteye ve zanaatkarlığa değer verir. Uzun ömürlü ürünleri tercih eder.",
        "weight": 0.20,
        "conditions": {"age_range": [35, 80]},
    },
}

MENA_ANXIETIES = {
    "currency_aware": {
        "id": "mena_currency",
        "name": "Döviz Bilinçli",
        "description": "Yerel para biriminin değerini takip eder. İthal ürünlerin fiyat değişimlerine dikkat eder.",
        "weight": 0.20,
        "conditions": {},
    },
    "family_honor": {
        "id": "mena_family",
        "name": "Aile Değerleri Odaklı",
        "description": "Aile onuru ve toplumsal kabul önemlidir. Ailenin ihtiyaçlarını kendi isteklerinin önüne koyar.",
        "weight": 0.25,
        "conditions": {"has_children": True},
    },
    "luxury_aspirant": {
        "id": "mena_luxury",
        "name": "Lüks Tutkunu",
        "description": "Premium markalara ve lüks deneyimlere yönelir. Statü simgelerine değer verir.",
        "weight": 0.20,
        "conditions": {"income_levels": ["Orta-Yüksek", "Yüksek"]},
    },
    "tradition_keeper": {
        "id": "mena_tradition",
        "name": "Gelenek Koruyucusu",
        "description": "Geleneksel ve kültürel değerlere bağlıdır. Helal ürünler ve İslami finans tercih eder.",
        "weight": 0.20,
        "conditions": {},
    },
    "modernizer": {
        "id": "mena_modern",
        "name": "Modernleşmeci",
        "description": "Yeni teknolojilere ve modern yaşam tarzına açık. Gelenekle modernlik arasında denge kurar.",
        "weight": 0.15,
        "conditions": {"age_range": [18, 40]},
    },
}
