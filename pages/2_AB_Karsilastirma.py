"""
SimuTarget.ai - A/B Karşılaştırma Sayfası
İki kampanyayı yan yana test eder.
"""

import streamlit as st
import sys
import os
import time
import random
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.personas.models import Persona, PersonaConfig, Region, Gender
from src.personas.factory import PersonaFactory

st.set_page_config(
    page_title="A/B Karşılaştırma - SimuTarget.ai",
    page_icon="⚔️",
    layout="wide",
)

st.markdown("""
<style>
    .vs-badge {
        background: linear-gradient(135deg, #7c3aed, #6366f1);
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 20px;
        font-size: 1.2rem;
        font-weight: 700;
        text-align: center;
        display: inline-block;
    }
    .winner-card {
        background: linear-gradient(135deg, #064e3b, #065f46);
        border: 2px solid #34d399;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
    .loser-card {
        background: linear-gradient(135deg, #1e293b, #334155);
        border: 1px solid #475569;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🎯 SimuTarget.ai")
    st.markdown("*A/B Karşılaştırma*")
    st.divider()
    
    api_key = st.session_state.get("openai_api_key", "")
    if not api_key:
        new_key = st.text_input("🔑 OpenAI API Key", type="password", placeholder="sk-...")
        if new_key:
            st.session_state["openai_api_key"] = new_key
            st.rerun()
        st.info("💡 Demo mod aktif")
    else:
        st.success("✅ API Key aktif")
    
    st.divider()
    plan = st.session_state.get("user_plan", "Basic")
    credits = st.session_state.get("credits_remaining", 50)
    st.markdown(f"📦 Paket: **{plan}**")
    st.markdown(f"💳 Kalan Kredi: **{credits}**")

# Ana İçerik
st.markdown("# ⚔️ A/B Karşılaştırma")
st.markdown("İki kampanyayı aynı persona grubuna gösterin, hangisinin daha etkili olduğunu görün.")

# Kampanya girişleri
camp_cols = st.columns([5, 1, 5])

with camp_cols[0]:
    st.markdown("### 🔵 Seçenek A")
    campaign_a = st.text_area(
        "Kampanya A",
        height=200,
        placeholder="İlk kampanya metnini buraya yazın...",
        key="campaign_a",
        label_visibility="collapsed",
    )

with camp_cols[1]:
    st.markdown("")
    st.markdown("")
    st.markdown("")
    st.markdown('<div style="text-align:center"><span class="vs-badge">VS</span></div>', unsafe_allow_html=True)

with camp_cols[2]:
    st.markdown("### 🔴 Seçenek B")
    campaign_b = st.text_area(
        "Kampanya B",
        height=200,
        placeholder="İkinci kampanya metnini buraya yazın...",
        key="campaign_b",
        label_visibility="collapsed",
    )

# Ayarlar
with st.container(border=True):
    set_cols = st.columns(3)
    with set_cols[0]:
        region = st.selectbox(
            "🌍 Bölge",
            ["TR", "US", "EU", "MENA"],
            format_func=lambda x: {"TR": "🇹🇷 Türkiye", "US": "🇺🇸 ABD", "EU": "🇪🇺 Avrupa", "MENA": "🌙 MENA"}.get(x, x),
        )
    with set_cols[1]:
        credits = st.session_state.get("credits_remaining", 50)
        persona_count = st.slider("👥 Persona Sayısı", 5, min(50, credits), min(10, credits), step=5)
    with set_cols[2]:
        st.markdown(f"**💳 Kredi:** {persona_count * 2} kredi (×2 kampanya)")

# Test butonu
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    test_btn = st.button(
        "⚔️ Karşılaştırmayı Başlat",
        use_container_width=True,
        type="primary",
        disabled=not (campaign_a.strip() and campaign_b.strip()),
    )

if test_btn and campaign_a.strip() and campaign_b.strip():
    
    credits = st.session_state.get("credits_remaining", 50)
    needed = persona_count * 2
    if needed > credits:
        st.error(f"❌ Yetersiz kredi! Gereken: {needed}, Kalan: {credits}")
        st.stop()
    
    st.markdown("---")
    
    with st.status("🤖 A/B Test Çalışıyor...", expanded=True) as status:
        
        # Persona üretimi
        st.write("👥 Persona'lar oluşturuluyor...")
        progress = st.progress(0)
        
        config = PersonaConfig(region=Region(region))
        factory = PersonaFactory(config)
        personas = factory.generate_batch(persona_count)
        
        progress.progress(15, text=f"{len(personas)} persona oluşturuldu ✓")
        
        # Her iki kampanya için değerlendirme
        api_key = st.session_state.get("openai_api_key", "")
        use_real_llm = bool(api_key)
        
        results_a = []
        results_b = []
        
        if use_real_llm:
            try:
                from src.inference.openai_client import SimuTargetLLM
                llm = SimuTargetLLM(api_key=api_key)
                
                for i, persona in enumerate(personas):
                    pct = 15 + int((i / len(personas)) * 75)
                    progress.progress(pct, text=f"🎭 {persona.name} değerlendiriyor... ({i+1}/{len(personas)})")
                    
                    # A değerlendirmesi
                    eval_a = llm.evaluate_campaign(persona=persona, campaign_content=campaign_a, campaign_id="ab_test_a")
                    # B değerlendirmesi
                    eval_b = llm.evaluate_campaign(persona=persona, campaign_content=campaign_b, campaign_id="ab_test_b")
                    
                    if eval_a.success and eval_a.decision:
                        results_a.append({"decision": eval_a.decision.decision, "confidence": eval_a.decision.confidence, "persona": persona})
                    if eval_b.success and eval_b.decision:
                        results_b.append({"decision": eval_b.decision.decision, "confidence": eval_b.decision.confidence, "persona": persona})
                    
                    time.sleep(0.3)
            except Exception as e:
                st.error(f"LLM hatası: {e}")
                use_real_llm = False
        
        if not use_real_llm:
            st.write("🎮 Demo modu — sonuçlar simüle ediliyor...")
            
            for i, persona in enumerate(personas):
                pct = 15 + int((i / len(personas)) * 75)
                progress.progress(pct, text=f"🎭 {persona.name} değerlendiriyor... ({i+1}/{len(personas)})")
                
                # A simülasyonu
                prob_a = 0.45 + random.uniform(-0.15, 0.15)
                if persona.buying_style in ["Fırsat Avcısı", "Anlık Alıcı"]:
                    prob_a += 0.10
                dec_a = random.random() < prob_a
                results_a.append({"decision": dec_a, "confidence": random.randint(3, 9), "persona": persona})
                
                # B simülasyonu - biraz farklı
                prob_b = 0.40 + random.uniform(-0.15, 0.15)
                if persona.income_level in ["Yüksek", "Orta-Yüksek"]:
                    prob_b += 0.10
                dec_b = random.random() < prob_b
                results_b.append({"decision": dec_b, "confidence": random.randint(3, 9), "persona": persona})
                
                time.sleep(0.03)
        
        # Kredi düşür
        st.session_state["credits_remaining"] = credits - needed
        
        progress.progress(100, text="✅ Analiz tamamlandı!")
        status.update(label="✅ A/B Test Tamamlandı!", state="complete")
    
    # Sonuçlar
    st.markdown("---")
    st.markdown("## 📊 Karşılaştırma Sonuçları")
    
    if not use_real_llm:
        st.info("🎮 **Demo Modu** aktif")
    
    yes_a = sum(1 for r in results_a if r["decision"])
    yes_b = sum(1 for r in results_b if r["decision"])
    conv_a = (yes_a / len(results_a) * 100) if results_a else 0
    conv_b = (yes_b / len(results_b) * 100) if results_b else 0
    avg_conf_a = sum(r["confidence"] for r in results_a) / len(results_a) if results_a else 0
    avg_conf_b = sum(r["confidence"] for r in results_b) / len(results_b) if results_b else 0
    
    winner = "A" if conv_a > conv_b else "B" if conv_b > conv_a else "Berabere"
    
    # Kazanan banner
    if winner != "Berabere":
        winner_color = "#34d399"
        winner_emoji = "🔵" if winner == "A" else "🔴"
        st.success(f"🏆 **Kazanan: Seçenek {winner}** — {max(conv_a, conv_b):.1f}% dönüşüm oranı ile!")
    else:
        st.info("🤝 **Berabere!** İki kampanya benzer performans gösterdi.")
    
    # Karşılaştırma kartları
    res_cols = st.columns(2)
    
    with res_cols[0]:
        card_class = "winner-card" if winner == "A" else "loser-card"
        st.markdown(f"""
        <div class="{card_class}">
            <h2>🔵 Seçenek A {'🏆' if winner == 'A' else ''}</h2>
            <div style="font-size:2.5rem; font-weight:800; color:{'#34d399' if winner == 'A' else '#94a3b8'};">{conv_a:.1f}%</div>
            <div style="color:#94a3b8;">Dönüşüm Oranı</div>
        </div>
        """, unsafe_allow_html=True)
        st.metric("EVET", yes_a, delta=f"{yes_a - yes_b:+d}" if winner != "Berabere" else None)
        st.metric("Ort. Güven", f"{avg_conf_a:.1f}/10")
    
    with res_cols[1]:
        card_class = "winner-card" if winner == "B" else "loser-card"
        st.markdown(f"""
        <div class="{card_class}">
            <h2>🔴 Seçenek B {'🏆' if winner == 'B' else ''}</h2>
            <div style="font-size:2.5rem; font-weight:800; color:{'#34d399' if winner == 'B' else '#94a3b8'};">{conv_b:.1f}%</div>
            <div style="color:#94a3b8;">Dönüşüm Oranı</div>
        </div>
        """, unsafe_allow_html=True)
        st.metric("EVET", yes_b, delta=f"{yes_b - yes_a:+d}" if winner != "Berabere" else None)
        st.metric("Ort. Güven", f"{avg_conf_b:.1f}/10")
    
    # Karşılaştırma grafik
    import plotly.graph_objects as go
    
    fig = go.Figure(data=[
        go.Bar(name="🔵 Seçenek A", x=["EVET", "HAYIR", "Dönüşüm %"], 
               y=[yes_a, len(results_a) - yes_a, conv_a], marker_color="#38bdf8"),
        go.Bar(name="🔴 Seçenek B", x=["EVET", "HAYIR", "Dönüşüm %"], 
               y=[yes_b, len(results_b) - yes_b, conv_b], marker_color="#f87171"),
    ])
    fig.update_layout(
        barmode="group",
        title="A vs B Karşılaştırma",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0",
    )
    st.plotly_chart(fig, use_container_width=True)
