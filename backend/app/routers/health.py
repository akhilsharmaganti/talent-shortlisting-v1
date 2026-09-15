from fastapi import APIRouter

from app.services.ollama_client import is_available

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/ollama")
def ollama_health():
    return {"available": is_available()}
