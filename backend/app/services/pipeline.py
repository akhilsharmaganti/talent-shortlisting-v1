"""Orchestrates a full screening run: prefilter -> extract -> score -> reason.

Ollama calls are made sequentially, not in parallel, because a small
CPU-bound local model serializes better than concurrent requests and this
avoids resource contention/timeouts (not addressed in either approach doc).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

from app.config import EXTRACTED_CACHE_DIR, PREFILTER_TOP_N
from app.services import embeddings
from app.services.extraction import extract_jd_json, extract_resume_json
from app.services.reasoning import generate_reasoning
from app.services.scoring import ScoreResult, score_candidate


@dataclass
class CandidateResult:
    resume_id: int | str
    resume_json: dict
    score: ScoreResult
    reasoning: str
    prefiltered_out: bool = False


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _cached_extract(text: str, kind: str) -> dict:
    """kind is 'resume' or 'jd'. Extraction results are cached to disk keyed
    by content hash, per TEXT_JSON_SCORING_APPROACH.md, so re-running the
    pipeline after a scoring/reasoning code change doesn't re-run extraction."""
    key = f"{kind}_{_content_hash(text)}"
    cache_path = EXTRACTED_CACHE_DIR / f"{key}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    result = extract_jd_json(text) if kind == "jd" else extract_resume_json(text)
    cache_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def run_screening(jd_text: str, resumes: list[dict]) -> dict:
    """resumes: list of {"id": ..., "text": ...}. Returns
    {"jd_json": ..., "candidates": [CandidateResult, ...]} ranked by
    combined_score descending."""
    jd_json = _cached_extract(jd_text, "jd")
    jd_embedding = embeddings.embed_text(embeddings.jd_embedding_text(jd_json))

    resume_jsons = [_cached_extract(r["text"], "resume") for r in resumes]
    resume_embeddings = embeddings.embed_texts(
        [embeddings.resume_embedding_text(rj) for rj in resume_jsons]
    )

    selector = embeddings.TopNSelector()
    shortlist_idx = set(selector.select(jd_embedding, resume_embeddings, PREFILTER_TOP_N))

    candidates: list[CandidateResult] = []
    for i, resume in enumerate(resumes):
        resume_json = resume_jsons[i]
        if i not in shortlist_idx:
            candidates.append(
                CandidateResult(
                    resume_id=resume["id"],
                    resume_json=resume_json,
                    score=score_candidate(resume_json, jd_json, 0.0),
                    reasoning="Not shortlisted for detailed review (low embedding similarity to this JD).",
                    prefiltered_out=True,
                )
            )
            continue

        sim = embeddings.cosine_similarity(resume_embeddings[i], jd_embedding)
        score = score_candidate(resume_json, jd_json, sim)
        reasoning = generate_reasoning(resume_json, jd_json, score)
        candidates.append(
            CandidateResult(resume_id=resume["id"], resume_json=resume_json, score=score, reasoning=reasoning)
        )

    candidates.sort(key=lambda c: c.score.combined_score, reverse=True)
    return {"jd_json": jd_json, "candidates": candidates}


def candidate_result_to_dict(result: CandidateResult) -> dict:
    d = asdict(result)
    return d
