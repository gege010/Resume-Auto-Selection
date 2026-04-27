"""
LLM Explainer — generates natural language reasoning for candidate rankings.

Uses Groq API to produce recruiter-friendly explanations per candidate.
"""
from __future__ import annotations

from groq import Groq
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import GROQ_API_KEY, GROQ_MODEL


_client: Groq | None = None

def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


_EXPLAIN_SYSTEM = """You are an objective HR analyst AI. Given a candidate's scoring data and job requirements,
write a concise 3-4 sentence professional explanation in English that covers:
1. Why the candidate achieved their rank (strengths)
2. Key gaps or areas of concern (weaknesses)
3. A brief hiring recommendation (recommend / conditionally recommend / not recommended)
Be specific, factual, and base everything on the numbers provided. Do NOT be generic."""


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8))
def generate_explanation(
    candidate_name: str,
    ensemble_rank: int,
    dimension_scores: dict[str, float],
    saw_score: float,
    wp_score: float,
    topsis_score: float,
    vacancy_title: str,
    vacancy_requirements: dict,
) -> str:
    """
    Generate a natural-language explanation for a candidate's DSS result.

    Returns plain text explanation string.
    """
    prompt = f"""
Job Position: {vacancy_title}
Required Skills: {', '.join(vacancy_requirements.get('required_skills', []))}
Required Experience: {vacancy_requirements.get('required_experience_months', 0)} months
Required Education: {vacancy_requirements.get('required_education_level', 'S1')} in {vacancy_requirements.get('required_education_field', 'any')}

Candidate: {candidate_name}
Final Ensemble Rank: #{ensemble_rank}

Dimension Scores (0–1):
- Education:       {dimension_scores.get('education', 0):.3f}
- Experience:      {dimension_scores.get('experience', 0):.3f}
- Skills:          {dimension_scores.get('skills', 0):.3f}
- Certifications:  {dimension_scores.get('certifications', 0):.3f}
- Languages:       {dimension_scores.get('languages', 0):.3f}

Algorithm Scores:
- SAW:    {saw_score:.4f}
- WP:     {wp_score:.4f}
- TOPSIS: {topsis_score:.4f}

Write your professional assessment:"""

    try:
        resp = _get_client().chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": _EXPLAIN_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=300,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("LLM explanation failed for {}: {}", candidate_name, exc)
        return f"Automated explanation unavailable. Ensemble rank: #{ensemble_rank}."


def generate_summary_report(
    vacancy_title: str,
    ranked_results: list[dict],
    n_top: int = 3,
) -> str:
    """
    Generate an executive summary for the top-N candidates.
    """
    top = ranked_results[:n_top]
    lines = [f"#{r['ensemble_rank']} {r.get('name', 'Unknown')} (Borda: {r.get('borda_score')})"
             for r in top]

    prompt = f"""Job: {vacancy_title}
Top {n_top} candidates:
{chr(10).join(lines)}

Write a 2-3 sentence executive summary for the hiring manager recommending next steps."""

    try:
        resp = _get_client().chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a senior HR consultant writing executive summaries."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=200,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("Summary report failed: {}", exc)
        return "Executive summary unavailable."
