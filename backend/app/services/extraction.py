"""Resume/JD raw text -> fixed JSON schema, via a local LLM.

Per TEXT_JSON_SCORING_APPROACH.md: resume formats vary too much for reliable
regex/NER extraction, so an LLM with a fixed JSON schema is used instead.
"""
from __future__ import annotations

from app.services.ollama_client import generate_json

RESUME_SCHEMA_HINT = """{
  "name": "string",
  "titles": ["string"],
  "years_experience": 0,
  "skills": ["string"],
  "education": ["string"],
  "certifications": ["string"],
  "summary": "3-4 sentence factual summary, no marketing fluff"
}"""

JD_SCHEMA_HINT = """{
  "title": "string",
  "required_skills": ["string"],
  "nice_to_have_skills": ["string"],
  "min_years_experience": 0,
  "education_requirement": "string",
  "responsibilities": ["string"]
}"""

RESUME_EMPTY_FIELDS = {
    "name": None,
    "titles": [],
    "years_experience": 0,
    "skills": [],
    "education": [],
    "certifications": [],
    "summary": "",
}

JD_EMPTY_FIELDS = {
    "title": None,
    "required_skills": [],
    "nice_to_have_skills": [],
    "min_years_experience": 0,
    "education_requirement": "",
    "responsibilities": [],
}


def extract_resume_json(resume_text: str) -> dict:
    prompt = f"""You are an expert resume parser. Extract the following fields from the
resume text below and return ONLY a JSON object matching this exact schema
(no extra keys, no commentary):

{RESUME_SCHEMA_HINT}

Rules:
- "years_experience" is your best-effort estimate of total professional experience, as a number.
- "skills" should be normalized (e.g. "JS" -> "JavaScript") and deduplicated.
- "summary" must be factual, based only on the resume content, 3-4 sentences, no marketing language.

Resume text:
\"\"\"
{resume_text}
\"\"\"
"""
    result = generate_json(prompt)
    if result is None:
        return dict(RESUME_EMPTY_FIELDS)
    return {**RESUME_EMPTY_FIELDS, **result}


def extract_jd_json(jd_text: str) -> dict:
    prompt = f"""You are an expert technical recruiter. Extract the following fields from
the job description below and return ONLY a JSON object matching this exact
schema (no extra keys, no commentary):

{JD_SCHEMA_HINT}

Rules:
- "required_skills" are must-have skills explicitly stated as required.
- "nice_to_have_skills" are skills mentioned as a bonus/preferred, not mandatory.
- "min_years_experience" is a number; use 0 if not specified.

Job description text:
\"\"\"
{jd_text}
\"\"\"
"""
    result = generate_json(prompt)
    if result is None:
        return dict(JD_EMPTY_FIELDS)
    return {**JD_EMPTY_FIELDS, **result}
