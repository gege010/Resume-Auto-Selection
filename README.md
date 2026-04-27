# 🧠 Resume Auto-Selection DSS

**Decision Support System for Multi-Criteria Candidate Selection**  
Universitas Brawijaya · Fakultas Ilmu Komputer · 2026

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.43-red)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/Database-Supabase-green)](https://supabase.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://docker.com)

---

## 📌 Overview

A full-pipeline AI-powered Decision Support System that:
- 📄 **Parses** PDF resumes using LLM (Groq llama-3.3-70b)
- ⚖️ **Derives** criteria weights via **AHP** (pairwise comparison, CR validation)
- ⚡ **Runs ensemble MCDM**: SAW + WP + TOPSIS aggregated via Borda Count
- 📈 **Visualizes** results with radar charts, heatmaps, and score comparisons
- 🤖 **Explains** rankings with AI-generated natural language reasoning

---

## 🚀 Quick Start

### 1. Clone & Configure
```bash
git clone <repo>
cd resume-auto-selection
cp .env.example .env
# Edit .env and fill in your keys
```

### 2. Set Environment Variables
```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
GROQ_API_KEY=gsk_...
```

### 3. Setup Supabase Database
- Create a new project at [supabase.com](https://supabase.com)
- Go to **SQL Editor** and run the contents of `db/migrations/001_initial_schema.sql`

### 4. Run Locally
```bash
pip install -r requirements.txt
streamlit run app/main.py
```

### 5. Run with Docker
```bash
docker compose up --build
# App available at http://localhost:8501
```

---

## 🗂️ Project Structure
```
├── app/
│   ├── main.py                   # Home dashboard
│   ├── config.py                 # App configuration
│   └── pages/
│       ├── 01_job_vacancies.py   # Job vacancy manager
│       ├── 02_upload_resumes.py  # PDF upload & AI parsing
│       ├── 03_ahp_wizard.py      # AHP weight wizard
│       ├── 04_run_analysis.py    # Run MCDM pipeline
│       └── 05_results.py         # Results dashboard
├── core/
│   ├── resume_parser.py          # PDF → structured JSON (pdfplumber + Groq)
│   ├── semantic_scorer.py        # Sentence-transformers skill matching
│   ├── dimension_calculator.py   # 5-dimension scoring
│   ├── llm_explainer.py          # AI explanation generation
│   └── mcdm/
│       ├── ahp.py                # AHP weight derivation
│       ├── saw.py                # Simple Additive Weighting
│       ├── weighted_product.py   # Weighted Product
│       ├── topsis.py             # TOPSIS
│       └── ensemble.py           # Borda Count aggregation
├── db/
│   ├── supabase_client.py        # DB connection
│   ├── repositories.py           # CRUD layer
│   └── migrations/
│       └── 001_initial_schema.sql
├── data/
│   └── job_templates.py          # 10 predefined job families
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 🧮 Algorithm Details

| Algorithm | Formula | Role |
|---|---|---|
| **AHP** | Pairwise comparison → eigenvector | Weight derivation |
| **SAW** | Σ(w·r) | Additive scoring |
| **WP** | Π(x^w) | Multiplicative scoring |
| **TOPSIS** | d⁻/(d⁺+d⁻) | Distance to ideal |
| **Borda Count** | Sum of ranks | Ensemble aggregation |

**5 Scoring Dimensions:**
1. **Education** — degree level + field semantic relevance
2. **Experience** — total months + role semantic relevance
3. **Skills** — cosine similarity (sentence-transformers)
4. **Certifications** — semantic matching
5. **Languages** — requirement fulfillment ratio

---

## 📦 Tech Stack

- **UI**: Streamlit + Plotly + Altair
- **LLM**: Groq API (llama-3.3-70b-versatile)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2, local)
- **PDF**: pdfplumber + PyMuPDF
- **Database**: Supabase (PostgreSQL)
- **Container**: Docker + Docker Compose

---

## 👥 Team

| NIM | Name |
|---|---|
| 225150407111061 | Ambar Willis Widiansyah |
| 235150400111033 | Anugerah Gabriel Hutajulu |
| 235150407111038 | Andhika Daniswara Hidayat |
| 235150407111021 | Raditya Ramadhan Firdanto |
| 225150407111030 | Rubens Willsandro Taimenas |
