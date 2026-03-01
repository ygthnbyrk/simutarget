"""
SimuTarget.ai - AI-Powered Synthetic Market Research Platform
Main Streamlit Application
"""

import streamlit as st

# ============================================
# PAGE CONFIG - Must be first Streamlit command
# ============================================
st.set_page_config(
    page_title="SimuTarget.ai",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================
# CUSTOM CSS
# ============================================
st.markdown("""
<style>
    /* Ana tema */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Sidebar stil */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] .stMarkdown span {
        color: #e2e8f0 !important;
    }
    
    /* Metrik kartlar */
    .metric-card {
        background: linear-gradient(135deg, #1e293b, #334155);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        border: 1px solid #475569;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-top: 0.3rem;
    }
    
    /* Hero section */
    .hero-section {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
        border-radius: 16px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        border: 1px solid #1e40af;
        text-align: center;
    }
    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .hero-subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
    }
    
    /* Feature cards */
    .feature-card {
        background: #1e293b;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #334155;
        height: 100%;
    }
    .feature-card h3 {
        color: #f1f5f9;
        margin-bottom: 0.5rem;
    }
    .feature-card p {
        color: #94a3b8;
        font-size: 0.9rem;
    }
    
    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .status-active {
        background: #064e3b;
        color: #34d399;
    }
    .status-inactive {
        background: #7f1d1d;
        color: #fca5a5;
    }
    
    /* Genel buton stilleri */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #38bdf8, #818cf8);
    }
    
    /* Kilitli özellik */
    .locked-feature {
        position: relative;
        opacity: 0.5;
        pointer-events: none;
    }
    .lock-overlay {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0,0,0,0.7);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        color: #fbbf24;
        font-size: 0.85rem;
        z-index: 10;
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("## 🎯 SimuTarget.ai")
    st.markdown("*AI-Powered Market Research*")
    st.divider()
    
    # API Key kontrolü
    api_key = st.text_input(
        "🔑 OpenAI API Key",
        type="password",
        placeholder="sk-...",
        help="Kampanya testi için OpenAI API anahtarı gereklidir."
    )
    
    if api_key:
        st.session_state["openai_api_key"] = api_key
        st.success("✅ API Key ayarlandı")
    elif "openai_api_key" not in st.session_state:
        st.warning("⚠️ API Key girilmedi. Demo mod aktif.")
    
    st.divider()
    
    # Kullanıcı bilgisi (şimdilik mock)
    st.markdown("### 👤 Hesap")
    st.markdown("**Demo Kullanıcı**")
    
    # Paket bilgisi
    current_plan = st.session_state.get("user_plan", "Basic")
    plan_colors = {"Basic": "🟢", "Pro": "🔵", "Business": "🟣", "Enterprise": "🟡"}
    st.markdown(f"{plan_colors.get(current_plan, '⚪')} Paket: **{current_plan}**")
    
    # Kredi bilgisi
    credits = st.session_state.get("credits_remaining", 50)
    max_credits = {"Basic": 50, "Pro": 100, "Business": 250, "Enterprise": 999}
    st.progress(credits / max_credits.get(current_plan, 50))
    st.markdown(f"💳 Kalan Kredi: **{credits}** / {max_credits.get(current_plan, 50)}")
    
    st.divider()
    
    # Demo paket değiştirme
    st.markdown("### ⚙️ Demo Ayarları")
    demo_plan = st.selectbox(
        "Paket Simülasyonu",
        ["Basic", "Pro", "Business", "Enterprise"],
        help="Farklı paketlerin özelliklerini test etmek için"
    )
    if demo_plan != current_plan:
        st.session_state["user_plan"] = demo_plan
        st.session_state["credits_remaining"] = max_credits.get(demo_plan, 50)
        st.rerun()


# ============================================
# ANA SAYFA İÇERİĞİ
# ============================================

# Hero Section
st.markdown("""
<div class="hero-section">
    <div class="hero-title">SimuTarget.ai</div>
    <div class="hero-subtitle">
        Yapay zeka destekli sentetik pazar araştırma platformu.<br>
        Kampanyalarınızı gerçek tüketicilere göstermeden önce test edin.
    </div>
</div>
""", unsafe_allow_html=True)

# Hızlı erişim butonları
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>🧪 Kampanya Testi</h3>
        <p>Reklam metninizi sentetik persona'lara gösterin, dönüşüm oranını ölçün.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Kampanya Test Et →", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Kampanya_Testi.py")

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>⚔️ A/B Karşılaştırma</h3>
        <p>İki kampanyayı karşılaştırın, hangisinin daha etkili olduğunu görün.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("A/B Test →", use_container_width=True):
        st.switch_page("pages/2_AB_Karsilastirma.py")

with col3:
    st.markdown("""
    <div class="feature-card">
        <h3>📊 Dashboard</h3>
        <p>Geçmiş testlerinizi ve performans metriklerinizi inceleyin.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Dashboard →", use_container_width=True):
        st.switch_page("pages/3_Dashboard.py")

st.divider()

# Nasıl çalışır
st.markdown("### 🔄 Nasıl Çalışır?")

steps = st.columns(4)
with steps[0]:
    st.markdown("**1️⃣ Kampanya Girin**")
    st.caption("Reklam metni, ürün açıklaması veya kampanya içeriğinizi yazın.")

with steps[1]:
    st.markdown("**2️⃣ Hedef Kitle Seçin**")
    st.caption("Bölge, yaş aralığı, gelir seviyesi gibi filtreleri belirleyin.")

with steps[2]:
    st.markdown("**3️⃣ AI Analiz Eder**")
    st.caption("Sentetik persona'lar kampanyanızı değerlendirir.")

with steps[3]:
    st.markdown("**4️⃣ Sonuçları Görün**")
    st.caption("Dönüşüm oranı, güven skoru ve detaylı analiz raporu alın.")

st.divider()

# İstatistikler
st.markdown("### 📈 Platform İstatistikleri")
stat_cols = st.columns(4)

with stat_cols[0]:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-value">4</div>
        <div class="metric-label">Desteklenen Bölge</div>
    </div>
    """, unsafe_allow_html=True)

with stat_cols[1]:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-value">34</div>
        <div class="metric-label">Persona Alanı</div>
    </div>
    """, unsafe_allow_html=True)

with stat_cols[2]:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-value">AI</div>
        <div class="metric-label">LLM Destekli</div>
    </div>
    """, unsafe_allow_html=True)

with stat_cols[3]:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-value">∞</div>
        <div class="metric-label">A/B Test</div>
    </div>
    """, unsafe_allow_html=True)
