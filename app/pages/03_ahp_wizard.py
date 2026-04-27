"""
Page 3 — AHP Weight Wizard
Step-by-step pairwise comparison interface with CR validation.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from app.config import AHP_CRITERIA, SAATY_SCALE
from core.mcdm.ahp import compute_ahp, build_reciprocal_matrix
from db.repositories import list_vacancies, save_ahp_matrix, get_ahp_matrix

st.set_page_config(page_title="AHP Wizard · DSS", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #0d1b2a, #1b2838, #0d2137);
    border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1.5rem;
    border-left: 4px solid #f59e0b;
}
.page-header h2 { color: #fef3c7; margin: 0; }
.page-header p  { color: #94a3b8; margin: 0.3rem 0 0; }
.weight-bar {
    height: 24px; border-radius: 4px;
    background: linear-gradient(90deg, #7c3aed, #a78bfa);
    display: inline-block; margin-bottom: 4px;
    transition: width 0.4s ease;
}
.cr-ok  { background:#064e3b; color:#34d399; padding:6px 14px; border-radius:8px; font-weight:600; }
.cr-err { background:#7f1d1d; color:#f87171; padding:6px 14px; border-radius:8px; font-weight:600; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="page-header">
  <h2>⚖️ AHP Weight Wizard</h2>
  <p>Derive criteria weights systematically via pairwise comparison (Saaty scale 1–9)</p>
</div>""", unsafe_allow_html=True)


# ── Vacancy Selector ──────────────────────────────────────────────────────────
try:
    vacancies = list_vacancies()
except Exception:
    vacancies = []

if not vacancies:
    st.warning("No vacancies found. Please create one first.")
    st.stop()

vacancy_map = {f"[{v['job_family']}] {v['title']}": v for v in vacancies}
selected_label = st.selectbox("Select Job Vacancy", list(vacancy_map.keys()))
vacancy = vacancy_map[selected_label]
vacancy_id = vacancy["id"]

# Load existing AHP if available
existing = None
try:
    existing = get_ahp_matrix(vacancy_id)
except Exception:
    pass


# ── Saaty Scale Reference ─────────────────────────────────────────────────────
with st.expander("📖 Saaty Scale Reference"):
    for k, v in SAATY_SCALE.items():
        st.markdown(f"**{k}** — {v}")


# ── Pairwise Matrix Input ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Step 1: Pairwise Comparisons")
st.markdown(
    "For each pair, how much **more important** is the **left criterion** compared to the **right**?  \n"
    "Use Saaty scale 1–9. Values < 1 auto-invert (right side is more important)."
)

n = len(AHP_CRITERIA)
upper_defaults: dict[tuple[int, int], float] = {}

if existing and existing.get("pairwise_matrix"):
    mat = existing["pairwise_matrix"]
    for i in range(n):
        for j in range(i+1, n):
            upper_defaults[(i, j)] = mat[i][j]

upper_vals: dict[tuple[int, int], float] = {}
pair_idx = 0
for i in range(n):
    for j in range(i+1, n):
        default_val = upper_defaults.get((i, j), 1.0)
        col_l, col_slider, col_r = st.columns([2, 4, 2])
        with col_l:
            st.markdown(f"<div style='text-align:right;padding-top:0.5rem;color:#a78bfa;font-weight:600'>"
                        f"{AHP_CRITERIA[i]}</div>", unsafe_allow_html=True)
        with col_slider:
            val = st.slider(
                f"vs",
                min_value=1.0/9.0, max_value=9.0,
                value=float(default_val),
                step=1.0,
                format="%.1f",
                key=f"ahp_{i}_{j}",
                label_visibility="collapsed",
            )
            upper_vals[(i, j)] = val
        with col_r:
            st.markdown(f"<div style='padding-top:0.5rem;color:#60a5fa;font-weight:600'>"
                        f"{AHP_CRITERIA[j]}</div>", unsafe_allow_html=True)
        pair_idx += 1


# ── Compute AHP ───────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Step 2: Compute Weights")

compute_btn = st.button("⚡ Compute AHP Weights", type="primary")

if compute_btn:
    matrix = build_reciprocal_matrix(upper_vals, n)
    result = compute_ahp(matrix)
    st.session_state["ahp_result"] = result
    st.session_state["ahp_matrix"] = matrix

if "ahp_result" in st.session_state:
    result = st.session_state["ahp_result"]
    weights = result["weights"]
    cr = result["consistency_ratio"]
    ci = result["consistency_index"]
    lam = result["lambda_max"]

    # CR status
    cr_class = "cr-ok" if result["is_valid"] else "cr-err"
    cr_icon  = "✅" if result["is_valid"] else "⚠️"
    st.markdown(
        f'<div class="{cr_class}">{cr_icon} Consistency Ratio (CR) = {cr:.4f} '
        f'{"(Valid — CR < 0.10)" if result["is_valid"] else "(INVALID — CR ≥ 0.10, please revise comparisons)"}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"λ_max = `{lam:.4f}` · CI = `{ci:.4f}` · CR = `{cr:.4f}`")

    # Weight bars
    st.markdown("#### Derived Criteria Weights")
    for crit, w in zip(AHP_CRITERIA, weights):
        bar_w = int(w * 500)
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:6px'>"
            f"<span style='width:120px;color:#e2e8f0;font-weight:500'>{crit}</span>"
            f"<div class='weight-bar' style='width:{bar_w}px'></div>"
            f"<span style='color:#a78bfa;font-weight:700'>{w:.4f}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

    # Radar chart
    fig = go.Figure(go.Scatterpolar(
        r=weights + [weights[0]],
        theta=AHP_CRITERIA + [AHP_CRITERIA[0]],
        fill="toself",
        fillcolor="rgba(124,58,237,0.25)",
        line=dict(color="#a78bfa", width=2),
        name="Weights",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max(weights)*1.2])),
        paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
        font=dict(color="#e2e8f0"),
        height=360, margin=dict(t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Save button
    if result["is_valid"]:
        if st.button("💾 Save Weights to Vacancy", type="primary"):
            try:
                matrix_2d = st.session_state["ahp_matrix"]
                save_ahp_matrix({
                    "vacancy_id": vacancy_id,
                    "criteria_names": AHP_CRITERIA,
                    "pairwise_matrix": matrix_2d,
                    "weights": weights,
                    "lambda_max": lam,
                    "consistency_index": ci,
                    "consistency_ratio": cr,
                    "is_valid": True,
                })
                st.success("✅ AHP weights saved for this vacancy.")
            except Exception as e:
                st.error(f"Save failed: {e}")
    else:
        st.warning("⚠️ Please revise your comparisons until CR < 0.10 before saving.")

elif existing and existing.get("weights"):
    st.info(f"Previously saved weights found (CR={existing.get('consistency_ratio',0):.4f}). "
            f"Click **Compute** above to update.")
    for crit, w in zip(AHP_CRITERIA, existing["weights"]):
        st.markdown(f"- **{crit}**: `{w:.4f}`")
