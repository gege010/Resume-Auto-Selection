"""
Page 2 — Upload & Parse Resumes
Drag-and-drop PDF upload with real-time AI parsing and preview.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import streamlit as st
import json

from db.repositories import list_vacancies, create_candidate, update_candidate, list_candidates, delete_candidate
from core.resume_parser import parse_resume

st.set_page_config(page_title="Upload Resumes · DSS", page_icon="📄", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
    border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1.5rem;
    border-left: 4px solid #a78bfa;
}
.page-header h2 { color: #e2e8f0; margin: 0; }
.page-header p  { color: #94a3b8; margin: 0.3rem 0 0; }
.parse-card {
    background: #1e293b; border: 1px solid #334155;
    border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.6rem;
}
.parse-card h5 { color: #c4b5fd; margin: 0 0 0.4rem; }
.skill-pill {
    background: #1e3a5f; color: #93c5fd;
    padding: 2px 8px; border-radius: 99px; font-size: 0.74rem;
    display: inline-block; margin: 2px;
}
.status-ok  { color: #34d399; font-weight: 600; }
.status-err { color: #f87171; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="page-header">
  <h2>📄 Upload & Parse Resumes</h2>
  <p>Upload PDF resumes — AI automatically extracts structured candidate profiles</p>
</div>""", unsafe_allow_html=True)


# ── Vacancy Selector ──────────────────────────────────────────────────────────
try:
    vacancies = list_vacancies()
except Exception:
    vacancies = []

if not vacancies:
    st.warning("⚠️ No job vacancies found. Please create one first in **Job Vacancies**.")
    st.stop()

vacancy_map = {f"[{v['job_family']}] {v['title']}": v["id"] for v in vacancies}
selected_label = st.selectbox("Select Job Vacancy", list(vacancy_map.keys()))
vacancy_id = vacancy_map[selected_label]


# ── File Upload ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### Upload PDF Resumes")
uploaded_files = st.file_uploader(
    "Drag & drop PDF files here (max 10 MB each)",
    type=["pdf"],
    accept_multiple_files=True,
    key="pdf_uploader",
)

if uploaded_files:
    st.markdown(f"**{len(uploaded_files)} file(s) selected**")
    parse_btn = st.button("🚀 Parse All Resumes", type="primary", use_container_width=False)

    if parse_btn:
        progress_bar = st.progress(0, text="Starting…")
        results_log = []

        for idx, f in enumerate(uploaded_files):
            progress_bar.progress(
                (idx) / len(uploaded_files),
                text=f"Parsing {f.name} ({idx+1}/{len(uploaded_files)})…"
            )
            pdf_bytes = f.read()

            try:
                raw_text, profile = parse_resume(pdf_bytes, f.name)
                # Save to DB
                candidate_rec = create_candidate({
                    "vacancy_id": vacancy_id,
                    "original_filename": f.name,
                    "raw_text": raw_text,
                    "parsed_profile": profile.model_dump(),
                    "parsing_status": "success",
                })
                results_log.append({"filename": f.name, "status": "success", "name": profile.name, "id": candidate_rec["id"]})
            except Exception as e:
                try:
                    create_candidate({
                        "vacancy_id": vacancy_id,
                        "original_filename": f.name,
                        "raw_text": "",
                        "parsing_status": "failed",
                        "parsing_error": str(e),
                    })
                except Exception:
                    pass
                results_log.append({"filename": f.name, "status": "failed", "error": str(e)})

        progress_bar.progress(1.0, text="Done!")

        st.markdown("#### Parse Results")
        for r in results_log:
            if r["status"] == "success":
                st.markdown(
                    f'<span class="status-ok">✅ {r["filename"]}</span> — {r["name"] or "Name not found"}',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<span class="status-err">❌ {r["filename"]}</span> — {r.get("error", "Unknown error")}',
                    unsafe_allow_html=True
                )
        st.success(f"Parsed {sum(1 for r in results_log if r['status']=='success')}/{len(results_log)} resumes successfully.")


# ── Candidate List ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### Parsed Candidates for This Vacancy")

col_refresh, col_del_all = st.columns([1, 1])
with col_refresh:
    if st.button("🔄 Refresh List"):
        st.rerun()

try:
    candidates = list_candidates(vacancy_id)
except Exception:
    candidates = []

if not candidates:
    st.info("No candidates uploaded yet for this vacancy.")
else:
    st.markdown(f"**{len(candidates)} candidate(s) on record**")

    for c in candidates:
        profile_data = c.get("parsed_profile") or {}
        name    = profile_data.get("name") or c["original_filename"]
        skills  = profile_data.get("skills", [])[:8]
        exp_list = profile_data.get("experience", [])
        total_exp = sum(e.get("duration_months", 0) for e in exp_list)
        status  = c.get("parsing_status", "pending")

        with st.expander(f"{'✅' if status=='success' else '❌'} {name} — {c['original_filename']}"):
            col_info, col_del = st.columns([5, 1])
            with col_info:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Name:** {profile_data.get('name','—')}")
                    st.markdown(f"**Email:** {profile_data.get('email','—')}")
                    st.markdown(f"**Location:** {profile_data.get('location','—')}")
                with col2:
                    edu = profile_data.get("education", [])
                    if edu:
                        e = edu[0]
                        st.markdown(f"**Education:** {e.get('degree','')} {e.get('field','')}")
                        st.markdown(f"**Institution:** {e.get('institution','—')}")
                    st.markdown(f"**Experience:** {total_exp} months ({len(exp_list)} roles)")
                with col3:
                    if skills:
                        pills = " ".join(f'<span class="skill-pill">{s}</span>' for s in skills)
                        st.markdown(f"**Skills:**<br>{pills}", unsafe_allow_html=True)
                    certs = profile_data.get("certifications", [])
                    if certs:
                        st.markdown(f"**Certs:** {', '.join(certs[:3])}")

            with col_del:
                if st.button("🗑️", key=f"del_cand_{c['id']}"):
                    try:
                        delete_candidate(c["id"])
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
