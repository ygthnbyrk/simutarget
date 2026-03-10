"""
Agent Mining - Demografik Dağılım Verileri

TR segmenti: TÜİK 2023 verilerine dayalı
Global segmenti: Worldbank / Eurostat / US Census ağırlıklı

Her dağılım (değer, ağırlık) tuple listesi olarak tanımlanmıştır.
random.choices(population, weights=weights) ile kullanılır.
"""

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# TÜRKİYE SEGMENTI
# ---------------------------------------------------------------------------

TR_AGE_DIST = [
    # (yaş_aralığı_min, yaş_aralığı_max, ağırlık)
    (18, 24, 14),   # TÜİK: ~%14 — Z kuşağı
    (25, 34, 21),   # ~%21 — Y kuşağı
    (35, 44, 18),   # ~%18 — X kuşağı
    (45, 54, 16),   # ~%16
    (55, 64, 14),   # ~%14
    (65, 75, 10),   # ~%10
    (76, 85, 7),    # ~%7
]

TR_GENDER_DIST = [
    ("Erkek", 50),
    ("Kadın", 50),
]

TR_CITY_DIST = [
    # (şehir, ağırlık) — nüfus büyüklüğüne göre
    ("İstanbul", 20),
    ("Ankara", 7),
    ("İzmir", 5),
    ("Bursa", 3),
    ("Antalya", 3),
    ("Adana", 3),
    ("Gaziantep", 3),
    ("Konya", 2),
    ("Şanlıurfa", 2),
    ("Mersin", 2),
    ("Diyarbakır", 2),
    ("Kayseri", 2),
    ("Trabzon", 2),
    ("Samsun", 2),
    ("Eskişehir", 2),
    ("Kocaeli", 2),
    ("Zonguldak", 1),
    ("Diğer", 37),
]

TR_INCOME_DIST = [
    ("Düşük", 25),           # < 17K TL/ay
    ("Orta-Düşük", 30),      # 17K-35K TL/ay
    ("Orta", 25),            # 35K-70K TL/ay
    ("Orta-Yüksek", 14),     # 70K-150K TL/ay
    ("Yüksek", 6),           # 150K+ TL/ay
]

TR_EDUCATION_DIST = [
    ("İlkokul", 15),
    ("Ortaokul", 20),
    ("Lise", 35),
    ("Üniversite", 22),
    ("Yüksek Lisans", 6),
    ("Doktora", 2),
]

TR_OCCUPATION_DIST = [
    ("Serbest Meslek", 12),
    ("Özel Sektör Çalışanı", 25),
    ("Kamu Çalışanı", 10),
    ("İşçi / Vasıfsız İşgücü", 15),
    ("Ev Hanımı / Bakım Verici", 12),
    ("Öğrenci", 10),
    ("Emekli", 8),
    ("Girişimci / İşletme Sahibi", 5),
    ("İşsiz", 3),
]

TR_MARITAL_DIST = [
    ("Bekar", 35),
    ("Evli", 55),
    ("Boşanmış / Dul", 10),
]

TR_HOUSEHOLD_SIZE_DIST = [
    (1, 10),
    (2, 18),
    (3, 22),
    (4, 28),
    (5, 14),
    (6, 8),
]

TR_VALUES_POOL = [
    "aile", "güvenlik", "dini değerler", "kariyer başarısı",
    "sosyal statü", "çevre / sürdürülebilirlik", "sağlık",
    "özgürlük / bağımsızlık", "eğitim / öğrenme",
    "topluluk / dayanışma", "lüks / konfor", "tasarruf",
    "geleneksel değerler", "modernlik / yenilik",
]

TR_INTERESTS_POOL = [
    "futbol", "dizi izleme", "yemek / mutfak", "alışveriş",
    "seyahat", "teknoloji / gadget", "sosyal medya",
    "müzik", "kitap okuma", "fitness / spor",
    "el sanatları / hobi", "oyun (video / masa)", "doğa / kamp",
    "moda / stil", "arabalar", "bahçecilik",
]

TR_BRANDS_POOL = [
    "LC Waikiki", "Migros", "BİM", "Trendyol", "Hepsiburada",
    "Apple", "Samsung", "Arçelik", "Beko", "Vestel",
    "Ülker", "Eti", "Koton", "DeFacto", "Zara",
    "Nike", "Adidas", "Puma", "Xiaomi", "Huawei",
]

TR_SOCIAL_DIST = [
    ("az", 20),
    ("orta", 45),
    ("yoğun", 35),
]

TR_ONLINE_SHOPPING_DIST = [
    ("nadiren", 25),
    ("aylık", 40),
    ("haftalık", 35),
]


# ---------------------------------------------------------------------------
# GLOBAL SEGMENT (US / EU / İngiltere / Avustralya ağırlıklı)
# ---------------------------------------------------------------------------

GLOBAL_AGE_DIST = [
    (18, 24, 13),
    (25, 34, 20),
    (35, 44, 19),
    (45, 54, 18),
    (55, 64, 16),
    (65, 80, 14),
]

GLOBAL_GENDER_DIST = [
    ("Male", 49),
    ("Female", 49),
    ("Non-binary", 2),
]

GLOBAL_CITY_DIST = [
    # US
    ("New York, USA", 8),
    ("Los Angeles, USA", 6),
    ("Chicago, USA", 4),
    ("Houston, USA", 3),
    ("Phoenix, USA", 2),
    ("San Francisco, USA", 3),
    # EU
    ("London, UK", 5),
    ("Berlin, Germany", 4),
    ("Paris, France", 4),
    ("Amsterdam, Netherlands", 2),
    ("Madrid, Spain", 3),
    ("Rome, Italy", 3),
    # Other
    ("Sydney, Australia", 3),
    ("Toronto, Canada", 3),
    ("Dubai, UAE", 2),
    ("Other", 45),
]

GLOBAL_INCOME_DIST = [
    ("Low", 15),
    ("Lower-Middle", 20),
    ("Middle", 35),
    ("Upper-Middle", 20),
    ("High", 10),
]

GLOBAL_EDUCATION_DIST = [
    ("High School", 25),
    ("Some College", 15),
    ("Bachelor's Degree", 35),
    ("Master's Degree", 18),
    ("PhD", 7),
]

GLOBAL_OCCUPATION_DIST = [
    ("Self-employed / Freelancer", 12),
    ("Corporate Employee", 28),
    ("Government / Public Sector", 8),
    ("Blue-collar Worker", 12),
    ("Homemaker / Caregiver", 8),
    ("Student", 9),
    ("Retired", 10),
    ("Entrepreneur / Business Owner", 8),
    ("Unemployed", 5),
]

GLOBAL_MARITAL_DIST = [
    ("Single", 38),
    ("Married / Partnered", 50),
    ("Divorced / Widowed", 12),
]

GLOBAL_VALUES_POOL = [
    "family", "security", "career success", "personal freedom",
    "environment / sustainability", "health & wellness", "education",
    "community", "luxury / comfort", "financial independence",
    "innovation / technology", "travel & experiences", "faith / spirituality",
    "social justice", "minimalism",
]

GLOBAL_INTERESTS_POOL = [
    "streaming / TV shows", "cooking / food", "travel", "technology",
    "sports (general)", "fitness / gym", "music", "reading / books",
    "gaming", "fashion / style", "investing / finance", "photography",
    "outdoor activities", "arts / culture", "cars",
]

GLOBAL_BRANDS_POOL = [
    "Apple", "Amazon", "Nike", "Adidas", "IKEA",
    "H&M", "Zara", "Starbucks", "Netflix", "Tesla",
    "Samsung", "Google", "Microsoft", "Costco", "Walmart",
    "Target", "Levi's", "Patagonia", "Dyson", "Spotify",
]

GLOBAL_SOCIAL_DIST = [
    ("minimal", 15),
    ("moderate", 45),
    ("heavy", 40),
]

GLOBAL_ONLINE_SHOPPING_DIST = [
    ("rarely", 15),
    ("monthly", 35),
    ("weekly", 50),
]


# ---------------------------------------------------------------------------
# HELPER: Dağılım nesneleri - factory.py'de kullanımı kolaylaştırır
# ---------------------------------------------------------------------------

@dataclass
class SegmentDistributions:
    """Bir segment için tüm demografik dağılımları bir arada tutar."""
    age_dist: list
    gender_dist: list
    city_dist: list
    income_dist: list
    education_dist: list
    occupation_dist: list
    marital_dist: list
    household_dist: list
    values_pool: list
    interests_pool: list
    brands_pool: list
    social_dist: list
    online_shopping_dist: list
    language: str        # "tr" veya "en"
    country_default: str # Prompt'ta kullanılacak ülke adı


TR_DISTRIBUTIONS = SegmentDistributions(
    age_dist=TR_AGE_DIST,
    gender_dist=TR_GENDER_DIST,
    city_dist=TR_CITY_DIST,
    income_dist=TR_INCOME_DIST,
    education_dist=TR_EDUCATION_DIST,
    occupation_dist=TR_OCCUPATION_DIST,
    marital_dist=TR_MARITAL_DIST,
    household_dist=TR_HOUSEHOLD_SIZE_DIST,
    values_pool=TR_VALUES_POOL,
    interests_pool=TR_INTERESTS_POOL,
    brands_pool=TR_BRANDS_POOL,
    social_dist=TR_SOCIAL_DIST,
    online_shopping_dist=TR_ONLINE_SHOPPING_DIST,
    language="tr",
    country_default="Türkiye",
)

GLOBAL_DISTRIBUTIONS = SegmentDistributions(
    age_dist=GLOBAL_AGE_DIST,
    gender_dist=GLOBAL_GENDER_DIST,
    city_dist=GLOBAL_CITY_DIST,
    income_dist=GLOBAL_INCOME_DIST,
    education_dist=GLOBAL_EDUCATION_DIST,
    occupation_dist=GLOBAL_OCCUPATION_DIST,
    marital_dist=GLOBAL_MARITAL_DIST,
    household_dist=TR_HOUSEHOLD_SIZE_DIST,  # evrensel benzer
    values_pool=GLOBAL_VALUES_POOL,
    interests_pool=GLOBAL_INTERESTS_POOL,
    brands_pool=GLOBAL_BRANDS_POOL,
    social_dist=GLOBAL_SOCIAL_DIST,
    online_shopping_dist=GLOBAL_ONLINE_SHOPPING_DIST,
    language="en",
    country_default="USA",
)

SEGMENT_MAP = {
    "TR": TR_DISTRIBUTIONS,
    "GLOBAL": GLOBAL_DISTRIBUTIONS,
}
