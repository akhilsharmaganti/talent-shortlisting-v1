# Talent Shortlisting — Resume Screening Platform

An AI-assisted resume screening app: upload a job description and a batch of
resumes (PDF or text), and get back a ranked, explainable shortlist. Combines
two validated local approaches — free, local-only PDF extraction and a hybrid
keyword+semantic+experience scoring pipeline — behind a FastAPI backend and a
React dashboard.

## What it does

1. **Extract** — resume PDFs are converted to text with PyMuPDF, falling back
   to RapidOCR for scanned/image-only pages (see `PDF_TEXT_EXTRACTION_APPROACH.md`).
2. **Structure** — a local LLM (Ollama, `llama3.2:3b`) parses resume and job
   description text into a fixed JSON schema (skills, years of experience,
   education, required/nice-to-have skills, etc).
3. **Score** — each candidate is scored against the JD with a hybrid signal:
   keyword overlap on required/nice-to-have skills, semantic similarity via
   sentence embeddings, and a soft experience-gate penalty. See
   `TEXT_JSON_SCORING_APPROACH.md` for the full rationale, including why
   ranking never relies on semantic similarity alone.
4. **Explain** — the same local LLM writes a short, honest, candidate-specific
   explanation for each score.
5. **Dashboard** — results are persisted (SQLite) and shown in a React
   dashboard: ranked candidate table, score breakdown, matched/missing skill
   chips, score-distribution chart, and run history/comparison.

Everything runs locally with zero API cost — no hosted LLM, no cloud vector
database.

## Architecture

```
resume PDF/txt ──► pdf_extract.py (PyMuPDF + RapidOCR fallback)
                          │
                          ▼
                  extraction.py (Ollama → JSON schema)
                          │
        ┌─────────────────┼─────────────────┐
        ▼                                    ▼
  embeddings.py                        scoring.py
  (cosine similarity,                  (keyword + semantic +
   top-N prefilter)                     experience gate)
        │                                    │
        └─────────────────┬──────────────────┘
                          ▼
                  reasoning.py (Ollama → explanation)
                          │
                          ▼
                  pipeline.py (orchestration)
                          │
                          ▼
          SQLite (job_descriptions, resumes,
                   screening_runs, candidate_scores)
                          │
                          ▼
              FastAPI REST API ──► React dashboard
```

- **Backend**: FastAPI, SQLAlchemy + SQLite, FastAPI `BackgroundTasks` for
  async screening runs (no Celery/Redis — single-instance app).
- **Frontend**: React + Vite + TypeScript, React Router, Recharts.
- **LLM**: local [Ollama](https://ollama.com) running `llama3.2:3b`.
- **Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`), brute-force
  cosine similarity pre-filter (fast enough at hundreds of resumes; isolated
  behind a `TopNSelector` so a FAISS index can be swapped in later without a
  rearchitecture).

## Project layout

```
backend/
  app/
    main.py            FastAPI app, CORS, router registration
    config.py           Ollama URL, DB path, upload dir, scoring weights
    db.py, models.py     SQLAlchemy engine + ORM tables
    schemas.py          Pydantic request/response models
    routers/             job_descriptions, resumes, runs, health
    services/             pdf_extract, ollama_client, extraction,
                           embeddings, scoring, reasoning, pipeline
    jobs.py              background execution of a screening run
  data/uploads/, data/cache/extracted/
  requirements.txt
  screening.db          (created on first run)

frontend/
  src/
    api/client.ts         typed fetch wrappers
    pages/                 JobDescriptionsPage, ResumeUploadPage, RunPage,
                            RunResultsPage, RunHistoryPage
    components/             CandidateTable, ScoreBreakdown, SkillMatchChips,
                             ScoreDistributionChart, RunStatusPoller

PDF_TEXT_EXTRACTION_APPROACH.md   benchmarked PDF extraction recommendation
TEXT_JSON_SCORING_APPROACH.md     hybrid scoring approach documentation
```

## Running it locally

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- [Ollama](https://ollama.com) installed and running, with the model pulled:
  ```
  ollama pull llama3.2:3b
  ```

### Backend

```
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

The API is now at `http://localhost:8000` (interactive docs at `/docs`).
SQLite database (`screening.db`) and upload/cache directories are created
automatically on first startup.

### Frontend

```
cd frontend
npm install
npm run dev
```

The dashboard is now at `http://localhost:5173`, proxying `/api/*` requests
to the backend at `http://localhost:8000`.

## API overview

| Method | Path | Purpose |
|---|---|---|
| GET | `/health`, `/health/ollama` | App / Ollama availability |
| POST/GET/DELETE | `/job-descriptions[/{id}]` | JD CRUD, triggers JD extraction on create |
| POST/GET | `/resumes[/{id}]` | Upload resume file(s), triggers text + JSON extraction |
| POST | `/runs` | Start a screening run (`job_description_id`, optional `resume_ids`) |
| GET | `/runs`, `/runs/{id}`, `/runs/{id}/status` | List runs, full ranked results, poll job status |

## Known limitations

- Scoring weights (`KEYWORD_WEIGHT` / `SEMANTIC_WEIGHT` in `config.py`) are
  hand-picked, not calibrated against labeled human judgments.
- No skill-synonym taxonomy — synonym handling relies entirely on the
  semantic embedding signal.
- Single-pass LLM extraction, no self-consistency/majority voting.
- Brute-force embedding pre-filter is fine at hundreds of resumes; swap in a
  FAISS index in `services/embeddings.py` if the resume pool grows past
  roughly 5,000–10,000.
