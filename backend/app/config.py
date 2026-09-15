import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
EXTRACTED_CACHE_DIR = DATA_DIR / "cache" / "extracted"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EXTRACTED_CACHE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'screening.db'}")

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Hybrid scoring weights, per TEXT_JSON_SCORING_APPROACH.md
KEYWORD_WEIGHT = 0.45
SEMANTIC_WEIGHT = 0.55
REQUIRED_SKILL_WEIGHT = 0.85
NICE_TO_HAVE_SKILL_WEIGHT = 0.15
MAX_EXPERIENCE_PENALTY = 20.0

# Pre-filter: how many candidates survive the embedding shortlist before
# the expensive per-candidate LLM reasoning stage runs.
PREFILTER_TOP_N = 50

MIN_CHARS_PER_PAGE = 20  # below this, a PDF page is treated as scanned/no text layer

MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB per resume file
ALLOWED_RESUME_EXTENSIONS = {".pdf", ".txt"}
