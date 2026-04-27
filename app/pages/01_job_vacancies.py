"""
Page 1 — Job Vacancy Manager
Create, edit, and manage job vacancies using predefined templates or custom configs.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import streamlit as st
import json

from data.job_templates import get_template, list_job_families
from db.repositories import (
    create_vacancy, list_vacancies, update_vacancy, delete_vacancy
)

st.set_page_config(page_title="Job Vacancies · DSS", page_icon="💼", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1.5rem;
    border-left: 4px solid #60a5fa;
}
.page-header h2 { color: #e2e8f0; margin: 0; }
.page-header p  { color: #94a3b8; margin: 0.3rem 0 0; }
.vacancy-card {
    background: #1e293b; border: 1px solid #334155;
    border-radius: 10px; padding: 1.2rem; margin-bottom: 0.8rem;
    transition: border-color 0.2s;
}
.vacancy-card:hover { border-color: #60a5fa; }
.vacancy-card h4 { color: #a78bfa; margin: 0 0 0.3rem; }
.vacancy-card .tag {
    background: #1e3a5f; color: #93c5fd;
    padding: 2px 8px; border-radius: 99px; font-size: 0.75rem;
    display: inline-block; margin-right: 4px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="page-header">
  <h2>💼 Job Vacancy Manager</h2>
  <p>Create and manage job vacancies with predefined templates or custom criteria</p>
</div>""", unsafe_allow_html=True)

tab_create, tab_manage = st.tabs(["➕ Create Vacancy", "📋 Manage Vacancies"])

# ── Tab 1: Create ─────────────────────────────────────────────────────────────
with tab_create:
    st.markdown("#### Select a Job Family Template")

    families = list_job_families()
    col_sel, col_load = st.columns([3, 1])
    with col_sel:
        selected_family = st.selectbox("Job Family", families, key="new_family")
    with col_load:
        st.markdown("<br>", unsafe_allow_html=True)
        load_btn = st.button("Load Template", use_container_width=True)

    if load_btn or "template_loaded" not in st.session_state:
        st.session_state["template_data"] = get_template(selected_family)
        st.session_state["template_loaded"] = True

    tpl = st.session_state.get("template_data", get_template(selected_family))

    st.markdown("---")
    st.markdown("#### Vacancy Details")

    col_a, col_b = st.columns(2)
    with col_a:
        v_title = st.text_input("Job Title *", value=tpl.get("job_family", ""))
        v_edu_level = st.selectbox(
            "Min. Education Level",
            ["D3", "S1", "S2", "S3"],
            index=["D3","S1","S2","S3"].index(tpl.get("required_education_level","S1"))
        )
        v_exp = st.number_input(
            "Min. Experience (months)", min_value=0, max_value=240,
            value=int(tpl.get("required_experience_months", 0))
        )
    with col_b:
        v_edu_field = st.text_input(
            "Education Field", value=tpl.get("required_education_field", "")
        )
        v_desc = st.text_area("Job Description", value="", height=120)

    st.markdown("#### Criteria Configuration")
    col_sk, col_cert, col_lang = st.columns(3)

    with col_sk:
        skills_default = "\n".join(tpl.get("required_skills", []))
        v_skills_raw = st.text_area(
            "Required Skills (one per line)", value=skills_default, height=180
        )

    with col_cert:
        certs_default = "\n".join(tpl.get("required_certifications", []))
        v_certs_raw = st.text_area(
            "Required Certifications (one per line)", value=certs_default, height=180
        )

    with col_lang:
        langs_default = "\n".join(tpl.get("required_languages", []))
        v_langs_raw = st.text_area(
            "Required Languages (one per line)", value=langs_default, height=180
        )

    st.markdown("---")
    save_col, _ = st.columns([1, 4])
    with save_col:
        if st.button("💾 Save Vacancy", use_container_width=True, type="primary"):
            if not v_title.strip():
                st.error("Job title is required.")
            else:
                payload = {
                    "title": v_title.strip(),
                    "job_family": selected_family,
                    "description": v_desc.strip(),
                    "required_education_level": v_edu_level,
                    "required_education_field": v_edu_field.strip(),
                    "required_experience_months": int(v_exp),
                    "required_skills": [s.strip() for s in v_skills_raw.splitlines() if s.strip()],
                    "required_certifications": [c.strip() for c in v_certs_raw.splitlines() if c.strip()],
                    "required_languages": [l.strip() for l in v_langs_raw.splitlines() if l.strip()],
                }
                try:
                    rec = create_vacancy(payload)
                    st.success(f"✅ Vacancy '{v_title}' saved! ID: `{rec['id']}`")
                    st.session_state["template_loaded"] = False
                except Exception as e:
                    st.error(f"Failed to save: {e}")


# ── Tab 2: Manage ─────────────────────────────────────────────────────────────
with tab_manage:
    st.markdown("#### Existing Vacancies")
    refresh = st.button("🔄 Refresh")

    try:
        vacancies = list_vacancies()
    except Exception as e:
        st.error(f"Could not load vacancies: {e}")
        vacancies = []

    if not vacancies:
        st.info("No vacancies yet. Create one in the '➕ Create Vacancy' tab.")
    else:
        for v in vacancies:
            with st.container():
                skills_preview = ", ".join((v.get("required_skills") or [])[:5])
                col_info, col_actions = st.columns([5, 1])
                with col_info:
                    st.markdown(f"""<div class="vacancy-card">
                        <h4>💼 {v['title']}</h4>
                        <span class="tag">{v['job_family']}</span>
                        <span class="tag">Min {v.get('required_experience_months',0)} mo exp</span>
                        <span class="tag">{v.get('required_education_level','S1')}</span>
                        <br><small style='color:#64748b;margin-top:0.4rem;display:block'>
                        Skills: {skills_preview or '—'}</small>
                        <small style='color:#475569'>ID: {v['id']}</small>
                    </div>""", unsafe_allow_html=True)
                with col_actions:
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    if st.button("🗑️ Delete", key=f"del_{v['id']}"):
                        try:
                            delete_vacancy(v["id"])
                            st.success("Deleted.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
