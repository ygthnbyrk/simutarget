"""
Agent Mining - Demografik Dağılım Verileri

Segment dağılımı:
  TR   → 100,000 persona (TÜİK 2023 bazlı)
  EU   → 175,000 persona (12 ülke: DE, FR, UK, IT, ES, NL, PL, SE, BE, PT, AT, CH)
  USA  → 175,000 persona (US Census bazlı)
  MENA → 50,000  persona (Dubai, Katar, Mısır, BAE)
  TOPLAM: 500,000 persona

Her dağılım (değer, ağırlık) tuple listesi.
random.choices(population, weights=weights) ile kullanılır.
"""

from dataclasses import dataclass

# ===========================================================================
# TÜRKİYE (100,000 persona — TÜİK 2023)
# ===========================================================================

TR_AGE_DIST = [
    (18, 24, 14),
    (25, 34, 21),
    (35, 44, 18),
    (45, 54, 16),
    (55, 64, 14),
    (65, 75, 10),
    (76, 85, 7),
]

TR_GENDER_DIST = [
    ("Erkek", 50),
    ("Kadın", 50),
]

TR_CITY_DIST = [
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
    ("Bolu", 1),
    ("Malatya", 1),
    ("Erzurum", 1),
    ("Diğer", 34),
]

TR_INCOME_DIST = [
    ("Düşük", 25),
    ("Orta-Düşük", 30),
    ("Orta", 25),
    ("Orta-Yüksek", 14),
    ("Yüksek", 6),
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
    (1, 10), (2, 18), (3, 22), (4, 28), (5, 14), (6, 8),
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

TR_SOCIAL_DIST = [("az", 20), ("orta", 45), ("yoğun", 35)]
TR_ONLINE_SHOPPING_DIST = [("nadiren", 25), ("aylık", 40), ("haftalık", 35)]


# ===========================================================================
# AVRUPA — EU (175,000 persona — 12 ülke, Eurostat bazlı)
# Almanya, Fransa, İngiltere, İtalya, İspanya, Hollanda,
# Polonya, İsveç, Belçika, Portekiz, Avusturya, İsviçre
# ===========================================================================

EU_AGE_DIST = [
    (18, 24, 11),
    (25, 34, 18),
    (35, 44, 19),
    (45, 54, 20),
    (55, 64, 17),
    (65, 80, 15),
]

EU_GENDER_DIST = [
    ("Male", 49),
    ("Female", 49),
    ("Non-binary", 2),
]

EU_CITY_DIST = [
    # Almanya (%22)
    ("Berlin, Germany", 7),
    ("Munich, Germany", 5),
    ("Hamburg, Germany", 5),
    ("Frankfurt, Germany", 5),
    # Fransa (%15)
    ("Paris, France", 8),
    ("Lyon, France", 4),
    ("Marseille, France", 3),
    # İngiltere (%15)
    ("London, UK", 9),
    ("Manchester, UK", 3),
    ("Birmingham, UK", 3),
    # İtalya (%12)
    ("Rome, Italy", 5),
    ("Milan, Italy", 5),
    ("Naples, Italy", 2),
    # İspanya (%10)
    ("Madrid, Spain", 5),
    ("Barcelona, Spain", 5),
    # Hollanda (%6)
    ("Amsterdam, Netherlands", 4),
    ("Rotterdam, Netherlands", 2),
    # Polonya (%5)
    ("Warsaw, Poland", 3),
    ("Krakow, Poland", 2),
    # İsveç (%4)
    ("Stockholm, Sweden", 3),
    ("Gothenburg, Sweden", 1),
    # Belçika (%3)
    ("Brussels, Belgium", 2),
    ("Antwerp, Belgium", 1),
    # Portekiz (%3)
    ("Lisbon, Portugal", 2),
    ("Porto, Portugal", 1),
    # Avusturya (%2)
    ("Vienna, Austria", 2),
    # İsviçre (%3)
    ("Zurich, Switzerland", 2),
    ("Geneva, Switzerland", 1),
]

EU_INCOME_DIST = [
    ("Low", 12),
    ("Lower-Middle", 18),
    ("Middle", 35),
    ("Upper-Middle", 25),
    ("High", 10),
]

EU_EDUCATION_DIST = [
    ("Secondary School", 20),
    ("Vocational Training", 18),
    ("Bachelor's Degree", 38),
    ("Master's Degree", 18),
    ("PhD", 6),
]

EU_OCCUPATION_DIST = [
    ("Self-employed / Freelancer", 11),
    ("Corporate Employee", 30),
    ("Government / Public Sector", 12),
    ("Blue-collar Worker", 14),
    ("Homemaker / Caregiver", 7),
    ("Student", 9),
    ("Retired", 11),
    ("Entrepreneur / Business Owner", 4),
    ("Unemployed", 2),
]

EU_MARITAL_DIST = [
    ("Single", 36),
    ("Married / Partnered", 52),
    ("Divorced / Widowed", 12),
]

EU_HOUSEHOLD_SIZE_DIST = [
    (1, 18), (2, 28), (3, 22), (4, 22), (5, 7), (6, 3),
]

EU_VALUES_POOL = [
    "family", "work-life balance", "sustainability / environment",
    "health & wellness", "education", "personal freedom",
    "security", "community", "innovation", "tradition",
    "financial stability", "travel & experiences", "social justice",
    "minimalism", "quality over quantity",
]

EU_INTERESTS_POOL = [
    "football / soccer", "cycling", "cooking / food", "travel",
    "reading / books", "music", "arts & culture", "fitness",
    "technology", "fashion / style", "gaming", "hiking / nature",
    "cinema", "investing / finance", "photography",
]

EU_BRANDS_POOL = [
    "IKEA", "Zara", "H&M", "Adidas", "BMW",
    "Volkswagen", "Lidl", "Aldi", "Apple", "Samsung",
    "Spotify", "Netflix", "Dyson", "Lego", "Patagonia",
    "L'Oréal", "Unilever", "Nestlé", "Philips", "Bosch",
]

EU_SOCIAL_DIST = [("minimal", 18), ("moderate", 47), ("heavy", 35)]
EU_ONLINE_SHOPPING_DIST = [("rarely", 12), ("monthly", 35), ("weekly", 53)]


# ===========================================================================
# USA (175,000 persona — US Census 2023 bazlı)
# ===========================================================================

USA_AGE_DIST = [
    (18, 24, 13),
    (25, 34, 18),
    (35, 44, 18),
    (45, 54, 17),
    (55, 64, 17),
    (65, 80, 17),
]

USA_GENDER_DIST = [
    ("Male", 49),
    ("Female", 49),
    ("Non-binary", 2),
]

USA_CITY_DIST = [
    # Northeast
    ("New York, NY", 9),
    ("Philadelphia, PA", 2),
    ("Boston, MA", 2),
    ("Washington, DC", 2),
    # South
    ("Houston, TX", 4),
    ("Dallas, TX", 3),
    ("Miami, FL", 3),
    ("Atlanta, GA", 2),
    ("Charlotte, NC", 1),
    ("Nashville, TN", 1),
    # Midwest
    ("Chicago, IL", 5),
    ("Detroit, MI", 1),
    ("Minneapolis, MN", 1),
    ("Columbus, OH", 1),
    # West
    ("Los Angeles, CA", 8),
    ("San Francisco, CA", 3),
    ("Seattle, WA", 2),
    ("Denver, CO", 2),
    ("Phoenix, AZ", 2),
    ("Las Vegas, NV", 1),
    ("Portland, OR", 1),
    # Other
    ("Other (Suburban)", 25),
    ("Other (Rural)", 19),
]

USA_INCOME_DIST = [
    ("Low (< $30K)", 14),
    ("Lower-Middle ($30K-$60K)", 22),
    ("Middle ($60K-$100K)", 30),
    ("Upper-Middle ($100K-$200K)", 24),
    ("High ($200K+)", 10),
]

USA_EDUCATION_DIST = [
    ("High School / GED", 27),
    ("Some College", 15),
    ("Associate's Degree", 10),
    ("Bachelor's Degree", 32),
    ("Master's Degree", 12),
    ("PhD / Professional", 4),
]

USA_OCCUPATION_DIST = [
    ("Self-employed / Freelancer", 10),
    ("Corporate / Office Worker", 28),
    ("Government / Military", 6),
    ("Blue-collar / Trades", 15),
    ("Homemaker / Caregiver", 8),
    ("Student", 8),
    ("Retired", 12),
    ("Entrepreneur / Business Owner", 7),
    ("Unemployed / Job-seeking", 6),
]

USA_MARITAL_DIST = [
    ("Single", 38),
    ("Married / Partnered", 50),
    ("Divorced / Widowed", 12),
]

USA_HOUSEHOLD_SIZE_DIST = [
    (1, 16), (2, 27), (3, 21), (4, 23), (5, 9), (6, 4),
]

USA_VALUES_POOL = [
    "family", "personal freedom", "hard work / hustle", "faith / religion",
    "financial independence", "patriotism", "health & fitness",
    "entrepreneurship", "education", "community",
    "sustainability", "security", "diversity & inclusion",
    "innovation / technology", "entertainment",
]

USA_INTERESTS_POOL = [
    "American football / NFL", "basketball / NBA", "baseball",
    "streaming (Netflix / Hulu)", "cooking / BBQ", "fitness / gym",
    "travel", "technology / gadgets", "gaming", "fashion",
    "investing / stocks", "podcasts", "outdoor activities",
    "music", "cars / trucks",
]

USA_BRANDS_POOL = [
    "Amazon", "Apple", "Nike", "Walmart", "Target",
    "Costco", "Starbucks", "McDonald's", "Tesla", "Google",
    "Microsoft", "Netflix", "Levi's", "Ralph Lauren", "Ford",
    "Chevrolet", "Patagonia", "Yeti", "Stanley", "Peloton",
]

USA_SOCIAL_DIST = [("minimal", 13), ("moderate", 42), ("heavy", 45)]
USA_ONLINE_SHOPPING_DIST = [("rarely", 10), ("monthly", 30), ("weekly", 60)]


# ===========================================================================
# MENA (50,000 persona — Dubai, Katar, Mısır, BAE)
# ===========================================================================

MENA_AGE_DIST = [
    (18, 24, 20),
    (25, 34, 28),
    (35, 44, 22),
    (45, 54, 16),
    (55, 64, 9),
    (65, 75, 5),
]

MENA_GENDER_DIST = [
    ("Male", 55),
    ("Female", 45),
]

MENA_CITY_DIST = [
    # BAE
    ("Dubai, UAE", 20),
    ("Abu Dhabi, UAE", 10),
    ("Sharjah, UAE", 5),
    # Katar
    ("Doha, Qatar", 15),
    # Mısır
    ("Cairo, Egypt", 25),
    ("Alexandria, Egypt", 10),
    ("Giza, Egypt", 5),
    ("Sharm El-Sheikh, Egypt", 2),
    # Diğer
    ("Other MENA", 8),
]

MENA_INCOME_DIST = [
    ("Low", 20),
    ("Lower-Middle", 22),
    ("Middle", 28),
    ("Upper-Middle", 20),
    ("High", 10),
]

MENA_EDUCATION_DIST = [
    ("Primary / Secondary", 18),
    ("High School", 22),
    ("Bachelor's Degree", 40),
    ("Master's Degree", 16),
    ("PhD", 4),
]

MENA_OCCUPATION_DIST = [
    ("Corporate / Finance", 18),
    ("Government / Public Sector", 14),
    ("Real Estate / Construction", 10),
    ("Hospitality / Tourism", 10),
    ("Retail / Trade", 12),
    ("Student", 12),
    ("Homemaker / Caregiver", 10),
    ("Entrepreneur / Business Owner", 8),
    ("Unemployed", 6),
]

MENA_MARITAL_DIST = [
    ("Single", 32),
    ("Married", 58),
    ("Divorced / Widowed", 10),
]

MENA_HOUSEHOLD_SIZE_DIST = [
    (1, 8), (2, 15), (3, 20), (4, 25), (5, 18), (6, 14),
]

MENA_VALUES_POOL = [
    "family", "faith / Islam", "social status / prestige",
    "hospitality / generosity", "loyalty", "financial security",
    "education", "luxury / lifestyle", "health",
    "tradition & culture", "community", "ambition / success",
    "travel & experiences", "philanthropy / giving back",
]

MENA_INTERESTS_POOL = [
    "football / soccer", "luxury shopping", "travel", "technology",
    "fine dining / food", "social media (Instagram / TikTok)",
    "real estate / investing", "fitness / gym", "gaming",
    "fashion / luxury brands", "music (Arabic & Western)",
    "cars / supercars", "outdoor / desert activities",
    "crypto / fintech", "family gatherings",
]

MENA_BRANDS_POOL = [
    "Apple", "Samsung", "Nike", "Adidas", "Zara",
    "H&M", "Amazon", "Noon", "Carrefour", "LuLu Hypermarket",
    "Rolex", "Gucci", "Louis Vuitton", "Mercedes-Benz", "BMW",
    "Lamborghini", "Emirates Airlines", "Etihad", "Deliveroo", "Talabat",
]

MENA_SOCIAL_DIST = [("minimal", 10), ("moderate", 35), ("heavy", 55)]
MENA_ONLINE_SHOPPING_DIST = [("rarely", 12), ("monthly", 33), ("weekly", 55)]


# ===========================================================================
# HELPER: SegmentDistributions dataclass
# ===========================================================================

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
    language: str
    country_default: str


TR_DISTRIBUTIONS = SegmentDistributions(
    age_dist=TR_AGE_DIST, gender_dist=TR_GENDER_DIST, city_dist=TR_CITY_DIST,
    income_dist=TR_INCOME_DIST, education_dist=TR_EDUCATION_DIST,
    occupation_dist=TR_OCCUPATION_DIST, marital_dist=TR_MARITAL_DIST,
    household_dist=TR_HOUSEHOLD_SIZE_DIST, values_pool=TR_VALUES_POOL,
    interests_pool=TR_INTERESTS_POOL, brands_pool=TR_BRANDS_POOL,
    social_dist=TR_SOCIAL_DIST, online_shopping_dist=TR_ONLINE_SHOPPING_DIST,
    language="tr", country_default="Türkiye",
)

EU_DISTRIBUTIONS = SegmentDistributions(
    age_dist=EU_AGE_DIST, gender_dist=EU_GENDER_DIST, city_dist=EU_CITY_DIST,
    income_dist=EU_INCOME_DIST, education_dist=EU_EDUCATION_DIST,
    occupation_dist=EU_OCCUPATION_DIST, marital_dist=EU_MARITAL_DIST,
    household_dist=EU_HOUSEHOLD_SIZE_DIST, values_pool=EU_VALUES_POOL,
    interests_pool=EU_INTERESTS_POOL, brands_pool=EU_BRANDS_POOL,
    social_dist=EU_SOCIAL_DIST, online_shopping_dist=EU_ONLINE_SHOPPING_DIST,
    language="en", country_default="Europe",
)

USA_DISTRIBUTIONS = SegmentDistributions(
    age_dist=USA_AGE_DIST, gender_dist=USA_GENDER_DIST, city_dist=USA_CITY_DIST,
    income_dist=USA_INCOME_DIST, education_dist=USA_EDUCATION_DIST,
    occupation_dist=USA_OCCUPATION_DIST, marital_dist=USA_MARITAL_DIST,
    household_dist=USA_HOUSEHOLD_SIZE_DIST, values_pool=USA_VALUES_POOL,
    interests_pool=USA_INTERESTS_POOL, brands_pool=USA_BRANDS_POOL,
    social_dist=USA_SOCIAL_DIST, online_shopping_dist=USA_ONLINE_SHOPPING_DIST,
    language="en", country_default="USA",
)

MENA_DISTRIBUTIONS = SegmentDistributions(
    age_dist=MENA_AGE_DIST, gender_dist=MENA_GENDER_DIST, city_dist=MENA_CITY_DIST,
    income_dist=MENA_INCOME_DIST, education_dist=MENA_EDUCATION_DIST,
    occupation_dist=MENA_OCCUPATION_DIST, marital_dist=MENA_MARITAL_DIST,
    household_dist=MENA_HOUSEHOLD_SIZE_DIST, values_pool=MENA_VALUES_POOL,
    interests_pool=MENA_INTERESTS_POOL, brands_pool=MENA_BRANDS_POOL,
    social_dist=MENA_SOCIAL_DIST, online_shopping_dist=MENA_ONLINE_SHOPPING_DIST,
    language="en", country_default="MENA",
)

# Segment haritası
SEGMENT_MAP = {
    "TR": TR_DISTRIBUTIONS,
    "EU": EU_DISTRIBUTIONS,
    "USA": USA_DISTRIBUTIONS,
    "MENA": MENA_DISTRIBUTIONS,
}

# 500K üretim hedefleri
PRODUCTION_TARGETS = {
    "TR": 100_000,
    "EU": 175_000,
    "USA": 175_000,
    "MENA": 50_000,
}  # TOPLAM: 500,000
