"""Global Persona Factory - Supports TR, US, EU, MENA regions with 34 fields."""

import random
from typing import Optional
from .models import (
    Persona, PersonaConfig, Region, Gender, MaritalStatus, Education, IncomeLevel,
    LifeOutlook, PoliticalView, Religion, ShoppingPreference, BuyingStyle,
    TechAdoption, SocialMediaInfluence, FinancialBehavior, ScreenTime,
    OnlineShoppingFrequency, PaymentPreference, PersonalValues, DigitalHabits,
    Anxiety, BigFiveTraits
)
from .demographics import get_demographics
from .anxieties import get_anxieties


class PersonaFactory:
    """Factory for generating realistic synthetic personas across regions."""
    
    def __init__(self, config: Optional[PersonaConfig] = None):
        self.config = config or PersonaConfig()
        self.region = self.config.region.value if hasattr(self.config.region, 'value') else self.config.region
        self.demographics = get_demographics(self.region)
        self.anxieties = get_anxieties(self.region)
    
    def set_region(self, region: str):
        """Change the region for persona generation."""
        self.region = region
        self.demographics = get_demographics(region)
        self.anxieties = get_anxieties(region)
    
    def generate_one(self, forced_gender: Optional[Gender] = None) -> Persona:
        """Generate a single realistic persona."""
        
        # 1. Temel bilgiler
        gender = forced_gender or self._random_gender()
        age = self._random_age()
        country = self._random_country()
        city = self._random_city(country)
        name = self._random_name(gender, age)
        
        # 2. Sosyoekonomik
        education = self._random_education(age)
        occupation = self._random_occupation(age, education, gender)
        income_level = self._random_income(occupation, age, city)
        purchasing_power = self._calculate_purchasing_power(income_level, age, occupation)
        
        # 3. Medeni durum ve çocuk
        marital_status = self._random_marital_status(age)
        children_count = self._random_children_count(age, marital_status)
        
        # 4. Değerler ve inançlar
        life_outlook = self._random_life_outlook(age, income_level)
        political_view = self._random_political_view() if self.region != "MENA" else None
        religion = self._random_religion()
        personal_values = self._random_personal_values(age, gender)
        
        # 5. Tüketici davranışı
        shopping_preference = self._random_shopping_preference(age)
        buying_style = self._random_buying_style(income_level, age)
        tech_adoption = self._random_tech_adoption(age)
        social_media_influence = self._random_social_media_influence(age)
        financial_behavior = self._random_financial_behavior(income_level, age)
        
        # 6. Dijital alışkanlıklar
        digital_habits = self._random_digital_habits(age, income_level)
        
        # 7. Endişeler
        primary_anxiety, secondary_anxiety = self._assign_anxieties(
            age, income_level, occupation, marital_status, children_count, gender
        )
        
        # 8. Kişilik
        personality = self._random_personality()
        
        return Persona(
            name=name,
            region=Region(self.region),
            country=country,
            city=city,
            age=age,
            gender=gender,
            marital_status=marital_status,
            children_count=children_count,
            education=education,
            occupation=occupation,
            income_level=income_level,
            purchasing_power=purchasing_power,
            life_outlook=life_outlook,
            political_view=political_view,
            religion=religion,
            personal_values=personal_values,
            shopping_preference=shopping_preference,
            buying_style=buying_style,
            tech_adoption=tech_adoption,
            social_media_influence=social_media_influence,
            financial_behavior=financial_behavior,
            digital_habits=digital_habits,
            primary_anxiety=primary_anxiety,
            secondary_anxiety=secondary_anxiety,
            personality=personality,
        )
    
    def generate_batch(self, count: int) -> list[Persona]:
        """Generate multiple personas with optional filtering."""
        personas = []
        has_filters = self.config.filters is not None
        max_attempts = count * 15  # Filtre varsa daha fazla deneme
        attempts = 0

        if has_filters:
            # Filtreli üretim: üret, kontrol et, uyuyorsa ekle
            while len(personas) < count and attempts < max_attempts:
                persona = self.generate_one()
                if self._matches_filters(persona):
                    personas.append(persona)
                attempts += 1
        else:
            # Filtresiz: eski davranış (cinsiyet dengeli)
            male_count = 0
            female_count = 0
            target_per_gender = count // 2

            for _ in range(count):
                if male_count >= target_per_gender:
                    forced_gender = Gender.FEMALE
                elif female_count >= target_per_gender:
                    forced_gender = Gender.MALE
                else:
                    forced_gender = None

                persona = self.generate_one(forced_gender)
                personas.append(persona)

                if persona.gender == Gender.MALE or persona.gender == "Erkek":
                    male_count += 1
                else:
                    female_count += 1

        return personas

    def _matches_filters(self, persona) -> bool:
        """Check if persona matches the configured filters."""
        f = self.config.filters
        if not f:
            return True

        # Persona has use_enum_values = True, so fields are already strings
        # But we handle both cases for safety

        # Pro filters
        if f.gender:
            gender_val = persona.gender.value if hasattr(persona.gender, 'value') else str(persona.gender)
            if gender_val != f.gender:
                return False

        if f.min_age is not None and persona.age < f.min_age:
            return False
        if f.max_age is not None and persona.age > f.max_age:
            return False

        if f.income_levels:
            income_val = persona.income_level.value if hasattr(persona.income_level, 'value') else str(persona.income_level)
            if income_val not in f.income_levels:
                return False

        # Business filters
        if f.education_levels:
            edu_val = persona.education.value if hasattr(persona.education, 'value') else str(persona.education)
            if edu_val not in f.education_levels:
                return False

        if f.buying_styles:
            buy_val = persona.buying_style.value if hasattr(persona.buying_style, 'value') else str(persona.buying_style)
            if buy_val not in f.buying_styles:
                return False

        if f.marital_statuses:
            mar_val = persona.marital_status.value if hasattr(persona.marital_status, 'value') else str(persona.marital_status)
            if mar_val not in f.marital_statuses:
                return False

        # Enterprise filters
        if f.tech_adoptions:
            tech_val = persona.tech_adoption.value if hasattr(persona.tech_adoption, 'value') else str(persona.tech_adoption)
            if tech_val not in f.tech_adoptions:
                return False

        if f.online_shopping_freqs:
            # digital_habits is a nested model
            if isinstance(persona.digital_habits, dict):
                shop_val = persona.digital_habits.get("online_shopping_freq", "")
            else:
                shop_val = persona.digital_habits.online_shopping_freq.value if hasattr(persona.digital_habits.online_shopping_freq, 'value') else str(persona.digital_habits.online_shopping_freq)
            if shop_val not in f.online_shopping_freqs:
                return False

        if f.financial_behaviors:
            fin_val = persona.financial_behavior.value if hasattr(persona.financial_behavior, 'value') else str(persona.financial_behavior)
            if fin_val not in f.financial_behaviors:
                return False

        return True

    # ============================================
    # TEMEL BİLGİLER
    # ============================================
    
    def _random_gender(self) -> Gender:
        return random.choice([Gender.MALE, Gender.FEMALE])
    
    def _random_age(self) -> int:
        # Yaş dağılımı: 18-24 (%15), 25-34 (%22), 35-44 (%20), 45-54 (%18), 55-64 (%14), 65+ (%11)
        brackets = [(18, 24, 0.15), (25, 34, 0.22), (35, 44, 0.20), (45, 54, 0.18), (55, 64, 0.14), (65, 80, 0.11)]
        weights = [b[2] for b in brackets]
        chosen = random.choices(brackets, weights=weights)[0]
        
        min_age = max(chosen[0], self.config.min_age)
        max_age = min(chosen[1], self.config.max_age)
        return random.randint(min_age, max_age)
    
    def _random_country(self) -> str:
        countries = self.demographics["countries"]
        return random.choice(countries)
    
    def _random_city(self, country: str = None) -> str:
        cities = self.demographics["cities"]
        
        # Ülkeye göre filtrele (eğer ülke bilgisi varsa)
        if country and any("country" in cities[c] for c in cities):
            filtered = {k: v for k, v in cities.items() if v.get("country") == country}
            if filtered:
                cities = filtered
        
        city_names = list(cities.keys())
        weights = [cities[c]["weight"] for c in city_names]
        return random.choices(city_names, weights=weights)[0]
    
    def _random_name(self, gender: Gender, age: int) -> str:
        if gender == Gender.MALE:
            first_names = self.demographics["male_names"]
        else:
            first_names = self.demographics["female_names"]
        
        # Yaşlılar için geleneksel isimler (listenin başındakiler)
        if age > 50:
            first_names = first_names[:len(first_names)//2]
        
        last_names = self.demographics["last_names"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    # ============================================
    # SOSYOEKONOMİK
    # ============================================
    
    def _random_education(self, age: int) -> Education:
        base = {
            Education.PRIMARY: 0.10,
            Education.MIDDLE_SCHOOL: 0.12,
            Education.HIGH_SCHOOL: 0.28,
            Education.ASSOCIATE: 0.10,
            Education.UNIVERSITY: 0.28,
            Education.MASTERS: 0.08,
            Education.PHD: 0.04,
        }
        
        # Genç nesil daha yüksek eğitimli
        if age < 35:
            base[Education.PRIMARY] *= 0.3
            base[Education.MIDDLE_SCHOOL] *= 0.5
            base[Education.UNIVERSITY] *= 1.4
            base[Education.MASTERS] *= 1.3
        elif age > 55:
            base[Education.PRIMARY] *= 1.5
            base[Education.MIDDLE_SCHOOL] *= 1.3
            base[Education.UNIVERSITY] *= 0.8
        
        return random.choices(list(base.keys()), weights=list(base.values()))[0]
    
    def _random_occupation(self, age: int, education: Education, gender: Gender) -> str:
        occupations = self.demographics["occupations"]
        
        # 65+ yaş emekli olasılığı yüksek
        if age >= 65 and random.random() < 0.80:
            for occ in ["Emekli", "Retired"]:
                if occ in occupations:
                    return occ
        
        # Öğrenci kontrolü
        if age <= 28 and education.value in ["Lise", "Ön Lisans", "Üniversite", "Yüksek Lisans"]:
            if random.random() < 0.35:
                for occ in ["Öğrenci", "Student"]:
                    if occ in occupations:
                        return occ
        
        # Uygun meslekleri filtrele
        suitable = []
        for occ_name, occ_data in occupations.items():
            min_age, max_age = occ_data["age_range"]
            if not (min_age <= age <= max_age):
                continue
            
            if education.value not in occ_data["education"]:
                continue
            
            # Cinsiyet kontrolü
            gender_ratio = occ_data["gender_ratio"]
            if gender == Gender.MALE and gender_ratio < 0.1:
                continue
            if gender == Gender.FEMALE and gender_ratio > 0.95:
                continue
            
            # Ev hanımı sadece kadın
            if occ_name in ["Ev Hanımı", "Housewife", "Homemaker"] and gender != Gender.FEMALE:
                continue
            
            weight = gender_ratio if gender == Gender.MALE else (1 - gender_ratio)
            suitable.append((occ_name, max(0.1, weight)))
        
        if not suitable:
            return "İşsiz" if self.region == "TR" else "Unemployed"
        
        names, weights = zip(*suitable)
        return random.choices(names, weights=weights)[0]
    
    def _random_income(self, occupation: str, age: int, city: str) -> IncomeLevel:
        occupations = self.demographics["occupations"]
        cities = self.demographics["cities"]
        
        if occupation in occupations:
            allowed = occupations[occupation]["income"]
        else:
            allowed = ["Orta-Düşük", "Orta"]
        
        income_map = {
            "Düşük": IncomeLevel.LOW,
            "Orta-Düşük": IncomeLevel.LOWER_MIDDLE,
            "Orta": IncomeLevel.MIDDLE,
            "Orta-Yüksek": IncomeLevel.UPPER_MIDDLE,
            "Yüksek": IncomeLevel.HIGH,
        }
        
        # İzin verilen seviyeleri filtrele
        valid_levels = [income_map[i] for i in allowed if i in income_map]
        if not valid_levels:
            valid_levels = [IncomeLevel.MIDDLE]
        
        # Şehir gelir çarpanı
        city_mod = cities.get(city, {}).get("income_modifier", 1.0)
        
        # Yüksek gelir şehirlerinde üst seviyelere yönelim
        if city_mod > 1.2 and IncomeLevel.UPPER_MIDDLE in valid_levels:
            if random.random() < 0.3:
                return IncomeLevel.UPPER_MIDDLE
        
        return random.choice(valid_levels)
    
    def _calculate_purchasing_power(self, income: IncomeLevel, age: int, occupation: str) -> float:
        base = {
            IncomeLevel.LOW: 0.15,
            IncomeLevel.LOWER_MIDDLE: 0.30,
            IncomeLevel.MIDDLE: 0.50,
            IncomeLevel.UPPER_MIDDLE: 0.70,
            IncomeLevel.HIGH: 0.90,
        }
        
        power = base.get(income, 0.50)
        
        # Öğrenci düşük
        if occupation in ["Öğrenci", "Student"]:
            power *= 0.6
        
        # Emekli orta
        if occupation in ["Emekli", "Retired"]:
            power *= 0.85
        
        # Yaş etkisi
        if age < 25:
            power *= 0.8
        elif 30 <= age <= 50:
            power *= 1.1
        
        return max(0.05, min(0.98, power + random.uniform(-0.08, 0.08)))
    
    # ============================================
    # MEDENİ DURUM VE ÇOCUK
    # ============================================
    
    def _random_marital_status(self, age: int) -> MaritalStatus:
        if age < 25:
            weights = {"Bekar": 0.88, "Evli": 0.10, "Boşanmış": 0.02}
        elif age < 35:
            weights = {"Bekar": 0.35, "Evli": 0.58, "Boşanmış": 0.07}
        elif age < 50:
            weights = {"Bekar": 0.12, "Evli": 0.75, "Boşanmış": 0.13}
        else:
            weights = {"Bekar": 0.08, "Evli": 0.72, "Boşanmış": 0.20}
        
        status_map = {
            "Bekar": MaritalStatus.SINGLE,
            "Evli": MaritalStatus.MARRIED,
            "Boşanmış": MaritalStatus.DIVORCED,
        }
        
        chosen = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
        return status_map[chosen]
    
    def _random_children_count(self, age: int, marital_status: MaritalStatus) -> int:
        if marital_status == MaritalStatus.SINGLE:
            return 0
        
        if age < 28:
            return random.choices([0, 1], weights=[0.7, 0.3])[0]
        elif age < 40:
            return random.choices([0, 1, 2, 3], weights=[0.15, 0.35, 0.35, 0.15])[0]
        else:
            return random.choices([0, 1, 2, 3, 4], weights=[0.10, 0.20, 0.40, 0.20, 0.10])[0]
    
    # ============================================
    # DEĞERLER VE İNANÇLAR
    # ============================================
    
    def _random_life_outlook(self, age: int, income: IncomeLevel) -> LifeOutlook:
        weights = {
            LifeOutlook.OPTIMIST: 0.20,
            LifeOutlook.PESSIMIST: 0.10,
            LifeOutlook.REALIST: 0.30,
            LifeOutlook.ADVENTUROUS: 0.12,
            LifeOutlook.CONSERVATIVE: 0.15,
            LifeOutlook.PROGRESSIVE: 0.13,
        }
        
        # Gençler maceracı
        if age < 30:
            weights[LifeOutlook.ADVENTUROUS] *= 1.8
            weights[LifeOutlook.PROGRESSIVE] *= 1.5
        
        # Yaşlılar muhafazakar
        if age > 55:
            weights[LifeOutlook.CONSERVATIVE] *= 1.8
            weights[LifeOutlook.ADVENTUROUS] *= 0.5
        
        # Düşük gelir kötümser
        if income in [IncomeLevel.LOW, IncomeLevel.LOWER_MIDDLE]:
            weights[LifeOutlook.PESSIMIST] *= 1.5
        
        return random.choices(list(weights.keys()), weights=list(weights.values()))[0]
    
    def _random_political_view(self) -> Optional[PoliticalView]:
        dist = self.demographics.get("political_distribution")
        if not dist:
            return None
        
        view_map = {
            "Sol": PoliticalView.LEFT,
            "Merkez Sol": PoliticalView.CENTER_LEFT,
            "Merkez": PoliticalView.CENTER,
            "Merkez Sağ": PoliticalView.CENTER_RIGHT,
            "Sağ": PoliticalView.RIGHT,
            "Apolitik": PoliticalView.APOLITICAL,
        }
        
        views = list(dist.keys())
        weights = list(dist.values())
        chosen = random.choices(views, weights=weights)[0]
        return view_map.get(chosen)
    
    def _random_religion(self) -> Religion:
        dist = self.demographics.get("religion_distribution", {})
        
        religion_map = {
            "Müslüman": Religion.MUSLIM,
            "Hristiyan": Religion.CHRISTIAN,
            "Yahudi": Religion.JEWISH,
            "Ateist": Religion.ATHEIST,
            "Agnostik": Religion.AGNOSTIC,
            "Hindu": Religion.HINDU,
            "Budist": Religion.BUDDHIST,
            "Diğer": Religion.OTHER,
        }
        
        if not dist:
            return Religion.OTHER
        
        religions = list(dist.keys())
        weights = list(dist.values())
        chosen = random.choices(religions, weights=weights)[0]
        return religion_map.get(chosen, Religion.OTHER)
    
    def _random_personal_values(self, age: int, gender: Gender) -> PersonalValues:
        animal_lover = random.random() < 0.35
        environmentalist = random.random() < (0.45 if age < 40 else 0.25)
        family_oriented = random.random() < (0.70 if age > 30 else 0.40)
        
        return PersonalValues(
            animal_lover=animal_lover,
            environmentalist=environmentalist,
            family_oriented=family_oriented,
        )
    
    # ============================================
    # TÜKETİCİ DAVRANIŞI
    # ============================================
    
    def _random_shopping_preference(self, age: int) -> ShoppingPreference:
        if age < 30:
            weights = [0.15, 0.40, 0.30, 0.12, 0.03]
        elif age < 50:
            weights = [0.08, 0.25, 0.40, 0.20, 0.07]
        else:
            weights = [0.03, 0.12, 0.30, 0.35, 0.20]
        
        options = list(ShoppingPreference)
        return random.choices(options, weights=weights)[0]
    
    def _random_buying_style(self, income: IncomeLevel, age: int) -> BuyingStyle:
        weights = {
            BuyingStyle.PLANNER: 0.25,
            BuyingStyle.IMPULSIVE: 0.18,
            BuyingStyle.RESEARCHER: 0.22,
            BuyingStyle.BARGAIN_HUNTER: 0.20,
            BuyingStyle.BRAND_LOYAL: 0.15,
        }
        
        # Düşük gelir fırsat avcısı
        if income in [IncomeLevel.LOW, IncomeLevel.LOWER_MIDDLE]:
            weights[BuyingStyle.BARGAIN_HUNTER] *= 1.8
        
        # Yüksek gelir marka bağımlısı
        if income in [IncomeLevel.UPPER_MIDDLE, IncomeLevel.HIGH]:
            weights[BuyingStyle.BRAND_LOYAL] *= 1.6
        
        # Gençler anlık alıcı
        if age < 30:
            weights[BuyingStyle.IMPULSIVE] *= 1.5
        
        return random.choices(list(weights.keys()), weights=list(weights.values()))[0]
    
    def _random_tech_adoption(self, age: int) -> TechAdoption:
        if age < 30:
            weights = [0.35, 0.40, 0.20, 0.05]
        elif age < 50:
            weights = [0.15, 0.40, 0.35, 0.10]
        else:
            weights = [0.05, 0.20, 0.45, 0.30]
        
        options = list(TechAdoption)
        return random.choices(options, weights=weights)[0]
    
    def _random_social_media_influence(self, age: int) -> SocialMediaInfluence:
        if age < 30:
            weights = [0.40, 0.25, 0.15, 0.20]
        elif age < 50:
            weights = [0.20, 0.35, 0.20, 0.25]
        else:
            weights = [0.10, 0.30, 0.30, 0.30]
        
        options = list(SocialMediaInfluence)
        return random.choices(options, weights=weights)[0]
    
    def _random_financial_behavior(self, income: IncomeLevel, age: int) -> FinancialBehavior:
        weights = {
            FinancialBehavior.SAVER: 0.30,
            FinancialBehavior.SPENDER: 0.25,
            FinancialBehavior.INVESTOR: 0.20,
            FinancialBehavior.DEBT_USER: 0.25,
        }
        
        # Düşük gelir borç kullanıcısı
        if income in [IncomeLevel.LOW, IncomeLevel.LOWER_MIDDLE]:
            weights[FinancialBehavior.DEBT_USER] *= 1.5
            weights[FinancialBehavior.INVESTOR] *= 0.5
        
        # Yüksek gelir yatırımcı
        if income in [IncomeLevel.UPPER_MIDDLE, IncomeLevel.HIGH]:
            weights[FinancialBehavior.INVESTOR] *= 1.8
        
        # Yaşlılar tasarrufçu
        if age > 50:
            weights[FinancialBehavior.SAVER] *= 1.4
        
        return random.choices(list(weights.keys()), weights=list(weights.values()))[0]
    
    # ============================================
    # DİJİTAL ALIŞKANLIKLAR
    # ============================================
    
    def _random_digital_habits(self, age: int, income: IncomeLevel) -> DigitalHabits:
        platforms = self.demographics.get("platforms_by_age", {})
        
        if age < 30:
            platform_list = platforms.get("young", ["Instagram", "TikTok"])
        elif age < 50:
            platform_list = platforms.get("middle", ["Facebook", "Instagram"])
        else:
            platform_list = platforms.get("older", ["Facebook", "WhatsApp"])
        
        primary_platform = random.choice(platform_list)
        
        # Ekran süresi
        if age < 30:
            screen_time = random.choices(
                [ScreenTime.LOW, ScreenTime.MEDIUM, ScreenTime.HIGH],
                weights=[0.10, 0.35, 0.55]
            )[0]
        elif age < 50:
            screen_time = random.choices(
                [ScreenTime.LOW, ScreenTime.MEDIUM, ScreenTime.HIGH],
                weights=[0.20, 0.50, 0.30]
            )[0]
        else:
            screen_time = random.choices(
                [ScreenTime.LOW, ScreenTime.MEDIUM, ScreenTime.HIGH],
                weights=[0.40, 0.45, 0.15]
            )[0]
        
        # Online alışveriş sıklığı
        if age < 40:
            shopping_freq = random.choices(
                list(OnlineShoppingFrequency),
                weights=[0.05, 0.25, 0.50, 0.20]
            )[0]
        else:
            shopping_freq = random.choices(
                list(OnlineShoppingFrequency),
                weights=[0.15, 0.40, 0.35, 0.10]
            )[0]
        
        # Ödeme tercihi
        payment_prefs = self.demographics.get("payment_preferences", {})
        if payment_prefs:
            payment = random.choices(
                list(payment_prefs.keys()),
                weights=list(payment_prefs.values())
            )[0]
            payment_map = {
                "Kredi Kartı": PaymentPreference.CREDIT_CARD,
                "Banka Kartı": PaymentPreference.DEBIT_CARD,
                "Kapıda Ödeme": PaymentPreference.CASH_ON_DELIVERY,
                "Dijital Cüzdan": PaymentPreference.DIGITAL_WALLET,
            }
            payment_pref = payment_map.get(payment, PaymentPreference.CREDIT_CARD)
        else:
            payment_pref = PaymentPreference.CREDIT_CARD
        
        return DigitalHabits(
            primary_platform=primary_platform,
            screen_time=screen_time,
            online_shopping_freq=shopping_freq,
            payment_preference=payment_pref,
        )
    
    # ============================================
    # ENDİŞE ATAMA
    # ============================================
    
    def _assign_anxieties(
        self, age: int, income: IncomeLevel, occupation: str,
        marital_status: MaritalStatus, children_count: int, gender: Gender
    ) -> tuple[Optional[Anxiety], Optional[Anxiety]]:
        """Assign 1-2 anxieties based on persona characteristics."""
        
        eligible = []
        
        for anx_key, anx_data in self.anxieties.items():
            conditions = anx_data.get("conditions", {})
            
            # Yaş kontrolü
            if "age_range" in conditions:
                min_age, max_age = conditions["age_range"]
                if not (min_age <= age <= max_age):
                    continue
            
            # Gelir kontrolü
            if "income_levels" in conditions:
                if income.value not in conditions["income_levels"]:
                    continue
            
            # Meslek kontrolü
            if "occupations" in conditions:
                if occupation not in conditions["occupations"]:
                    continue
            
            # Hariç tutulan meslekler
            if "excluded_occupations" in conditions:
                if occupation in conditions["excluded_occupations"]:
                    continue
            
            # Çocuk kontrolü
            if conditions.get("has_children") and children_count == 0:
                continue
            
            eligible.append((anx_key, anx_data))
        
        if not eligible:
            return None, None
        
        # Ağırlıklı seçim
        weights = [a[1]["weight"] for a in eligible]
        
        # Birincil endişe
        primary_idx = random.choices(range(len(eligible)), weights=weights)[0]
        primary_data = eligible[primary_idx][1]
        primary = Anxiety(
            id=primary_data["id"],
            name=primary_data["name"],
            description=primary_data["description"]
        )
        
        # İkincil endişe (%60 şans)
        secondary = None
        if random.random() < 0.60 and len(eligible) > 1:
            remaining = [e for i, e in enumerate(eligible) if i != primary_idx]
            remaining_weights = [a[1]["weight"] for a in remaining]
            secondary_idx = random.choices(range(len(remaining)), weights=remaining_weights)[0]
            secondary_data = remaining[secondary_idx][1]
            secondary = Anxiety(
                id=secondary_data["id"],
                name=secondary_data["name"],
                description=secondary_data["description"]
            )
        
        return primary, secondary
    
    # ============================================
    # KİŞİLİK
    # ============================================
    
    def _random_personality(self) -> BigFiveTraits:
        return BigFiveTraits(
            openness=random.betavariate(2, 2),
            conscientiousness=random.betavariate(2, 2),
            extraversion=random.betavariate(2, 2),
            agreeableness=random.betavariate(2, 2),
            neuroticism=random.betavariate(2, 2),
        )