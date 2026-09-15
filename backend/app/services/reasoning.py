"""LLM-generated recruiter-facing explanation for a candidate's score."""
from __future__ import annotations

from app.services.ollama_client import generate_text
from app.services.scoring import ScoreResult


def generate_reasoning(resume_json: dict, jd_json: dict, score: ScoreResult) -> str:
    prompt = f"""You are a technical recruiter writing a short, honest note about a candidate.

Job: {jd_json.get('title')}
Required skills: {', '.join(jd_json.get('required_skills') or [])}
Min years experience: {jd_json.get('min_years_experience')}

Candidate: {resume_json.get('name')}
Candidate summary: {resume_json.get('summary')}
Candidate years experience: {resume_json.get('years_experience')}
Matched required skills: {', '.join(score.matched_required) or 'none'}
Missing required skills: {', '.join(score.missing_required) or 'none'}
Keyword score: {score.keyword_score}/100
Semantic relevance score: {score.semantic_score}/100
Experience penalty: {score.experience_penalty}

Write a 3-4 sentence explanation of this candidate's fit for the role. Name
which required skills are present or missing, comment on whether experience
meets the bar, credit semantically-relevant experience even without exact
keyword matches, and be honest about weaknesses as well as strengths. Do not
repeat the raw scores as numbers; write in prose.
"""
    text = generate_text(prompt)
    return text or "Reasoning unavailable (LLM call failed)."
