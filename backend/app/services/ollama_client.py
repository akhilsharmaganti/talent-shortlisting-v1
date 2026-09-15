"""Thin HTTP wrapper around the local Ollama API."""
from __future__ import annotations

import json

import requests

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL


class OllamaError(RuntimeError):
    pass


def is_available() -> bool:
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def generate_text(prompt: str, *, temperature: float = 0.2) -> str:
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


def generate_json(prompt: str, *, temperature: float = 0.1, retries: int = 1) -> dict | None:
    """Calls Ollama in JSON mode and parses the result. Retries once on a
    parse failure (the model can occasionally emit invalid JSON even in
    format="json" mode), then returns None so the caller can fall back to
    null/empty fields instead of failing the whole pipeline."""
    last_error: Exception | None = None
    for _ in range(retries + 1):
        try:
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": temperature},
                },
                timeout=120,
            )
            resp.raise_for_status()
            raw = resp.json()["response"]
            return json.loads(raw)
        except (requests.RequestException, json.JSONDecodeError, KeyError) as exc:
            last_error = exc
            continue
    return None
