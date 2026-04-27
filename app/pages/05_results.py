"""
Page 5 — Results Dashboard
Full visualization: leaderboard, radar charts, heatmap, algorithm comparison, AI explanations.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import io

from db.repositories import list_vacancies, get_scoring_results
from core.llm_explainer import generate_summary_report

st.set_page_config(page_title="Results Dashboard · DSS", page_icon="📈", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1.5rem;
    border-left: 4px solid #34d399;
}
.page-header h2 { color: #ecfdf5; margin: 0; }
.page-header p  { color: #94a3b8; margin: 0.3rem 0 0; }
.rank-card {
    border-radius: 12px; padding: 1.2rem 1.5rem; margin-bottom: 0.8rem;
    border-left: 4px solid;
}
.rank-1 { background: linear-gradient(135deg,#1c1c0a,#2d2d00); border-color: #fbbf24; }
.rank-2 { background: linear-gradient(135deg,#111827,#1f2937); border-color: #94a3b8; }
.rank-3 { background: linear-gradient(135deg,#1c0d07,#2d1a0e); border-color: #b45309; }
.rank-other { background: #1e293b; border-color: #334155; }
.rank-badge { font-size: 1.8rem; font-weight: 800; }
.score-chip {
    display: inline-block; padding: 3px 10px;
    border-radius: 99px; font-size: 0.78rem; font-weight: 600; margin: 2px;
}
.chip-saw    { background: #1e3a5f; color: #60a5fa; }
.chip-wp     { background: #1e1e3a; color: #a78bfa; }
.chip-topsis { background: #0d2d1e; color: #34d399; }
.chip-borda  { background: #2d1b0e; color: #fb923c; }
.explanation-box {
    background: #0f172a; border: 1px solid #1e3a5f;
    border-radius: 8px; padding: 0.9rem; margin-top: 0.5rem;
    color: #cbd5e1; font-size: 0.88rem; line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="page-header">
  <h2>📈 Results Dashboard</h2>
  <p>Candidate rankings, score breakdown, visualizations, and AI explanations</p>
</div>""", unsafe_allow_html=True)


# ── Vacancy Selector ──────────────────────────────────────────────────────────
try:
    vacancies = list_vacancies()
except Exception:
    vacancies = []

if not vacancies:
    st.warning("No vacancies found.")
    st.stop()

vacancy_map = {f"[{v['job_family']}] {v['title']}": v for v in vacancies}
selected_label = st.selectbox("Select Job Vacancy", list(vacancy_map.keys()))
vacancy = vacancy_map[selected_label]
vacancy_id = vacancy["id"]


# ── Load Results ──────────────────────────────────────────────────────────────
try:
    results = get_scoring_results(vacancy_id)
except Exception as e:
    st.error(f"Could not load results: {e}")
    results = []

if not results:
    st.info("No results yet. Please run the analysis first from **Run Analysis** page.")
    st.stop()


# ── Build DataFrame ───────────────────────────────────────────────────────────
rows = []
for r in results:
    cand = r.get("candidates") or {}
    profile = cand.get("parsed_profile") or {}
    dims = r.get("dimension_scores") or {}
    rows.append({
        "rank":        r["ensemble_rank"],
        "name":        profile.get("name") or cand.get("original_filename", "Unknown"),
        "filename":    cand.get("original_filename", ""),
        "education":   dims.get("education", 0),
        "experience":  dims.get("experience", 0),
        "skills":      dims.get("skills", 0),
        "certifications": dims.get("certifications", 0),
        "languages":   dims.get("languages", 0),
        "SAW":         r.get("saw_score", 0),
        "SAW_rank":    r.get("saw_rank", 0),
        "WP":          r.get("wp_score", 0),
        "WP_rank":     r.get("wp_rank", 0),
        "TOPSIS":      r.get("topsis_score", 0),
        "TOPSIS_rank": r.get("topsis_rank", 0),
        "borda":       r.get("borda_score", 0),
        "explanation": r.get("ai_explanation", ""),
        "candidate_id": r["candidate_id"],
    })

df = pd.DataFrame(rows).sort_values("rank").reset_index(drop=True)
dim_cols = ["education", "experience", "skills", "certifications", "languages"]
algo_cols = ["SAW", "WP", "TOPSIS"]


# ── Section 1: Leaderboard ────────────────────────────────────────────────────
st.markdown("## 🏆 Candidate Leaderboard")

rank_icons = {1: "🥇", 2: "🥈", 3: "🥉"}
top_n = st.slider("Show top N candidates", min_value=1, max_value=len(df), value=min(10, len(df)))

for _, row in df.head(top_n).iterrows():
    rank = int(row["rank"])
    icon = rank_icons.get(rank, f"#{rank}")
    card_cls = {1:"rank-1", 2:"rank-2", 3:"rank-3"}.get(rank, "rank-other")

    with st.container():
        st.markdown(f"""
        <div class="rank-card {card_cls}">
          <span class="rank-badge">{icon}</span>
          <strong style="font-size:1.1rem;color:#f1f5f9;margin-left:8px">{row['name']}</strong>
          <span style="color:#64748b;font-size:0.83rem;margin-left:8px">{row['filename']}</span>
          <br>
          <span class="score-chip chip-saw">SAW: {row['SAW']:.4f} (#{row['SAW_rank']})</span>
          <span class="score-chip chip-wp">WP: {row['WP']:.4f} (#{row['WP_rank']})</span>
          <span class="score-chip chip-topsis">TOPSIS: {row['TOPSIS']:.4f} (#{row['TOPSIS_rank']})</span>
          <span class="score-chip chip-borda">Borda: {row['borda']}</span>
        </div>""", unsafe_allow_html=True)

        if row["explanation"]:
            with st.expander("🤖 AI Explanation"):
                st.markdown(f'<div class="explanation-box">{row["explanation"]}</div>',
                            unsafe_allow_html=True)


# ── Section 2: Score Table ────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 📊 Detailed Score Table")

display_df = df[["rank","name"] + dim_cols + algo_cols + ["borda"]].copy()
display_df.columns = ["Rank","Candidate","Education","Experience","Skills","Certs","Languages","SAW","WP","TOPSIS","Borda"]

st.dataframe(
    display_df.style
    .format({
        "Education":"{:.3f}","Experience":"{:.3f}","Skills":"{:.3f}",
        "Certs":"{:.3f}","Languages":"{:.3f}",
        "SAW":"{:.4f}","WP":"{:.4f}","TOPSIS":"{:.4f}",
    })
    .background_gradient(subset=["SAW","WP","TOPSIS"], cmap="Blues")
    .background_gradient(subset=dim_cols[:5] if len(dim_cols)>=5 else dim_cols, cmap="Purples"),
    use_container_width=True,
    height=400,
)


# ── Section 3: Radar Charts ────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 🕸️ Dimension Radar Charts")

top_radar = min(5, len(df))
radar_candidates = st.multiselect(
    "Select candidates to compare",
    options=df["name"].tolist(),
    default=df["name"].head(top_radar).tolist(),
)

if radar_candidates:
    fig_radar = go.Figure()
    colors = ["#a78bfa","#60a5fa","#34d399","#f59e0b","#f87171","#c084fc","#38bdf8"]
    filtered = df[df["name"].isin(radar_candidates)]

    for i, (_, row) in enumerate(filtered.iterrows()):
        vals = [row[d] for d in dim_cols]
        vals_closed = vals + [vals[0]]
        cats_closed = ["Education","Experience","Skills","Certifications","Languages","Education"]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals_closed, theta=cats_closed,
            fill="toself",
            fillcolor=f"rgba{tuple(int(colors[i%len(colors)].lstrip('#')[j:j+2],16) for j in (0,2,4)) + (0.15,)}",
            line=dict(color=colors[i % len(colors)], width=2),
            name=row["name"],
        ))

    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
        font=dict(color="#e2e8f0"),
        legend=dict(bgcolor="#1e293b"),
        height=500,
    )
    st.plotly_chart(fig_radar, use_container_width=True)


# ── Section 4: Heatmap ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 🌡️ Score Heatmap")

heatmap_data = df[["name"] + dim_cols].set_index("name")
fig_heat = px.imshow(
    heatmap_data,
    labels=dict(x="Dimension", y="Candidate", color="Score"),
    color_continuous_scale="Viridis",
    aspect="auto",
    zmin=0, zmax=1,
)
fig_heat.update_layout(
    paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
    font=dict(color="#e2e8f0"),
    height=max(300, len(df) * 30),
)
st.plotly_chart(fig_heat, use_container_width=True)


# ── Section 5: Algorithm Comparison ──────────────────────────────────────────
st.markdown("---")
st.markdown("## 🔬 Algorithm Score Comparison")

col1, col2 = st.columns(2)
with col1:
    fig_bar = go.Figure()
    for algo, color in [("SAW","#60a5fa"),("WP","#a78bfa"),("TOPSIS","#34d399")]:
        fig_bar.add_trace(go.Bar(
            name=algo, x=df["name"], y=df[algo],
            marker_color=color, opacity=0.85,
        ))
    fig_bar.update_layout(
        barmode="group", title="Score by Algorithm",
        paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
        font=dict(color="#e2e8f0"),
        xaxis=dict(tickangle=-30),
        height=400,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    fig_scatter = px.scatter(
        df, x="SAW", y="TOPSIS", size="WP", color="rank",
        hover_name="name", color_continuous_scale="Viridis_r",
        labels={"SAW":"SAW Score","TOPSIS":"TOPSIS Score"},
        title="SAW vs TOPSIS (bubble size = WP score)",
    )
    fig_scatter.update_layout(
        paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
        font=dict(color="#e2e8f0"), height=400,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)


# ── Section 6: Executive Summary ──────────────────────────────────────────────
st.markdown("---")
st.markdown("## 📝 Executive Summary")

if st.button("🤖 Generate Executive Summary (AI)"):
    top_candidates = df.head(3).to_dict("records")
    summary = generate_summary_report(vacancy["title"], top_candidates)
    st.markdown(f'<div class="explanation-box">{summary}</div>', unsafe_allow_html=True)


# ── Section 7: Export ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 💾 Export Results")

col_excel, col_csv = st.columns([1, 1])

with col_excel:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df[["rank","name","filename"] + dim_cols + algo_cols + ["borda","explanation"]].to_excel(
            writer, index=False, sheet_name="Rankings"
        )
    st.download_button(
        "📥 Download Excel",
        data=buffer.getvalue(),
        file_name=f"dss_results_{vacancy['title'].replace(' ','_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

with col_csv:
    csv_data = df[["rank","name","filename"] + dim_cols + algo_cols + ["borda"]].to_csv(index=False)
    st.download_button(
        "📥 Download CSV",
        data=csv_data,
        file_name=f"dss_results_{vacancy['title'].replace(' ','_')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
