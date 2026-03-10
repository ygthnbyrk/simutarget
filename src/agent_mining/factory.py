"""
Agent Mining - Persona Üretim Fabrikası

50K persona'yı verimli şekilde üretmek için tasarlanmış pipeline.

Strateji:
  - LLM KULLANMADAN üretiyoruz (kural bazlı + random sampling)
  - Demografik dağılımlar gerçekçi olduğu için persona'lar tutarlı
  - LLM sadece KARAR aşamasında kullanılır (campaign runner)
  - Bu sayede 50K persona = $0 üretim maliyeti

Örnek kullanım:
  factory = PersonaFactory(segment="TR")
  personas = factory.generate_batch(count=1000)
  factory.save_to_db(personas, session)
"""

import random
import hashlib
from typing import Optional
from uuid import uuid4

from .demographics import SEGMENT_MAP, SegmentDistributions
from .models import Persona, SegmentType


# ---------------------------------------------------------------------------
# İSİM HAVUZLARI
# ---------------------------------------------------------------------------

TR_MALE_NAMES = [
    "Ahmet", "Mehmet", "Mustafa", "Ali", "Hüseyin", "İbrahim", "Hasan",
    "Ömer", "Yusuf", "Burak", "Emre", "Arda", "Serkan", "Kemal", "Fatih",
    "Mert", "Can", "Berk", "Kaan", "Onur", "Tolga", "Sinan", "Murat",
]

TR_FEMALE_NAMES = [
    "Fatma", "Ayşe", "Hatice", "Zeynep", "Emine", "Elif", "Merve",
    "Büşra", "Esra", "Selin", "Derya", "Melisa", "Gamze", "Ceyda",
    "Neslihan", "Tuğçe", "Arzu", "Özge", "Pınar", "Nilüfer",
]

TR_SURNAMES = [
    "Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Yıldız", "Yıldırım",
    "Özdemir", "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Koç",
    "Erdoğan", "Kurt", "Özkan", "Şimşek", "Çakır", "Aydın",
]

GLOBAL_MALE_NAMES = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard",
    "Thomas", "Christopher", "Daniel", "Matthew", "Anthony", "Donald",
    "Luca", "Noah", "Oliver", "Elijah", "Lucas", "Mason", "Ethan",
    "Mohammed", "Yusuf", "Leon", "Paul", "Marco", "Carlos",
]

GLOBAL_FEMALE_NAMES = [
    "Emma", "Olivia", "Sophia", "Isabella", "Ava", "Mia", "Charlotte",
    "Amelia", "Harper", "Evelyn", "Abigail", "Emily", "Elizabeth",
    "Sarah", "Hannah", "Laura", "Anna", "Sofia", "Valentina", "Elena",
]

GLOBAL_SURNAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Martinez", "Wilson", "Anderson", "Taylor", "Thomas", "Moore",
    "Müller", "Schmidt", "Rossi", "Ferrari", "Dubois", "López", "Sánchez",
]


# ---------------------------------------------------------------------------
# FACTORY
# ---------------------------------------------------------------------------

class PersonaFactory:
    """
    Demografik dağılımlara göre sentetik persona üretir.
    LLM kullanmaz — tamamen kural bazlı ve rastgele örnekleme.
    """

    def __init__(self, segment: str = "TR", seed: Optional[int] = None):
        """
        Args:
            segment: "TR" veya "GLOBAL"
            seed: Reproducibility için random seed (opsiyonel)
        """
        if segment not in SEGMENT_MAP:
            raise ValueError(f"Geçersiz segment: {segment}. 'TR', 'EU', 'USA' veya 'MENA' olmalı.")

        self.segment = segment
        self.dist: SegmentDistributions = SEGMENT_MAP[segment]

        if seed is not None:
            random.seed(seed)

    def _weighted_choice(self, dist: list) -> str:
        """(değer, ağırlık) listesinden ağırlıklı rastgele seçim."""
        values = [item[0] for item in dist]
        weights = [item[-1] for item in dist]
        return random.choices(values, weights=weights, k=1)[0]

    def _sample_age(self) -> int:
        """Yaş dağılımından rastgele yaş üretir."""
        bucket = random.choices(
            self.dist.age_dist,
            weights=[b[-1] for b in self.dist.age_dist],
            k=1
        )[0]
        return random.randint(bucket[0], bucket[1])

    def _generate_name(self, gender: str) -> str:
        if self.segment == "TR":
            if gender == "Erkek":
                first = random.choice(TR_MALE_NAMES)
            else:
                first = random.choice(TR_FEMALE_NAMES)
            last = random.choice(TR_SURNAMES)
        else:
            # EU, USA, MENA hepsi global isim havuzu kullanır
            if gender in ("Male",):
                first = random.choice(GLOBAL_MALE_NAMES)
            else:
                first = random.choice(GLOBAL_FEMALE_NAMES)
            last = random.choice(GLOBAL_SURNAMES)
        return f"{first} {last}"

    def _big_five(self) -> dict:
        """
        Big Five skorları — korelasyonlu üretim.
        Tamamen bağımsız değil; yaşa ve eğitime göre hafif eğilim var.
        """
        return {
            "openness": round(random.betavariate(5, 3), 2),           # hafif yüksek eğilim
            "conscientiousness": round(random.betavariate(4, 3), 2),
            "extraversion": round(random.betavariate(4, 4), 2),       # nötr
            "agreeableness": round(random.betavariate(5, 3), 2),
            "neuroticism": round(random.betavariate(3, 4), 2),        # hafif düşük eğilim
        }

    def _sample_values_and_interests(self) -> tuple[list, list]:
        """Değer ve ilgi alanları havuzundan rastgele seçim."""
        num_values = random.randint(2, 5)
        num_interests = random.randint(3, 6)

        values = random.sample(self.dist.values_pool, min(num_values, len(self.dist.values_pool)))
        interests = random.sample(self.dist.interests_pool, min(num_interests, len(self.dist.interests_pool)))
        brands = random.sample(self.dist.brands_pool, random.randint(1, 4))

        return values, interests, brands

    def generate_one(self) -> Persona:
        """Tek bir Persona objesi üretir (DB'ye kaydetmez)."""
        gender = self._weighted_choice(self.dist.gender_dist)
        age = self._sample_age()
        big_five = self._big_five()
        values, interests, brands = self._sample_values_and_interests()

        city_raw = self._weighted_choice(self.dist.city_dist)
        city = city_raw if city_raw != "Diğer" and city_raw != "Other" else self._fallback_city()

        household = self._weighted_choice(self.dist.household_dist)

        persona = Persona(
            id=uuid4(),
            segment=SegmentType(self.segment),
            name=self._generate_name(gender),
            age=age,
            gender=gender,
            city=city,
            country=self.dist.country_default,
            income_level=self._weighted_choice(self.dist.income_dist),
            education=self._weighted_choice(self.dist.education_dist),
            occupation=self._weighted_choice(self.dist.occupation_dist),
            marital_status=self._weighted_choice(self.dist.marital_dist),
            household_size=household,
            openness=big_five["openness"],
            conscientiousness=big_five["conscientiousness"],
            extraversion=big_five["extraversion"],
            agreeableness=big_five["agreeableness"],
            neuroticism=big_five["neuroticism"],
            values=values,
            interests=interests,
            brands_liked=brands,
            price_sensitivity=round(random.uniform(0.1, 0.95), 2),
            social_media_usage=self._weighted_choice(self.dist.social_dist),
            online_shopping_freq=self._weighted_choice(self.dist.online_shopping_dist),
            generation_model="rule-based-v1",
            is_validated=False,
        )
        return persona

    def _fallback_city(self) -> str:
        """'Diğer' / 'Other' kategorisi için küçük şehir fallback."""
        fallbacks = {
            "TR": ["Bolu", "Kastamonu", "Sinop", "Bartın", "Karabük", "Kırıkkale"],
            "EU": ["Lyon, France", "Leipzig, Germany", "Valencia, Spain", "Turin, Italy", "Gdansk, Poland"],
            "USA": ["Denver, CO", "Portland, OR", "Austin, TX", "Raleigh, NC", "Salt Lake City, UT"],
            "MENA": ["Sharjah, UAE", "Al Ain, UAE", "Luxor, Egypt", "Aswan, Egypt"],
        }
        return random.choice(fallbacks.get(self.segment, ["Unknown City"]))

    def generate_batch(self, count: int, progress_cb=None) -> list[Persona]:
        """
        count adet Persona listesi üretir.

        Args:
            count: Kaç persona üretilsin
            progress_cb: İlerleme callback'i (i, total) → None (opsiyonel)

        Returns:
            List[Persona]
        """
        personas = []
        for i in range(count):
            personas.append(self.generate_one())
            if progress_cb and (i + 1) % 1000 == 0:
                progress_cb(i + 1, count)
        return personas

    def save_to_db(self, personas: list[Persona], session, batch_size: int = 500) -> int:
        """
        Persona listesini PostgreSQL'e toplu kayıt eder.

        Args:
            personas: Kaydedilecek persona listesi
            session: SQLAlchemy session
            batch_size: Her commit'te kaç kayıt

        Returns:
            Toplam kaydedilen sayı
        """
        total = 0
        for i in range(0, len(personas), batch_size):
            batch = personas[i:i + batch_size]
            session.bulk_save_objects(batch)
            session.commit()
            total += len(batch)
            print(f"  ✓ {total}/{len(personas)} persona kaydedildi")
        return total


# ---------------------------------------------------------------------------
# HIZLI TEST
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== TR Segmenti - 5 Örnek Persona ===\n")
    factory_tr = PersonaFactory(segment="TR", seed=42)
    for p in factory_tr.generate_batch(5):
        print(f"  {p.name} | {p.age}y | {p.city} | {p.income_level}")
        print(f"  Openness={p.openness} | Fiyat Hassasiyeti={p.price_sensitivity}")
        print(f"  Değerler: {p.values}")
        print()

    print("=== GLOBAL Segmenti - 5 Örnek Persona ===\n")
    factory_gl = PersonaFactory(segment="GLOBAL", seed=42)
    for p in factory_gl.generate_batch(5):
        print(f"  {p.name} | {p.age}y | {p.city} | {p.income_level}")
        print(f"  Interests: {p.interests}")
        print()
