"""
Page 4 — Run Analysis
Execute the full ensemble MCDM pipeline for a selected vacancy.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import streamlit as st
import pandas as pd

from db.repositories import (
    list_vacancies, list_candidates, get_ahp_matrix,
    upsert_scoring_result, delete_scoring_results, get_scoring_results,
)
from core.resume_parser import CandidateProfile
from core.dimension_calculator import compute_dimensions
from core.mcdm.saw import run_saw
from core.mcdm.weighted_product import run_wp
from core.mcdm.topsis import run_topsis
from core.mcdm.ensemble import run_ensemble
from core.llm_explainer import generate_explanation

st.set_page_config(page_title="Run Analysis · DSS", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #0a0a23, #1a1a3e, #2d1b69);
    border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1.5rem;
    border-left: 4px solid #f59e0b;
}
.page-header h2 { color: #fef9c3; margin: 0; }
.page-header p  { color: #94a3b8; margin: 0.3rem 0 0; }
.log-box {
    background: #0d1117; border: 1px solid #21262d;
    border-radius: 8px; padding: 1rem; font-family: monospace;
    font-size: 0.82rem; color: #c9d1d9; max-height: 300px; overflow-y: auto;
}
.log-ok  { color: #3fb950; }
.log-err { color: #f85149; }
.log-info{ color: #58a6ff; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="page-header">
  <h2>⚡ Run Ensemble Analysis</h2>
  <p>Execute SAW · WP · TOPSIS · Borda Count ensemble + AI explanations</p>
</div>""", unsafe_allow_html=True)


# ── Vacancy Selector ──────────────────────────────────────────────────────────
try:
    vacancies = list_vacancies()
except Exception:
    vacancies = []

if not vacancies:
    st.warning("No vacancies found. Create one first.")
    st.stop()

vacancy_map = {f"[{v['job_family']}] {v['title']}": v for v in vacancies}
selected_label = st.selectbox("Select Job Vacancy", list(vacancy_map.keys()))
vacancy = vacancy_map[selected_label]
vacancy_id = vacancy["id"]


# ── Pre-flight Checks ─────────────────────────────────────────────────────────
col_a, col_b, col_c = st.columns(3)

try:
    candidates = list_candidates(vacancy_id)
    n_ok = sum(1 for c in candidates if c.get("parsing_status") == "success")
except Exception:
    candidates, n_ok = [], 0

try:
    ahp = get_ahp_matrix(vacancy_id)
    ahp_ok = ahp and ahp.get("is_valid")
    weights = ahp["weights"] if ahp_ok else None
except Exception:
    ahp_ok, weights = False, None

with col_a:
    icon = "✅" if n_ok >= 2 else "❌"
    st.metric("Parsed Candidates", f"{n_ok}", help="Min 2 required")
    st.markdown(f"{icon} {'Ready' if n_ok>=2 else 'Need ≥2 candidates'}")

with col_b:
    icon = "✅" if ahp_ok else "❌"
    st.metric("AHP Weights", "Valid" if ahp_ok else "Missing", help="Run AHP Wizard first")
    st.markdown(f"{icon} {'Weights loaded' if ahp_ok else 'Go to AHP Wizard'}")

with col_c:
    st.metric("Ensemble Methods", "3 (SAW + WP + TOPSIS)")
    st.markdown("✅ Ready")


# ── Run Button ────────────────────────────────────────────────────────────────
st.markdown("---")
options_col, _ = st.columns([2, 3])
with options_col:
    include_ai = st.checkbox("🤖 Generate AI explanations (slower)", value=True)
    overwrite = st.checkbox("♻️ Overwrite existing results", value=True)

all_ready = n_ok >= 2 and ahp_ok

run_btn = st.button(
    "🚀 Run Full Analysis",
    type="primary",
    disabled=not all_ready,
    use_container_width=False,
)

if not all_ready:
    missing = []
    if n_ok < 2: missing.append("≥2 successfully parsed candidates")
    if not ahp_ok: missing.append("valid AHP weights")
    st.warning(f"Missing: {', '.join(missing)}")

if run_btn and all_ready:
    logs = []

    def log(msg, style="info"):
        logs.append((msg, style))

    log_placeholder = st.empty()

    def refresh_log():
        html = "<div class='log-box'>"
        for msg, sty in logs:
            html += f"<div class='log-{sty}'>{msg}</div>"
        html += "</div>"
        log_placeholder.markdown(html, unsafe_allow_html=True)

    log("▶ Starting analysis pipeline…")
    refresh_log()

    # ── Step 1: Collect parsed profiles
    log(f"📋 Loading {n_ok} candidate profiles…")
    refresh_log()

    parsed_candidates = []
    for c in candidates:
        if c.get("parsing_status") != "success" or not c.get("parsed_profile"):
            continue
        profile = CandidateProfile(**c["parsed_profile"])
        parsed_candidates.append({"db": c, "profile": profile})

    log(f"✅ Loaded {len(parsed_candidates)} profiles.", "ok")
    refresh_log()

    # ── Step 2: Compute dimension scores
    log("📐 Computing 5-dimension scores…")
    refresh_log()

    dim_rows = {}
    for item in parsed_candidates:
        cid = item["db"]["id"]
        dims = compute_dimensions(item["profile"], vacancy)
        dim_rows[cid] = dims
        log(f"  {item['profile'].name or item['db']['original_filename']}: {dims}")
    refresh_log()

    log("✅ Dimension scores computed.", "ok")
    refresh_log()

    # ── Step 3: Build decision matrix
    criteria_order = ["education", "experience", "skills", "certifications", "languages"]
    dm_data = {cid: [dims[c] for c in criteria_order] for cid, dims in dim_rows.items()}
    dm = pd.DataFrame.from_dict(dm_data, orient="index", columns=criteria_order)

    log(f"📊 Decision matrix shape: {dm.shape}")
    refresh_log()

    # ── Step 4: MCDM
    log("⚡ Running SAW…")
    saw_scores = run_saw(dm, weights)
    log("⚡ Running Weighted Product…")
    wp_scores = run_wp(dm, weights)
    log("⚡ Running TOPSIS…")
    topsis_scores = run_topsis(dm, weights)
    log("⚡ Running Borda Count Ensemble…")
    ensemble_df = run_ensemble({"SAW": saw_scores, "WP": wp_scores, "TOPSIS": topsis_scores})

    log("✅ All MCDM algorithms complete.", "ok")
    refresh_log()

    # ── Step 5: AI Explanations
    if overwrite:
        try:
            delete_scoring_results(vacancy_id)
        except Exception:
            pass

    for _, row in ensemble_df.iterrows():
        cid = row["candidate_id"]
        item = next(x for x in parsed_candidates if x["db"]["id"] == cid)
        profile = item["profile"]
        dims = dim_rows[cid]
        rank = int(row["ensemble_rank"])

        ai_text = ""
        if include_ai:
            log(f"🤖 Generating explanation for #{rank} {profile.name}…")
            refresh_log()
            ai_text = generate_explanation(
                candidate_name=profile.name or item["db"]["original_filename"],
                ensemble_rank=rank,
                dimension_scores=dims,
                saw_score=float(row["SAW_score"]),
                wp_score=float(row["WP_score"]),
                topsis_score=float(row["TOPSIS_score"]),
                vacancy_title=vacancy["title"],
                vacancy_requirements=vacancy,
            )

        upsert_scoring_result({
            "vacancy_id": vacancy_id,
            "candidate_id": cid,
            "dimension_scores": dims,
            "normalized_scores": dm.loc[cid].to_dict(),
            "saw_score":     float(row["SAW_score"]),
            "saw_rank":      int(row["SAW_rank"]),
            "wp_score":      float(row["WP_score"]),
            "wp_rank":       int(row["WP_rank"]),
            "topsis_score":  float(row["TOPSIS_score"]),
            "topsis_rank":   int(row["TOPSIS_rank"]),
            "borda_score":   int(row["borda_score"]),
            "ensemble_rank": rank,
            "ai_explanation": ai_text,
        })

    log("✅ All results saved to database!", "ok")
    log("🎉 Analysis complete. Go to Results Dashboard →", "ok")
    refresh_log()

    st.success("✅ Analysis complete! Navigate to **Results Dashboard** to see rankings.")
    st.balloons()
