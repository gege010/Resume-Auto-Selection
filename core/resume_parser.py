"""
Resume Parser — PDF → structured candidate profile.

Pipeline:
  1. pdfplumber  → extract raw text from PDF bytes
  2. Groq LLM   → parse structured JSON from raw text
  3. Pydantic    → validate & normalise the output schema
"""
from __future__ import annotations

import json
import re
from typing import Any

import pdfplumber
import io
from groq import Groq
from loguru import logger
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import GROQ_API_KEY, GROQ_MODEL


# ── Output Schema ─────────────────────────────────────────────────────────────

class EducationEntry(BaseModel):
    degree: str = ""
    field: str = ""
    institution: str = ""
    gpa: float | None = None
    graduation_year: int | None = None


class ExperienceEntry(BaseModel):
    title: str = ""
    company: str = ""
    duration_months: int = 0
    description: str = ""
    is_current: bool = False


class CandidateProfile(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    education: list[EducationEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    summary: str = ""


# ── PDF Text Extraction ───────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract plain text from a PDF binary using pdfplumber."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts).strip()


# ── LLM Extraction ────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are an expert resume parser. Extract structured information from the resume text.
Return ONLY a valid JSON object with NO additional text, following this exact schema:
{
  "name": "string",
  "email": "string",
  "phone": "string",
  "location": "string",
  "summary": "string",
  "education": [
    {"degree": "string", "field": "string", "institution": "string", "gpa": null_or_float, "graduation_year": null_or_int}
  ],
  "experience": [
    {"title": "string", "company": "string", "duration_months": int, "description": "string", "is_current": bool}
  ],
  "skills": ["string"],
  "certifications": ["string"],
  "languages": ["string"]
}
Rules:
- duration_months: estimate from date ranges (e.g. Jan 2022 - Dec 2023 = 24)
- If a field is unknown, use empty string or empty list
- skills: list individual skills (not categories)
- Return ONLY the JSON, nothing else"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call_groq(raw_text: str) -> str:
    client = Groq(api_key=GROQ_API_KEY)
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Resume text:\n\n{raw_text[:6000]}"},
        ],
        temperature=0.1,
        max_tokens=2048,
    )
    return resp.choices[0].message.content


def _clean_json_response(raw: str) -> str:
    """Strip markdown code fences if present."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


# ── Public API ────────────────────────────────────────────────────────────────

def parse_resume(pdf_bytes: bytes, filename: str = "resume.pdf") -> tuple[str, CandidateProfile]:
    """
    Full resume parsing pipeline.

    Returns:
        (raw_text, CandidateProfile)
    """
    logger.info("Parsing resume: {}", filename)

    # Step 1: extract text
    raw_text = extract_text_from_pdf(pdf_bytes)
    if not raw_text:
        logger.warning("No text extracted from {}; may be image-only PDF", filename)
        return raw_text, CandidateProfile()

    # Step 2: LLM extraction
    try:
        llm_output = _call_groq(raw_text)
        json_str = _clean_json_response(llm_output)
        data: dict[str, Any] = json.loads(json_str)
    except json.JSONDecodeError as exc:
        logger.error("JSON parse error for {}: {}", filename, exc)
        return raw_text, CandidateProfile()
    except Exception as exc:
        logger.error("LLM call failed for {}: {}", filename, exc)
        return raw_text, CandidateProfile()

    # Step 3: validate schema
    try:
        profile = CandidateProfile(**data)
    except Exception as exc:
        logger.warning("Profile validation warning for {}: {}", filename, exc)
        profile = CandidateProfile()

    logger.info("Parsed '{}' — skills={}, exp_entries={}",
                profile.name or filename, len(profile.skills), len(profile.experience))
    return raw_text, profile
