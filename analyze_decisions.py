"""
Agent Mining — Segment Analizi & Kural Motoru
DB'deki kararları okur, örüntü çıkarır, kuralları JSON olarak kaydeder.

Çalıştırma:
  python analyze_decisions.py
  python analyze_decisions.py --segment TR
  python analyze_decisions.py --export rules.json
"""

import os
import sys
import json
import argparse
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.agent_mining.models import Persona, AgentDecision, ReferenceCampaign, DecisionType, SegmentType

# ===========================================================================
# VERİ YÜKLEME
# ===========================================================================

def load_decisions(session, segment=None):
    """Karar + persona + kampanya verilerini birleşik yükle."""
    query = (
        session.query(AgentDecision, Persona, ReferenceCampaign)
        .join(Persona, AgentDecision.persona_id == Persona.id)
        .join(ReferenceCampaign, AgentDecision.campaign_id == ReferenceCampaign.id)
    )
    if segment:
        query = query.filter(Persona.segment == SegmentType(segment))

    rows = query.all()
    print(f"  ✅ {len(rows):,} karar yüklendi")
    return rows


# ===========================================================================
# TEMEL İSTATİSTİKLER
# ===========================================================================

def basic_stats(rows):
    total = len(rows)
    buy = sum(1 for d, p, c in rows if d.decision == DecisionType.BUY)
    print(f"\n{'='*60}")
    print(f"  GENEL İSTATİSTİKLER")
    print(f"{'='*60}")
    print(f"  Toplam karar:    {total:,}")
    print(f"  Satın alma:      {buy:,} (%{buy/total*100:.1f})")
    print(f"  Satın almama:    {total-buy:,} (%{(total-buy)/total*100:.1f})")
    print(f"  Ort. güven:      {sum(d.confidence for d,p,c in rows)/total:.2f}/10")

    # Segment bazlı
    seg_counts = defaultdict(lambda: {"buy": 0, "total": 0})
    for d, p, c in rows:
        seg = p.segment.value
        seg_counts[seg]["total"] += 1
        if d.decision == DecisionType.BUY:
            seg_counts[seg]["buy"] += 1

    print(f"\n  Segment bazlı:")
    for seg, v in sorted(seg_counts.items()):
        rate = v["buy"] / v["total"] * 100
        print(f"    {seg:8} → %{rate:.1f} satın alma ({v['buy']}/{v['total']})")


# ===========================================================================
# KAMPANYA ANALİZİ
# ===========================================================================

def campaign_analysis(rows):
    camp_data = defaultdict(lambda: {"buy": 0, "total": 0, "confidences": []})
    for d, p, c in rows:
        key = f"{p.segment.value} | {c.name}"
        camp_data[key]["total"] += 1
        camp_data[key]["confidences"].append(d.confidence)
        if d.decision == DecisionType.BUY:
            camp_data[key]["buy"] += 1

    print(f"\n{'='*60}")
    print(f"  KAMPANYA ANALİZİ (satın alma oranına göre)")
    print(f"{'='*60}")

    sorted_camps = sorted(camp_data.items(), key=lambda x: x[1]["buy"]/x[1]["total"], reverse=True)
    for key, v in sorted_camps:
        rate = v["buy"] / v["total"] * 100
        avg_conf = sum(v["confidences"]) / len(v["confidences"])
        bar = "█" * int(rate / 5)
        print(f"  {key:<45} %{rate:5.1f} {bar} (güven: {avg_conf:.1f})")


# ===========================================================================
# DEMOGRAFİK ÖRÜNTÜLER
# ===========================================================================

def demographic_patterns(rows):
    print(f"\n{'='*60}")
    print(f"  DEMOGRAFİK ÖRÜNTÜLER")
    print(f"{'='*60}")

    # Gelir seviyesi
    income_data = defaultdict(lambda: {"buy": 0, "total": 0})
    for d, p, c in rows:
        income_data[p.income_level]["total"] += 1
        if d.decision == DecisionType.BUY:
            income_data[p.income_level]["buy"] += 1

    print(f"\n  Gelir seviyesi → Satın alma oranı:")
    income_order = ["Düşük", "Orta-Düşük", "Orta", "Orta-Yüksek", "Yüksek",
                    "Low", "Lower-Middle", "Middle", "Upper-Middle", "High"]
    for income in income_order:
        if income in income_data:
            v = income_data[income]
            rate = v["buy"] / v["total"] * 100
            bar = "█" * int(rate / 5)
            print(f"    {income:<18} %{rate:5.1f} {bar}")

    # Yaş grubu
    age_data = defaultdict(lambda: {"buy": 0, "total": 0})
    for d, p, c in rows:
        age = p.age
        if age < 25:
            group = "18-24"
        elif age < 35:
            group = "25-34"
        elif age < 45:
            group = "35-44"
        elif age < 55:
            group = "45-54"
        else:
            group = "55+"
        age_data[group]["total"] += 1
        if d.decision == DecisionType.BUY:
            age_data[group]["buy"] += 1

    print(f"\n  Yaş grubu → Satın alma oranı:")
    for group in ["18-24", "25-34", "35-44", "45-54", "55+"]:
        if group in age_data:
            v = age_data[group]
            rate = v["buy"] / v["total"] * 100
            bar = "█" * int(rate / 5)
            print(f"    {group:<10} %{rate:5.1f} {bar}")

    # Fiyat hassasiyeti
    print(f"\n  Fiyat hassasiyeti → Satın alma oranı:")
    ps_data = defaultdict(lambda: {"buy": 0, "total": 0})
    for d, p, c in rows:
        ps = p.price_sensitivity
        if ps < 0.3:
            group = "Düşük (0.0-0.3)"
        elif ps < 0.6:
            group = "Orta (0.3-0.6)"
        else:
            group = "Yüksek (0.6-1.0)"
        ps_data[group]["total"] += 1
        if d.decision == DecisionType.BUY:
            ps_data[group]["buy"] += 1

    for group in ["Düşük (0.0-0.3)", "Orta (0.3-0.6)", "Yüksek (0.6-1.0)"]:
        if group in ps_data:
            v = ps_data[group]
            rate = v["buy"] / v["total"] * 100
            bar = "█" * int(rate / 5)
            print(f"    {group:<22} %{rate:5.1f} {bar}")

    # Cinsiyet
    print(f"\n  Cinsiyet → Satın alma oranı:")
    gender_data = defaultdict(lambda: {"buy": 0, "total": 0})
    for d, p, c in rows:
        gender_data[p.gender]["total"] += 1
        if d.decision == DecisionType.BUY:
            gender_data[p.gender]["buy"] += 1
    for gender, v in sorted(gender_data.items()):
        rate = v["buy"] / v["total"] * 100
        print(f"    {gender:<12} %{rate:5.1f}")

    # Eğitim
    print(f"\n  Eğitim → Satın alma oranı:")
    edu_data = defaultdict(lambda: {"buy": 0, "total": 0})
    for d, p, c in rows:
        edu_data[p.education]["total"] += 1
        if d.decision == DecisionType.BUY:
            edu_data[p.education]["buy"] += 1
    for edu, v in sorted(edu_data.items(), key=lambda x: x[1]["buy"]/x[1]["total"], reverse=True):
        rate = v["buy"] / v["total"] * 100
        bar = "█" * int(rate / 5)
        print(f"    {edu:<22} %{rate:5.1f} {bar}")


# ===========================================================================
# PSİKOGRAFİK ÖRÜNTÜLER
# ===========================================================================

def psychographic_patterns(rows):
    print(f"\n{'='*60}")
    print(f"  PSİKOGRAFİK ÖRÜNTÜLER (Big Five)")
    print(f"{'='*60}")

    traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
    trait_names = {
        "openness": "Yeniliğe Açıklık",
        "conscientiousness": "Sorumluluk",
        "extraversion": "Dışa Dönüklük",
        "agreeableness": "Uyumluluk",
        "neuroticism": "Duygusal Hassasiyet",
    }

    for trait in traits:
        # Yüksek (>0.6) vs Düşük (<0.4) karşılaştır
        high = {"buy": 0, "total": 0}
        low = {"buy": 0, "total": 0}
        for d, p, c in rows:
            val = getattr(p, trait)
            if val > 0.6:
                high["total"] += 1
                if d.decision == DecisionType.BUY:
                    high["buy"] += 1
            elif val < 0.4:
                low["total"] += 1
                if d.decision == DecisionType.BUY:
                    low["buy"] += 1

        if high["total"] > 0 and low["total"] > 0:
            high_rate = high["buy"] / high["total"] * 100
            low_rate = low["buy"] / low["total"] * 100
            diff = high_rate - low_rate
            direction = "↑ yüksek değer alım artırıyor" if diff > 2 else \
                        "↓ yüksek değer alımı azaltıyor" if diff < -2 else "→ etkisiz"
            print(f"  {trait_names[trait]:<22}: yüksek=%{high_rate:.1f} | düşük=%{low_rate:.1f} | {direction}")


# ===========================================================================
# KURAL MOTORU
# ===========================================================================

def build_rule_engine(rows):
    """
    Veriden örüntü çıkararak JSON kural seti oluşturur.
    Her kural: koşul + tahmini satın alma olasılığı
    """
    print(f"\n{'='*60}")
    print(f"  KURAL MOTORU — Çıkarılan Kurallar")
    print(f"{'='*60}")

    rules = []

    # --- Gelir × Fiyat kuralı ---
    income_price_data = defaultdict(lambda: {"buy": 0, "total": 0})
    for d, p, c in rows:
        price = (c.price_tl or 0) / 30 + (c.price_usd or 0)  # normalize to USD
        if price < 10:
            price_cat = "very_low"
        elif price < 50:
            price_cat = "low"
        elif price < 200:
            price_cat = "medium"
        elif price < 500:
            price_cat = "high"
        else:
            price_cat = "very_high"
        key = f"{p.income_level}|{price_cat}"
        income_price_data[key]["total"] += 1
        if d.decision == DecisionType.BUY:
            income_price_data[key]["buy"] += 1

    print(f"\n  Gelir × Fiyat Kategorisi (satın alma olasılığı):")
    income_price_rules = {}
    for key, v in income_price_data.items():
        if v["total"] >= 10:
            rate = v["buy"] / v["total"]
            income, price_cat = key.split("|")
            income_price_rules[key] = round(rate, 3)
            if rate > 0.4 or rate < 0.1:
                print(f"    {income:<20} × {price_cat:<12} → %{rate*100:.1f}")

    rules.append({
        "rule_id": "income_price_affinity",
        "description": "Gelir seviyesi × ürün fiyat kategorisi → satın alma olasılığı",
        "data": income_price_rules,
    })

    # --- Yaş × Kategori kuralı ---
    age_cat_data = defaultdict(lambda: {"buy": 0, "total": 0})
    for d, p, c in rows:
        age = p.age
        if age < 25: age_group = "18-24"
        elif age < 35: age_group = "25-34"
        elif age < 45: age_group = "35-44"
        elif age < 55: age_group = "45-54"
        else: age_group = "55+"
        key = f"{age_group}|{c.category}"
        age_cat_data[key]["total"] += 1
        if d.decision == DecisionType.BUY:
            age_cat_data[key]["buy"] += 1

    print(f"\n  Yaş × Kategori (satın alma olasılığı — sadece %40+ veya %5-):")
    age_cat_rules = {}
    for key, v in age_cat_data.items():
        if v["total"] >= 5:
            rate = v["buy"] / v["total"]
            age_cat_rules[key] = round(rate, 3)
            if rate > 0.4 or rate < 0.05:
                age_g, cat = key.split("|", 1)
                print(f"    {age_g:<8} × {cat:<30} → %{rate*100:.1f}")

    rules.append({
        "rule_id": "age_category_affinity",
        "description": "Yaş grubu × kampanya kategorisi → satın alma olasılığı",
        "data": age_cat_rules,
    })

    # --- Fiyat hassasiyeti × Fiyat kuralı ---
    ps_price_data = defaultdict(lambda: {"buy": 0, "total": 0})
    for d, p, c in rows:
        price = (c.price_tl or 0) / 30 + (c.price_usd or 0)
        ps = p.price_sensitivity
        ps_group = "low" if ps < 0.3 else "medium" if ps < 0.6 else "high"
        price_group = "affordable" if price < 30 else "mid" if price < 200 else "expensive"
        key = f"{ps_group}|{price_group}"
        ps_price_data[key]["total"] += 1
        if d.decision == DecisionType.BUY:
            ps_price_data[key]["buy"] += 1

    print(f"\n  Fiyat Hassasiyeti × Ürün Fiyatı:")
    ps_price_rules = {}
    for key, v in ps_price_data.items():
        if v["total"] >= 10:
            rate = v["buy"] / v["total"]
            ps_price_rules[key] = round(rate, 3)
            ps_g, price_g = key.split("|")
            print(f"    hassasiyet={ps_g:<8} × fiyat={price_g:<12} → %{rate*100:.1f}")

    rules.append({
        "rule_id": "price_sensitivity_price_match",
        "description": "Fiyat hassasiyeti × ürün fiyat seviyesi → satın alma olasılığı",
        "data": ps_price_rules,
    })

    # --- Segment bazlı kategori tercihleri ---
    seg_cat_data = defaultdict(lambda: {"buy": 0, "total": 0})
    for d, p, c in rows:
        key = f"{p.segment.value}|{c.category}"
        seg_cat_data[key]["total"] += 1
        if d.decision == DecisionType.BUY:
            seg_cat_data[key]["buy"] += 1

    print(f"\n  Segment × Kategori tercihleri (top satın alma oranları):")
    seg_cat_rules = {}
    for key, v in seg_cat_data.items():
        if v["total"] >= 10:
            rate = v["buy"] / v["total"]
            seg_cat_rules[key] = round(rate, 3)
    top_rules = sorted(seg_cat_rules.items(), key=lambda x: x[1], reverse=True)[:15]
    for key, rate in top_rules:
        seg, cat = key.split("|", 1)
        print(f"    {seg:<6} × {cat:<30} → %{rate*100:.1f}")

    rules.append({
        "rule_id": "segment_category_affinity",
        "description": "Coğrafi segment × kampanya kategorisi → satın alma olasılığı",
        "data": seg_cat_rules,
    })

    return rules


# ===========================================================================
# TAHMİN FONKSİYONU (kural motorunu kullan)
# ===========================================================================

def predict_buy_probability(rules_list, persona_dict, campaign_dict):
    """
    Verilen persona + kampanya için satın alma olasılığı tahmin eder.
    rules_list: build_rule_engine() çıktısı
    """
    rules = {r["rule_id"]: r["data"] for r in rules_list}

    # Normalize fiyat
    price_tl = campaign_dict.get("price_tl", 0) or 0
    price_usd = campaign_dict.get("price_usd", 0) or 0
    price = price_tl / 30 + price_usd

    # Fiyat kategorisi
    if price < 10: price_cat = "very_low"
    elif price < 50: price_cat = "low"
    elif price < 200: price_cat = "medium"
    elif price < 500: price_cat = "high"
    else: price_cat = "very_high"

    # Fiyat seviyesi
    if price < 30: price_level = "affordable"
    elif price < 200: price_level = "mid"
    else: price_level = "expensive"

    # Yaş grubu
    age = persona_dict.get("age", 30)
    if age < 25: age_group = "18-24"
    elif age < 35: age_group = "25-34"
    elif age < 45: age_group = "35-44"
    elif age < 55: age_group = "45-54"
    else: age_group = "55+"

    # Fiyat hassasiyeti grubu
    ps = persona_dict.get("price_sensitivity", 0.5)
    ps_group = "low" if ps < 0.3 else "medium" if ps < 0.6 else "high"

    # Segment
    segment = persona_dict.get("segment", "TR")
    category = campaign_dict.get("category", "")
    income = persona_dict.get("income_level", "Orta")

    # Kural bazlı skor topla
    scores = []

    ip_key = f"{income}|{price_cat}"
    if ip_key in rules.get("income_price_affinity", {}):
        scores.append(rules["income_price_affinity"][ip_key])

    ac_key = f"{age_group}|{category}"
    if ac_key in rules.get("age_category_affinity", {}):
        scores.append(rules["age_category_affinity"][ac_key])

    pp_key = f"{ps_group}|{price_level}"
    if pp_key in rules.get("price_sensitivity_price_match", {}):
        scores.append(rules["price_sensitivity_price_match"][pp_key])

    sc_key = f"{segment}|{category}"
    if sc_key in rules.get("segment_category_affinity", {}):
        scores.append(rules["segment_category_affinity"][sc_key])

    if not scores:
        return 0.3  # default

    return round(sum(scores) / len(scores), 3)


# ===========================================================================
# ANA FONKSİYON
# ===========================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--segment", choices=["TR", "EU", "USA", "MENA"])
    parser.add_argument("--export", default="agent_mining_rules.json",
                        help="Kural motorunu kaydet (varsayılan: agent_mining_rules.json)")
    parser.add_argument("--test", action="store_true",
                        help="Kural motorunu birkaç örnek ile test et")
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL eksik!")
        sys.exit(1)

    session = sessionmaker(bind=create_engine(db_url))()

    print("\n" + "=" * 60)
    print("  AGENT MINING — SEGMENT ANALİZİ & KURAL MOTORU")
    print("=" * 60)
    if args.segment:
        print(f"  Filtre: {args.segment} segmenti")

    rows = load_decisions(session, args.segment)

    if not rows:
        print("❌ DB'de karar bulunamadı. Önce veri topla.")
        session.close()
        return

    basic_stats(rows)
    campaign_analysis(rows)
    demographic_patterns(rows)
    psychographic_patterns(rows)
    rules = build_rule_engine(rows)

    # Kuralları JSON'a kaydet
    with open(args.export, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)
    print(f"\n  ✅ Kural motoru kaydedildi: {args.export}")

    # Test
    if args.test:
        print(f"\n{'='*60}")
        print(f"  KURAL MOTORU TEST")
        print(f"{'='*60}")
        test_cases = [
            ({"age": 28, "income_level": "Orta-Yüksek", "price_sensitivity": 0.2,
              "segment": "TR"}, {"category": "Teknoloji", "price_tl": 12999}),
            ({"age": 22, "income_level": "Orta-Düşük", "price_sensitivity": 0.8,
              "segment": "TR"}, {"category": "Eğitim", "price_tl": 279}),
            ({"age": 35, "income_level": "High", "price_sensitivity": 0.1,
              "segment": "EU"}, {"category": "Sport", "price_usd": 130}),
            ({"age": 45, "income_level": "Yüksek", "price_sensitivity": 0.15,
              "segment": "MENA"}, {"category": "Travel/Luxury", "price_usd": 2315}),
        ]
        for persona, campaign in test_cases:
            prob = predict_buy_probability(rules, persona, campaign)
            print(f"  {persona['income_level']:<15} | {persona['age']}y | "
                  f"hass={persona['price_sensitivity']:.1f} | "
                  f"{campaign['category']:<20} → %{prob*100:.1f}")

    session.close()


if __name__ == "__main__":
    main()
