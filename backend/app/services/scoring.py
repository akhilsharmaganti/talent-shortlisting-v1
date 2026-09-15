"""Hybrid scoring: keyword + semantic + experience gate.

Per TEXT_JSON_SCORING_APPROACH.md: ranking must not rely on semantic/cosine
similarity alone (extra resume content dilutes the similarity vector), so
keyword-matched required-skill coverage is kept as a first-class signal
alongside semantic similarity rather than the sole ranking driver.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config import (
    KEYWORD_WEIGHT,
    MAX_EXPERIENCE_PENALTY,
    NICE_TO_HAVE_SKILL_WEIGHT,
    REQUIRED_SKILL_WEIGHT,
    SEMANTIC_WEIGHT,
)


@dataclass
class ScoreResult:
    keyword_score: float
    semantic_score: float
    experience_penalty: float
    combined_score: float
    matched_required: list[str]
    missing_required: list[str]
    matched_nice_to_have: list[str]


def _normalize(skill: str) -> str:
    return skill.strip().lower()


def keyword_score(resume_skills: list[str], required_skills: list[str], nice_to_have_skills: list[str]) -> tuple[float, list[str], list[str], list[str]]:
    resume_set = {_normalize(s) for s in resume_skills}
    required_set = {_normalize(s) for s in required_skills}
    nice_set = {_normalize(s) for s in nice_to_have_skills}

    matched_required = sorted(required_set & resume_set)
    missing_required = sorted(required_set - resume_set)
    matched_nice = sorted(nice_set & resume_set)

    required_ratio = len(matched_required) / len(required_set) if required_set else 1.0
    nice_ratio = len(matched_nice) / len(nice_set) if nice_set else 1.0

    score = (REQUIRED_SKILL_WEIGHT * required_ratio + NICE_TO_HAVE_SKILL_WEIGHT * nice_ratio) * 100
    return score, matched_required, missing_required, matched_nice


def experience_penalty(years_experience: float, min_years_experience: float) -> float:
    if not min_years_experience or years_experience >= min_years_experience:
        return 0.0
    shortfall = min_years_experience - years_experience
    penalty = min(MAX_EXPERIENCE_PENALTY, (shortfall / max(min_years_experience, 1)) * MAX_EXPERIENCE_PENALTY)
    return round(penalty, 2)


def combined_score(kw_score: float, sem_score: float, exp_penalty: float) -> float:
    score = KEYWORD_WEIGHT * kw_score + SEMANTIC_WEIGHT * sem_score - exp_penalty
    return round(max(0.0, min(100.0, score)), 2)


def score_candidate(resume_json: dict, jd_json: dict, semantic_similarity: float) -> ScoreResult:
    kw_score, matched_required, missing_required, matched_nice = keyword_score(
        resume_json.get("skills") or [],
        jd_json.get("required_skills") or [],
        jd_json.get("nice_to_have_skills") or [],
    )
    sem_score = round(max(0.0, min(1.0, semantic_similarity)) * 100, 2)
    exp_penalty = experience_penalty(
        resume_json.get("years_experience") or 0,
        jd_json.get("min_years_experience") or 0,
    )
    combined = combined_score(kw_score, sem_score, exp_penalty)

    return ScoreResult(
        keyword_score=round(kw_score, 2),
        semantic_score=sem_score,
        experience_penalty=exp_penalty,
        combined_score=combined,
        matched_required=matched_required,
        missing_required=missing_required,
        matched_nice_to_have=matched_nice,
    )
