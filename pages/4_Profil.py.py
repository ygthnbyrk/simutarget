"""
SimuTarget.ai - Profil & Ayarlar
"""

import streamlit as st

st.set_page_config(page_title="Profil - SimuTarget.ai", page_icon="👤", layout="wide")

with st.sidebar:
    st.markdown("## 🎯 SimuTarget.ai")
    st.markdown("*Profil*")

st.markdown("# 👤 Profil & Ayarlar")

# Paket bilgisi
st.markdown("### 📦 Mevcut Paket")

plan = st.session_state.get("user_plan", "Basic")
plans_info = {
    "Basic": {"price": "$4.99/ay", "credits": 50, "features": ["Bölge seçimi", "Basit sonuç tablosu"]},
    "Pro": {"price": "$9.99/ay", "credits": 100, "features": ["Tüm temel filtreler", "PDF rapor", "Detaylı persona analizi"]},
    "Business": {"price": "$19.99/ay", "credits": 250, "features": ["Tüm filtreler", "Segment analizi", "Dashboard", "PDF rapor"]},
    "Enterprise": {"price": "$49.99/ay", "credits": "Sınırsız", "features": ["Her şey", "5 kişiye kadar ekip", "Danışmanlık"]},
}

info = plans_info.get(plan, plans_info["Basic"])

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**Paket:** {plan}")
    st.markdown(f"**Fiyat:** {info['price']}")
    st.markdown(f"**Aylık Kredi:** {info['credits']}")

with col2:
    st.markdown("**Özellikler:**")
    for f in info["features"]:
        st.markdown(f"- ✅ {f}")

st.divider()

# Paket karşılaştırma
st.markdown("### 📊 Paket Karşılaştırma")

import pandas as pd

comparison = pd.DataFrame({
    "Özellik": ["Fiyat", "Aylık Kredi", "Bölge Seçimi", "Yaş/Gelir Filtresi", "Eğitim/Meslek Filtresi", 
                 "PDF Rapor", "Segment Analizi", "Ekip Kullanımı", "Danışmanlık"],
    "Basic": ["$4.99", "50", "✅", "❌", "❌", "❌", "❌", "❌", "❌"],
    "Pro": ["$9.99", "100", "✅", "✅", "❌", "✅", "❌", "❌", "❌"],
    "Business": ["$19.99", "250", "✅", "✅", "✅", "✅", "✅", "❌", "❌"],
    "Enterprise": ["$49.99", "∞", "✅", "✅", "✅", "✅", "✅", "✅ (5 kişi)", "✅"],
})

st.dataframe(comparison, use_container_width=True, hide_index=True)

st.divider()

# Demo ayarları
st.markdown("### ⚙️ Demo Ayarları")
st.caption("Demo modda paket değiştirip farklı özellik kısıtlamalarını test edebilirsiniz.")

demo_plan = st.selectbox("Paket Değiştir", ["Basic", "Pro", "Business", "Enterprise"], 
                         index=["Basic", "Pro", "Business", "Enterprise"].index(plan))

if demo_plan != plan:
    if st.button("Paketi Değiştir", type="primary"):
        max_credits = {"Basic": 50, "Pro": 100, "Business": 250, "Enterprise": 999}
        st.session_state["user_plan"] = demo_plan
        st.session_state["credits_remaining"] = max_credits.get(demo_plan, 50)
        st.success(f"✅ Paket {demo_plan} olarak değiştirildi!")
        st.rerun()
