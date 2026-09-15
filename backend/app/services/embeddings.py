"""Sentence-embedding helpers: JD/resume similarity + a brute-force top-N
pre-filter shortlist.

Per TEXT_JSON_SCORING_APPROACH.md's scaling notes: at hundreds of resumes,
brute-force cosine similarity over numpy arrays is still sub-millisecond, so
no ANN index (FAISS/pgvector) is needed yet. This module is isolated so a
FAISS-backed TopNSelector can be swapped in later without touching callers.
"""
from __future__ import annotations

import numpy as np

from app.config import EMBEDDING_MODEL_NAME

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def embed_text(text: str) -> np.ndarray:
    model = _get_model()
    return model.encode(text, normalize_embeddings=True)


def embed_texts(texts: list[str]) -> np.ndarray:
    model = _get_model()
    return model.encode(texts, normalize_embeddings=True)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))


class TopNSelector:
    """Brute-force cosine-similarity shortlist of resume indices for a JD
    embedding. Swap the body of `select` for a FAISS index lookup if the
    resume pool grows past ~5-10k without changing the caller's interface."""

    def select(self, jd_embedding: np.ndarray, resume_embeddings: np.ndarray, top_n: int) -> list[int]:
        if resume_embeddings.shape[0] <= top_n:
            return list(range(resume_embeddings.shape[0]))
        scores = resume_embeddings @ jd_embedding
        return list(np.argsort(-scores)[:top_n])


def resume_embedding_text(resume_json: dict) -> str:
    skills = ", ".join(resume_json.get("skills") or [])
    return f"{resume_json.get('summary', '')}\nSkills: {skills}"


def jd_embedding_text(jd_json: dict) -> str:
    required = ", ".join(jd_json.get("required_skills") or [])
    nice = ", ".join(jd_json.get("nice_to_have_skills") or [])
    responsibilities = " ".join(jd_json.get("responsibilities") or [])
    return f"Required skills: {required}\nNice to have: {nice}\nResponsibilities: {responsibilities}"
