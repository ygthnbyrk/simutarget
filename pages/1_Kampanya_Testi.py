"""
SimuTarget.ai - Kampanya Testi Sayfası
Kullanıcı kampanya metnini girer, persona'lar değerlendirir.
"""

import streamlit as st
import sys
import os
import time
import json
import random
from pathlib import Path

# Proje root'unu path'e ekle
PROJECT_ROOT = str(Path(__file__).parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.personas.models import Persona, PersonaConfig, Region, Gender
from src.personas.factory import PersonaFactory

st.set_page_config(
    page_title="Kampanya Testi - SimuTarget.ai",
    page_icon="🧪",
    layout="wide",
)

# ============================================
# CSS
# ============================================
st.markdown("""
<style>
    .result-card {
        background: linear-gradient(135deg, #1e293b, #334155);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #475569;
        margin-bottom: 1rem;
    }
    .big-metric {
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
    }
    .metric-green { color: #34d399; }
    .metric-red { color: #f87171; }
    .metric-blue { color: #38bdf8; }
    .metric-yellow { color: #fbbf24; }
    .persona-row {
        background: #1e293b;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .persona-yes { border-left-color: #34d399; }
    .persona-no { border-left-color: #f87171; }
    .lock-icon {
        color: #fbbf24;
        font-size: 0.85rem;
        cursor: help;
    }
    .test-running {
        background: linear-gradient(135deg, #0f172a, #1e3a5f);
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        border: 1px solid #1e40af;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# PLAN ÖZELLİKLERİ
# ============================================
PLAN_FEATURES = {
    "Basic": {
        "max_personas": 50,
        "filters": ["region"],  # Sadece bölge
        "pdf_export": False,
        "detailed_report": False,
        "segment_analysis": False,
    },
    "Pro": {
        "max_personas": 100,
        "filters": ["region", "age", "gender", "income"],
        "pdf_export": True,
        "detailed_report": True,
        "segment_analysis": False,
    },
    "Business": {
        "max_personas": 100,
        "filters": ["region", "age", "gender", "income", "education", "marital", "buying_style", "tech_adoption"],
        "pdf_export": True,
        "detailed_report": True,
        "segment_analysis": True,
    },
    "Enterprise": {
        "max_personas": 100,
        "filters": ["region", "age", "gender", "income", "education", "marital", "buying_style", "tech_adoption"],
        "pdf_export": True,
        "detailed_report": True,
        "segment_analysis": True,
    },
}


def is_feature_available(feature: str) -> bool:
    """Mevcut pakette özellik var mı?"""
    plan = st.session_state.get("user_plan", "Basic")
    features = PLAN_FEATURES.get(plan, PLAN_FEATURES["Basic"])
    if feature in ["pdf_export", "detailed_report", "segment_analysis"]:
        return features.get(feature, False)
    return feature in features.get("filters", [])


def locked_label(label: str, feature: str) -> str:
    """Kilitli özellik etiketi."""
    if not is_feature_available(feature):
        return f"{label} 🔒"
    return label


def get_max_personas() -> int:
    plan = st.session_state.get("user_plan", "Basic")
    return PLAN_FEATURES.get(plan, {}).get("max_personas", 50)


# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("## 🎯 SimuTarget.ai")
    st.markdown("*Kampanya Testi*")
    st.divider()
    
    # API Key
    api_key = st.session_state.get("openai_api_key", "")
    if not api_key:
        new_key = st.text_input("🔑 OpenAI API Key", type="password", placeholder="sk-...")
        if new_key:
            st.session_state["openai_api_key"] = new_key
            st.rerun()
        st.info("💡 API Key olmadan **Demo Mod** aktif. Sonuçlar simüle edilir.")
    else:
        st.success("✅ API Key aktif")
        if st.button("API Key'i Kaldır", type="secondary"):
            del st.session_state["openai_api_key"]
            st.rerun()
    
    st.divider()
    
    # Paket & Kredi
    plan = st.session_state.get("user_plan", "Basic")
    credits = st.session_state.get("credits_remaining", 50)
    st.markdown(f"📦 Paket: **{plan}**")
    st.markdown(f"💳 Kalan Kredi: **{credits}**")
    
    st.divider()
    st.caption("1 persona = 1 kredi")


# ============================================
# ANA İÇERİK
# ============================================
st.markdown("# 🧪 Kampanya Testi")
st.markdown("Reklam metninizi sentetik tüketicilere gösterin, dönüşüm oranını ölçün.")

# ============================================
# KAMPANYA GİRİŞ FORMU
# ============================================
with st.container(border=True):
    st.markdown("### 📝 Kampanya İçeriği")
    
    campaign_content = st.text_area(
        "Kampanya / Reklam Metni",
        height=180,
        placeholder="""Örnek:
🎉 iPhone 15 Pro - Şimdi %30 İNDİRİMLİ!
Sadece 3 gün süreyle geçerli!
✅ 12 aya varan taksit imkanı
✅ Ücretsiz kargo
Normal fiyat: 89.999 TL → ŞİMDİ: 62.999 TL""",
        help="Test etmek istediğiniz reklam metnini, ürün açıklamasını veya kampanya içeriğini buraya yazın."
    )

# ============================================
# FİLTRELER
# ============================================
with st.container(border=True):
    st.markdown("### 🎯 Hedef Kitle Ayarları")
    
    filter_cols = st.columns([1, 1, 1])
    
    # Bölge seçimi - herkese açık
    with filter_cols[0]:
        region = st.selectbox(
            "🌍 Bölge",
            options=["TR", "US", "EU", "MENA"],
            format_func=lambda x: {
                "TR": "🇹🇷 Türkiye",
                "US": "🇺🇸 ABD",
                "EU": "🇪🇺 Avrupa",
                "MENA": "🌙 MENA"
            }.get(x, x),
            help="Persona'ların oluşturulacağı bölge"
        )
    
    # Persona sayısı
    with filter_cols[1]:
        max_p = get_max_personas()
        credits = st.session_state.get("credits_remaining", 50)
        actual_max = min(max_p, credits)
        
        persona_count = st.slider(
            "👥 Persona Sayısı",
            min_value=5,
            max_value=max(5, actual_max),
            value=min(10, actual_max),
            step=5,
            help=f"Paketiniz max {max_p} persona destekler. Kalan krediniz: {credits}"
        )
    
    # Kredi hesabı
    with filter_cols[2]:
        st.markdown("&nbsp;")  # Spacing
        st.markdown(f"""
        **💳 Kredi Kullanımı**  
        {persona_count} persona × 1 kredi = **{persona_count} kredi**
        """)
        if persona_count > credits:
            st.error("⚠️ Yetersiz kredi!")
    
    # Gelişmiş filtreler
    st.markdown("---")
    st.markdown("**🔧 Gelişmiş Filtreler**")
    
    adv_cols = st.columns(4)
    
    # Yaş filtresi
    with adv_cols[0]:
        if is_feature_available("age"):
            age_range = st.slider("📅 Yaş Aralığı", 18, 80, (18, 80))
        else:
            st.slider("📅 Yaş Aralığı 🔒", 18, 80, (18, 80), disabled=True)
            st.caption("🔒 Pro+ pakette açılır")
            age_range = (18, 80)
    
    # Cinsiyet filtresi
    with adv_cols[1]:
        if is_feature_available("gender"):
            gender_filter = st.selectbox(
                "⚥ Cinsiyet",
                ["Tümü", "Erkek", "Kadın"],
            )
        else:
            st.selectbox("⚥ Cinsiyet 🔒", ["Tümü"], disabled=True)
            st.caption("🔒 Pro+ pakette açılır")
            gender_filter = "Tümü"
    
    # Gelir filtresi
    with adv_cols[2]:
        if is_feature_available("income"):
            income_filter = st.selectbox(
                "💰 Gelir Seviyesi",
                ["Tümü", "Düşük", "Orta-Düşük", "Orta", "Orta-Yüksek", "Yüksek"],
            )
        else:
            st.selectbox("💰 Gelir 🔒", ["Tümü"], disabled=True)
            st.caption("🔒 Pro+ pakette açılır")
            income_filter = "Tümü"
    
    # Eğitim filtresi
    with adv_cols[3]:
        if is_feature_available("education"):
            education_filter = st.selectbox(
                "🎓 Eğitim",
                ["Tümü", "İlkokul", "Ortaokul", "Lise", "Ön Lisans", "Üniversite", "Yüksek Lisans", "Doktora"],
            )
        else:
            st.selectbox("🎓 Eğitim 🔒", ["Tümü"], disabled=True)
            st.caption("🔒 Business+ pakette açılır")
            education_filter = "Tümü"


# ============================================
# TEST BAŞLAT
# ============================================
st.markdown("")

col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    test_button = st.button(
        "🚀 Kampanyayı Test Et",
        use_container_width=True,
        type="primary",
        disabled=not campaign_content.strip()
    )

# ============================================
# TEST ÇALIŞTIRMA
# ============================================
if test_button and campaign_content.strip():
    
    # Kredi kontrolü
    credits = st.session_state.get("credits_remaining", 50)
    if persona_count > credits:
        st.error("❌ Yetersiz kredi! Lütfen paketinizi yükseltin.")
        st.stop()
    
    # Persona üretimi
    st.markdown("---")
    
    with st.status("🤖 AI Analiz Çalışıyor...", expanded=True) as status:
        
        # 1. Persona üretimi
        st.write("👥 Persona'lar oluşturuluyor...")
        progress = st.progress(0, text="Persona üretiliyor...")
        
        config = PersonaConfig(
            region=Region(region),
            min_age=age_range[0],
            max_age=age_range[1],
        )
        factory = PersonaFactory(config)
        personas = factory.generate_batch(persona_count)
        
        # Filtreleri uygula
        if gender_filter != "Tümü":
            personas = [p for p in personas if p.gender == gender_filter]
            if not personas:
                st.warning("Filtrelerle eşleşen persona bulunamadı. Filtreler genişletiliyor...")
                personas = factory.generate_batch(persona_count)
        
        if income_filter != "Tümü":
            filtered = [p for p in personas if p.income_level == income_filter]
            if filtered:
                personas = filtered
        
        progress.progress(20, text=f"{len(personas)} persona oluşturuldu ✓")
        time.sleep(0.3)
        
        # 2. LLM Değerlendirmesi
        api_key = st.session_state.get("openai_api_key", "")
        use_real_llm = bool(api_key)
        
        results = []
        yes_count = 0
        no_count = 0
        total_confidence = 0
        
        if use_real_llm:
            # GERÇEK LLM MODU
            st.write("🧠 AI değerlendirmesi yapılıyor...")
            
            try:
                from src.inference.openai_client import SimuTargetLLM
                llm = SimuTargetLLM(api_key=api_key)
                
                for i, persona in enumerate(personas):
                    progress.progress(
                        20 + int((i / len(personas)) * 70),
                        text=f"🎭 {persona.name} değerlendiriyor... ({i+1}/{len(personas)})"
                    )
                    
                    eval_result = llm.evaluate_campaign(
                        persona=persona,
                        campaign_content=campaign_content,
                        campaign_id="streamlit_test",
                    )
                    
                    if eval_result.success and eval_result.decision:
                        decision = eval_result.decision
                        results.append({
                            "persona": persona,
                            "decision": decision.decision,
                            "confidence": decision.confidence,
                            "reasoning": decision.reasoning,
                            "factors": decision.influencing_factors,
                            "anxiety_impact": decision.anxiety_impact,
                        })
                        
                        if decision.decision:
                            yes_count += 1
                        else:
                            no_count += 1
                        total_confidence += decision.confidence
                    else:
                        # Başarısız değerlendirme
                        results.append({
                            "persona": persona,
                            "decision": None,
                            "confidence": 0,
                            "reasoning": eval_result.error or "Değerlendirme başarısız",
                            "factors": [],
                            "anxiety_impact": None,
                        })
                    
                    # Rate limiting - basit bekleme
                    time.sleep(0.3)
                    
            except Exception as e:
                st.error(f"❌ LLM hatası: {e}")
                st.info("💡 Demo moda geçiliyor...")
                use_real_llm = False
                results = []
                yes_count = 0
                no_count = 0
                total_confidence = 0
        
        if not use_real_llm:
            # DEMO MODU - Simüle edilmiş sonuçlar
            st.write("🎮 Demo modu aktif — sonuçlar simüle ediliyor...")
            
            for i, persona in enumerate(personas):
                progress.progress(
                    20 + int((i / len(personas)) * 70),
                    text=f"🎭 {persona.name} değerlendiriyor... ({i+1}/{len(personas)})"
                )
                
                # Gerçekçi simülasyon — persona özelliklerine göre karar
                buy_probability = 0.45  # Base
                
                # Satın alma tarzına göre ayarla
                if persona.buying_style in ["Fırsat Avcısı", "Anlık Alıcı"]:
                    buy_probability += 0.15
                elif persona.buying_style == "Planlı Alıcı":
                    buy_probability -= 0.05
                
                # Gelir seviyesine göre
                if persona.income_level in ["Yüksek", "Orta-Yüksek"]:
                    buy_probability += 0.10
                elif persona.income_level in ["Düşük"]:
                    buy_probability -= 0.10
                
                # Yaşa göre
                if persona.age < 35:
                    buy_probability += 0.05
                elif persona.age > 60:
                    buy_probability -= 0.05
                
                # Kişilik - openness
                buy_probability += (persona.personality.openness - 0.5) * 0.1
                
                # Karar
                decision = random.random() < buy_probability
                confidence = random.randint(4, 9) if decision else random.randint(3, 8)
                
                # Gerekçe oluştur
                if decision:
                    reasons = [
                        f"Fiyat makul görünüyor, {persona.buying_style.lower()} olarak değerlendirdim.",
                        f"{persona.occupation} olarak bu ürüne ihtiyacım var.",
                        f"İndirim oranı dikkat çekici, {persona.financial_behavior.lower()} olarak kaçırmak istemem.",
                        f"Kampanya güvenilir görünüyor, {persona.shopping_preference.lower()} tercihime uyuyor.",
                    ]
                else:
                    reasons = [
                        f"Fiyat bütçeme uygun değil, {persona.income_level.lower()} gelir seviyesindeyim.",
                        f"Şu an böyle bir ürüne ihtiyacım yok.",
                        f"{persona.buying_style.lower()} olarak önce daha fazla araştırma yapmam lazım.",
                        f"Bu tür tekliflere karşı temkinliyim.",
                    ]
                
                factors = []
                if persona.primary_anxiety:
                    factors.append(persona.primary_anxiety.name)
                factors.append(persona.buying_style)
                factors.append(f"Gelir: {persona.income_level}")
                
                results.append({
                    "persona": persona,
                    "decision": decision,
                    "confidence": confidence,
                    "reasoning": random.choice(reasons),
                    "factors": factors,
                    "anxiety_impact": persona.primary_anxiety.name if persona.primary_anxiety and not decision else None,
                })
                
                if decision:
                    yes_count += 1
                else:
                    no_count += 1
                total_confidence += confidence
                
                time.sleep(0.05)  # Demo animasyon
        
        progress.progress(95, text="📊 Sonuçlar hazırlanıyor...")
        time.sleep(0.3)
        
        # Kredi düşür
        st.session_state["credits_remaining"] = credits - persona_count
        
        progress.progress(100, text="✅ Analiz tamamlandı!")
        status.update(label="✅ Analiz Tamamlandı!", state="complete")
    
    # ============================================
    # SONUÇLAR
    # ============================================
    st.markdown("---")
    st.markdown("## 📊 Sonuçlar")
    
    if not use_real_llm:
        st.info("🎮 **Demo Modu** — Bu sonuçlar simüle edilmiştir. Gerçek AI analizi için API Key girin.")
    
    # Genel Metrikler
    successful = [r for r in results if r["decision"] is not None]
    total_tested = len(successful)
    conversion = (yes_count / total_tested * 100) if total_tested > 0 else 0
    avg_conf = (total_confidence / total_tested) if total_tested > 0 else 0
    
    metric_cols = st.columns(4)
    
    with metric_cols[0]:
        st.markdown(f"""
        <div class="result-card">
            <div class="big-metric metric-blue">{total_tested}</div>
            <div style="text-align:center; color:#94a3b8;">Toplam Persona</div>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_cols[1]:
        color_class = "metric-green" if conversion >= 50 else "metric-yellow" if conversion >= 30 else "metric-red"
        st.markdown(f"""
        <div class="result-card">
            <div class="big-metric {color_class}">{conversion:.1f}%</div>
            <div style="text-align:center; color:#94a3b8;">Dönüşüm Oranı</div>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_cols[2]:
        st.markdown(f"""
        <div class="result-card">
            <div class="big-metric metric-green">{yes_count}</div>
            <div style="text-align:center; color:#94a3b8;">EVET</div>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_cols[3]:
        st.markdown(f"""
        <div class="result-card">
            <div class="big-metric metric-red">{no_count}</div>
            <div style="text-align:center; color:#94a3b8;">HAYIR</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Grafikler
    st.markdown("### 📈 Görsel Analiz")
    chart_cols = st.columns(2)
    
    with chart_cols[0]:
        # Pasta grafik
        import plotly.express as px
        import pandas as pd
        
        pie_data = pd.DataFrame({
            "Karar": ["EVET ✅", "HAYIR ❌"],
            "Sayı": [yes_count, no_count],
        })
        fig_pie = px.pie(
            pie_data, values="Sayı", names="Karar",
            color_discrete_sequence=["#34d399", "#f87171"],
            title="Karar Dağılımı",
            hole=0.4,
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with chart_cols[1]:
        # Güven dağılımı
        conf_data = pd.DataFrame({
            "Güven": [r["confidence"] for r in successful],
            "Karar": ["EVET" if r["decision"] else "HAYIR" for r in successful],
        })
        fig_conf = px.histogram(
            conf_data, x="Güven", color="Karar",
            color_discrete_map={"EVET": "#34d399", "HAYIR": "#f87171"},
            title="Güven Skoru Dağılımı",
            nbins=10,
            barmode="overlay",
        )
        fig_conf.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
            xaxis_title="Güven Skoru (1-10)",
            yaxis_title="Persona Sayısı",
        )
        st.plotly_chart(fig_conf, use_container_width=True)
    
    # Segment Analizi (Business+)
    if is_feature_available("segment_analysis"):
        st.markdown("### 🔍 Segment Analizi")
        
        seg_cols = st.columns(3)
        
        # Yaş gruplarına göre
        with seg_cols[0]:
            age_groups = {"18-24": [], "25-34": [], "35-44": [], "45-54": [], "55+": []}
            for r in successful:
                age = r["persona"].age
                if age < 25:
                    age_groups["18-24"].append(r["decision"])
                elif age < 35:
                    age_groups["25-34"].append(r["decision"])
                elif age < 45:
                    age_groups["35-44"].append(r["decision"])
                elif age < 55:
                    age_groups["45-54"].append(r["decision"])
                else:
                    age_groups["55+"].append(r["decision"])
            
            age_conv = {}
            for group, decisions in age_groups.items():
                if decisions:
                    age_conv[group] = sum(decisions) / len(decisions) * 100
            
            if age_conv:
                age_df = pd.DataFrame({
                    "Yaş Grubu": list(age_conv.keys()),
                    "Dönüşüm %": list(age_conv.values()),
                })
                fig_age = px.bar(
                    age_df, x="Yaş Grubu", y="Dönüşüm %",
                    color="Dönüşüm %",
                    color_continuous_scale=["#f87171", "#fbbf24", "#34d399"],
                    title="Yaş Gruplarına Göre Dönüşüm",
                )
                fig_age.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#e2e8f0",
                    showlegend=False,
                )
                st.plotly_chart(fig_age, use_container_width=True)
        
        # Gelir seviyesine göre
        with seg_cols[1]:
            income_groups = {}
            for r in successful:
                inc = r["persona"].income_level
                if inc not in income_groups:
                    income_groups[inc] = []
                income_groups[inc].append(r["decision"])
            
            income_conv = {}
            for group, decisions in income_groups.items():
                if decisions:
                    income_conv[group] = sum(decisions) / len(decisions) * 100
            
            if income_conv:
                inc_df = pd.DataFrame({
                    "Gelir": list(income_conv.keys()),
                    "Dönüşüm %": list(income_conv.values()),
                })
                fig_inc = px.bar(
                    inc_df, x="Gelir", y="Dönüşüm %",
                    color="Dönüşüm %",
                    color_continuous_scale=["#f87171", "#fbbf24", "#34d399"],
                    title="Gelir Seviyesine Göre Dönüşüm",
                )
                fig_inc.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#e2e8f0",
                    showlegend=False,
                )
                st.plotly_chart(fig_inc, use_container_width=True)
        
        # Cinsiyet
        with seg_cols[2]:
            gender_groups = {}
            for r in successful:
                g = r["persona"].gender
                if g not in gender_groups:
                    gender_groups[g] = []
                gender_groups[g].append(r["decision"])
            
            gender_conv = {}
            for group, decisions in gender_groups.items():
                if decisions:
                    gender_conv[group] = sum(decisions) / len(decisions) * 100
            
            if gender_conv:
                gen_df = pd.DataFrame({
                    "Cinsiyet": list(gender_conv.keys()),
                    "Dönüşüm %": list(gender_conv.values()),
                })
                fig_gen = px.bar(
                    gen_df, x="Cinsiyet", y="Dönüşüm %",
                    color="Dönüşüm %",
                    color_continuous_scale=["#f87171", "#fbbf24", "#34d399"],
                    title="Cinsiyete Göre Dönüşüm",
                )
                fig_gen.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#e2e8f0",
                    showlegend=False,
                )
                st.plotly_chart(fig_gen, use_container_width=True)
    else:
        st.markdown("### 🔍 Segment Analizi 🔒")
        st.info("📊 Yaş, gelir ve cinsiyet bazlı segment analizi **Business** ve üstü paketlerde kullanılabilir.")
    
    # Kişi Bazlı Sonuçlar
    st.markdown("### 📋 Kişi Bazlı Sonuçlar")
    
    if is_feature_available("detailed_report"):
        for r in successful:
            p = r["persona"]
            emoji = "✅" if r["decision"] else "❌"
            karar = "EVET" if r["decision"] else "HAYIR"
            css_class = "persona-yes" if r["decision"] else "persona-no"
            
            with st.expander(f"{emoji} {p.name} — {p.age} yaş, {p.occupation} ({p.city}) — Güven: {r['confidence']}/10"):
                detail_cols = st.columns([1, 1, 1])
                
                with detail_cols[0]:
                    st.markdown("**📋 Profil**")
                    st.markdown(f"- Yaş: {p.age}")
                    st.markdown(f"- Cinsiyet: {p.gender}")
                    st.markdown(f"- Gelir: {p.income_level}")
                    st.markdown(f"- Eğitim: {p.education}")
                    st.markdown(f"- Medeni durum: {p.marital_status}")
                
                with detail_cols[1]:
                    st.markdown("**🛒 Tüketici Profili**")
                    st.markdown(f"- Alışveriş: {p.buying_style}")
                    st.markdown(f"- Teknoloji: {p.tech_adoption}")
                    st.markdown(f"- Finansal: {p.financial_behavior}")
                    if p.primary_anxiety:
                        st.markdown(f"- Profil: {p.primary_anxiety.name}")
                
                with detail_cols[2]:
                    st.markdown("**💬 Değerlendirme**")
                    st.markdown(f"**Karar:** {emoji} {karar}")
                    st.markdown(f"**Güven:** {r['confidence']}/10")
                    st.markdown(f"**Gerekçe:** {r['reasoning']}")
                    if r["anxiety_impact"]:
                        st.markdown(f"**Endişe etkisi:** {r['anxiety_impact']}")
    else:
        # Basic plan - basit tablo
        st.info("💡 Detaylı kişi bazlı analiz **Pro** ve üstü paketlerde kullanılabilir.")
        
        basic_data = []
        for r in successful:
            p = r["persona"]
            basic_data.append({
                "Persona": p.name,
                "Yaş": p.age,
                "Şehir": p.city,
                "Karar": "✅ EVET" if r["decision"] else "❌ HAYIR",
                "Güven": f"{r['confidence']}/10",
            })
        
        st.dataframe(
            pd.DataFrame(basic_data),
            use_container_width=True,
            hide_index=True,
        )
    
    # PDF Export (Pro+)
    st.markdown("---")
    if is_feature_available("pdf_export"):
        if st.button("📥 PDF Rapor İndir", type="secondary"):
            st.info("📄 PDF rapor özelliği yakında aktif olacak!")
    else:
        st.button("📥 PDF Rapor İndir 🔒", disabled=True, help="Pro ve üstü paketlerde kullanılabilir.")
    
    # Sonuçları session'a kaydet
    st.session_state["last_test_results"] = {
        "campaign": campaign_content,
        "region": region,
        "persona_count": total_tested,
        "conversion_rate": conversion,
        "avg_confidence": avg_conf,
        "yes_count": yes_count,
        "no_count": no_count,
        "results": results,
        "timestamp": time.strftime("%Y-%m-%d %H:%M"),
    }
