"""
Global application configuration loaded from environment variables.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── App ───────────────────────────────────────────────────────────────────────
APP_NAME = os.getenv("APP_NAME", "Resume Auto-Selection DSS")
APP_ENV  = os.getenv("APP_ENV", "development")

# ── Groq ──────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── Embedding ─────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL      = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# ── MCDM ──────────────────────────────────────────────────────────────────────
# AHP random consistency index values (Saaty, 1980)
AHP_RI = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12,
          6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}

AHP_CRITERIA = ["Education", "Experience", "Skills", "Certifications", "Languages"]

# Saaty scale labels for pairwise comparison
SAATY_SCALE = {
    1: "Equally important",
    2: "Equal to moderate importance",
    3: "Moderately more important",
    4: "Moderate to strong importance",
    5: "Strongly more important",
    6: "Strong to very strong importance",
    7: "Very strongly more important",
    8: "Very strong to extremely important",
    9: "Extremely more important",
}

# ── Scoring Bounds ────────────────────────────────────────────────────────────
EDUCATION_LEVEL_SCORES = {
    "S3": 1.0, "PhD": 1.0, "Doktor": 1.0,
    "S2": 0.8, "Master": 0.8, "Magister": 0.8,
    "S1": 0.6, "Bachelor": 0.6, "Sarjana": 0.6,
    "D4": 0.55, "D3": 0.45, "D2": 0.35, "D1": 0.25,
    "SMA": 0.15, "SMK": 0.15,
}

# ── UI ────────────────────────────────────────────────────────────────────────
MAX_PDF_UPLOAD_MB = 10
MAX_CANDIDATES    = 100
