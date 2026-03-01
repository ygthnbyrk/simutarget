"""
SimuTarget.ai - Dashboard
Geçmiş testler ve performans metrikleri.
"""

import streamlit as st

st.set_page_config(page_title="Dashboard - SimuTarget.ai", page_icon="📊", layout="wide")

with st.sidebar:
    st.markdown("## 🎯 SimuTarget.ai")
    st.markdown("*Dashboard*")
    st.divider()
    plan = st.session_state.get("user_plan", "Basic")
    credits = st.session_state.get("credits_remaining", 50)
    st.markdown(f"📦 Paket: **{plan}**")
    st.markdown(f"💳 Kalan Kredi: **{credits}**")

st.markdown("# 📊 Dashboard")

# Son test sonucu varsa göster
last_test = st.session_state.get("last_test_results")

if last_test:
    st.markdown("### 🕐 Son Test Sonucu")
    st.markdown(f"*{last_test.get('timestamp', 'N/A')}*")
    
    cols = st.columns(4)
    with cols[0]:
        st.metric("Bölge", last_test.get("region", "N/A"))
    with cols[1]:
        st.metric("Persona Sayısı", last_test.get("persona_count", 0))
    with cols[2]:
        st.metric("Dönüşüm", f"{last_test.get('conversion_rate', 0):.1f}%")
    with cols[3]:
        st.metric("EVET / HAYIR", f"{last_test.get('yes_count', 0)} / {last_test.get('no_count', 0)}")
    
    with st.expander("📝 Kampanya Metni"):
        st.text(last_test.get("campaign", ""))
    
    st.divider()

# Kredi kullanımı
st.markdown("### 💳 Kredi Kullanımı")

plan = st.session_state.get("user_plan", "Basic")
max_credits = {"Basic": 50, "Pro": 100, "Business": 250, "Enterprise": 999}
total = max_credits.get(plan, 50)
remaining = st.session_state.get("credits_remaining", total)
used = total - remaining

col1, col2 = st.columns(2)
with col1:
    st.progress(remaining / total if total > 0 else 0)
    st.markdown(f"**{remaining}** / {total} kredi kalan")
with col2:
    st.markdown(f"Kullanılan: **{used}** kredi")
    st.markdown(f"Paket: **{plan}**")

if remaining < total * 0.2:
    st.warning("⚠️ Krediniz azalıyor! Paket yükseltme düşünebilirsiniz.")

st.divider()

# Boş durum
if not last_test:
    st.markdown("""
    <div style="text-align:center; padding:3rem; color:#64748b;">
        <h2>🧪</h2>
        <p>Henüz bir test yapmadınız.</p>
        <p>Kampanya Testi sayfasından ilk testinizi başlatın!</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🧪 İlk Testimi Yap →", type="primary"):
        st.switch_page("pages/1_🧪_Kampanya_Testi.py")
