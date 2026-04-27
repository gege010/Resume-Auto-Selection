"""
Resume Auto-Selection DSS — Streamlit Home Page
"""
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Resume Auto-Selection DSS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark glassmorphism sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0f0c29, #302b63, #24243e);
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label {
    color: #e0e0e0 !important;
}

/* Hero gradient */
.hero-banner {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
    border-radius: 16px;
    padding: 3rem 2rem;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
}
.hero-banner h1 {
    color: white;
    font-size: 2.8rem;
    font-weight: 700;
    margin: 0;
    text-shadow: 0 2px 10px rgba(0,0,0,0.3);
}
.hero-banner p {
    color: rgba(255,255,255,0.9);
    font-size: 1.15rem;
    margin-top: 0.75rem;
}

/* Feature cards */
.feature-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid rgba(102, 126, 234, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
    cursor: pointer;
}
.feature-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(102, 126, 234, 0.3);
}
.feature-card h3 { color: #a78bfa; margin: 0.5rem 0 0.25rem; }
.feature-card p  { color: #94a3b8; font-size: 0.9rem; margin: 0; }

/* Metric cards */
.metric-row { display: flex; gap: 1rem; }
.metric-box {
    flex: 1;
    background: linear-gradient(135deg, #1e3a5f, #0f2027);
    border: 1px solid rgba(96, 165, 250, 0.3);
    border-radius: 10px;
    padding: 1.2rem;
    text-align: center;
}
.metric-box .val { font-size: 2rem; font-weight: 700; color: #60a5fa; }
.metric-box .lbl { font-size: 0.8rem; color: #94a3b8; margin-top: 0.2rem; }

/* Status badge */
.badge-ok  { background:#064e3b; color:#34d399; padding:2px 10px; border-radius:99px; font-size:0.8rem; }
.badge-err { background:#7f1d1d; color:#f87171; padding:2px 10px; border-radius:99px; font-size:0.8rem; }

/* Step guide */
.step-item {
    display: flex; align-items: flex-start; gap: 1rem;
    margin-bottom: 1rem;
}
.step-num {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white; font-weight: 700; width:32px; height:32px;
    border-radius: 50%; display:flex; align-items:center;
    justify-content:center; flex-shrink:0; font-size:0.9rem;
}
.step-text h4 { color: #e2e8f0; margin: 0 0 0.2rem; }
.step-text p  { color: #94a3b8; margin: 0; font-size:0.88rem; }
</style>
""", unsafe_allow_html=True)


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
  <h1>🧠 Resume Auto-Selection DSS</h1>
  <p>Multi-Criteria Decision Support System · SAW + WP + TOPSIS Ensemble · AI-Powered Resume Analysis</p>
</div>
""", unsafe_allow_html=True)


# ── DB Status ─────────────────────────────────────────────────────────────────
col_status, col_spacer = st.columns([1, 3])
with col_status:
    with st.spinner("Checking database…"):
        try:
            from db.supabase_client import check_connection
            ok = check_connection()
            badge = '<span class="badge-ok">● Supabase Connected</span>' if ok else \
                    '<span class="badge-err">● Supabase Disconnected</span>'
        except Exception:
            badge = '<span class="badge-err">● Supabase Not Configured</span>'
    st.markdown(badge, unsafe_allow_html=True)


# ── Live Metrics ───────────────────────────────────────────────────────────────
st.markdown("### 📊 Session Overview")
try:
    from db.repositories import list_vacancies
    vacancies = list_vacancies()
    n_vacancies = len(vacancies)
except Exception:
    n_vacancies = 0

st.markdown(f"""
<div class="metric-row">
  <div class="metric-box"><div class="val">{n_vacancies}</div><div class="lbl">Job Vacancies</div></div>
  <div class="metric-box"><div class="val">SAW + WP + TOPSIS</div><div class="lbl">Algorithms</div></div>
  <div class="metric-box"><div class="val">Borda Count</div><div class="lbl">Ensemble Method</div></div>
  <div class="metric-box"><div class="val">AHP</div><div class="lbl">Weight Derivation</div></div>
</div>
""", unsafe_allow_html=True)


# ── Feature Cards ─────────────────────────────────────────────────────────────
st.markdown("### 🚀 Features")
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown("""<div class="feature-card">
        <div style="font-size:2rem">💼</div>
        <h3>Job Manager</h3>
        <p>Create & manage vacancies with job family templates</p>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown("""<div class="feature-card">
        <div style="font-size:2rem">📄</div>
        <h3>Resume Upload</h3>
        <p>Upload PDF resumes — AI parses them automatically</p>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown("""<div class="feature-card">
        <div style="font-size:2rem">⚖️</div>
        <h3>AHP Wizard</h3>
        <p>Derive criteria weights via pairwise comparison</p>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown("""<div class="feature-card">
        <div style="font-size:2rem">⚡</div>
        <h3>Run Analysis</h3>
        <p>Execute ensemble MCDM on all candidates</p>
    </div>""", unsafe_allow_html=True)

with c5:
    st.markdown("""<div class="feature-card">
        <div style="font-size:2rem">📈</div>
        <h3>Results</h3>
        <p>Interactive rankings, charts & AI explanations</p>
    </div>""", unsafe_allow_html=True)


# ── Quick Start Guide ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📖 Quick Start Guide")

steps = [
    ("1. Create a Job Vacancy",
     "Go to <b>Job Vacancies</b> → pick a template or build custom criteria."),
    ("2. Upload Resumes",
     "Go to <b>Upload Resumes</b> → drag & drop PDF files. AI parses them instantly."),
    ("3. Set AHP Weights",
     "Go to <b>AHP Wizard</b> → complete pairwise comparisons. System validates CR < 0.10."),
    ("4. Run Analysis",
     "Go to <b>Run Analysis</b> → one click runs SAW + WP + TOPSIS + ensemble."),
    ("5. Review Results",
     "Go to <b>Results Dashboard</b> → explore rankings, radar charts, and AI explanations."),
]

for title, desc in steps:
    num = title.split(".")[0]
    st.markdown(f"""<div class="step-item">
        <div class="step-num">{num}</div>
        <div class="step-text"><h4>{title}</h4><p>{desc}</p></div>
    </div>""", unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<center style='color:#4b5563;font-size:0.8rem'>"
    "Resume Auto-Selection DSS · Universitas Brawijaya · Fakultas Ilmu Komputer · 2026</center>",
    unsafe_allow_html=True,
)
