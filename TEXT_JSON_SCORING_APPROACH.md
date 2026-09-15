# Resume-to-Job-Description Matching: Approach Documentation

This document describes an end-to-end pipeline that scores candidate resumes against a job
description, with human-readable reasoning for each score. It runs entirely locally with zero
API cost. This is a description of a **working, tested implementation** (not a proposal) —
every stage below corresponds to real code in this repo.

## Problem being solved

Given raw resume text (already extracted from PDFs/docs by some upstream tool) and a job
description, produce for each candidate:
1. A numeric match score (0-100)
2. A breakdown of which required skills were matched/missing
3. A human-readable explanation of why the candidate scored the way they did

Scale target: this implementation was built and tested for one JD against ~10 resumes
(a "many resumes, one job" screening scenario). The design notes below call out what changes
at larger scale (many resumes x many JDs).

## High-level pipeline

```
Raw resume text ──┐
                   ├─► [1] LLM Extraction ──► Structured JSON ──┐
Raw JD text ───────┘                                             │
                                                                   ├─► [2] Hybrid Scoring ──► [3] LLM Reasoning ──► [4] Report
                                                                   │
                                                        (keyword + semantic + experience)
```

### Stage 1 — Extraction (unstructured text → JSON)

**Why an LLM and not regex/NER:** resumes vary hugely in format (headers, ordering, phrasing).
A rule-based parser (regex section-header detection, spaCy NER, gazetteer/PhraseMatcher skill
lists) is faster and fully deterministic, but brittle — it breaks on multi-column layouts,
nonstandard section headers, or paraphrased content. An LLM with a fixed JSON schema handles
that variance robustly. This is the one stage where an LLM earns its cost.

**Implementation:** a local LLM via [Ollama](https://ollama.com) (`llama3.2:3b`, ~2GB, runs on
CPU, zero API cost) is prompted to extract a fixed JSON schema from raw text.

Resume schema:
```json
{
  "name": "string",
  "titles": ["string"],
  "years_experience": 0,
  "skills": ["string"],
  "education": ["string"],
  "certifications": ["string"],
  "summary": "3-4 sentence factual summary, no marketing fluff"
}
```

Job description schema:
```json
{
  "title": "string",
  "required_skills": ["string"],
  "nice_to_have_skills": ["string"],
  "min_years_experience": 0,
  "education_requirement": "string",
  "responsibilities": ["string"]
}
```

The extraction prompt and schema live in `src/extract.py`. The Ollama HTTP API call
(`format: "json"` mode, forcing valid JSON output) lives in `src/ollama_client.py`.
Extraction results are cached to disk (`output/extracted/*.json`) keyed by source filename, so
re-running the pipeline after a code change to scoring/reasoning doesn't re-run extraction.

### Stage 2 — Hybrid scoring (keyword + semantic + experience)

Implemented in `src/match.py`. Three independent signals are computed per resume/JD pair and
combined:

**a) Keyword score** — exact/substring overlap between the resume's skill list and the JD's
`required_skills` / `nice_to_have_skills` (case-insensitive, normalized). Required skills are
weighted far more heavily than nice-to-have skills (`0.85 * required_ratio + 0.15 * nice_ratio`,
scaled to 0-100). This catches explicit, unambiguous skill matches and produces the
matched/missing skill lists shown in the report.

**b) Semantic score** — cosine similarity between a sentence embedding of the resume
(summary + skills text) and the JD (required + nice-to-have skills + responsibilities text).
Uses `sentence-transformers` with the `all-MiniLM-L6-v2` model (~80MB, runs locally on CPU, no
API cost). This catches paraphrased/synonym matches that keyword matching misses — e.g. a
resume saying "managed relational databases in production" instead of "PostgreSQL" still scores
well semantically even though it has zero keyword overlap on that skill.

**c) Experience gate** — compares the resume's `years_experience` against the JD's
`min_years_experience`. A shortfall is a *soft* penalty (up to -20 points, scaled by how many
years short), not a hard disqualifier — a slightly under-experienced but otherwise strong
candidate still surfaces in results rather than being filtered out entirely.

**Combination:** `combined_score = 0.45 * keyword_score + 0.55 * semantic_score`, then the
experience penalty is subtracted if applicable. These weights are a reasonable starting point,
not empirically tuned — see "Known limitations" below.

**Important design note (validated against related approaches):** ranking must not be done by
semantic/cosine similarity alone. A candidate with many additional skills beyond what's required
can score *lower* on raw cosine similarity than a candidate with only the exact required
skills, because the extra content dilutes the similarity vector. This is why keyword-matched
required-skill coverage is weighted as a first-class signal alongside semantic similarity,
rather than relying on semantic similarity as the primary or sole ranking signal.

### Stage 3 — LLM reasoning (score → explanation)

Implemented in `src/reasoning.py`. The same local LLM (Ollama `llama3.2:3b`) is given the
structured resume JSON, JD JSON, and the computed scores (keyword score, semantic score,
combined score, matched/missing required skills), and asked to write a 3-4 sentence
recruiter-facing explanation. The prompt explicitly asks the model to:
- Name which required skills are present/missing
- Comment on whether experience meets the bar
- Credit semantically-relevant experience even without exact keyword matches
- Be honest about weaknesses, not just strengths

This is what makes the score explainable rather than a black-box number — every score comes
with a specific, candidate-grounded justification, not generic boilerplate.

### Stage 4 — Report generation

Implemented in `src/report.py` (HTML) and `src/pipeline.py` (orchestration + JSON output).
Output:
- `output/results.json` — full structured results (JD, all resumes, all scores, all reasoning text)
- `output/report.html` — a static, styleable HTML report: candidates ranked by `combined_score`,
  with score bars (keyword/semantic breakdown), matched/missing required skills, and the
  reasoning paragraph per candidate

## Tech stack (all free, all local)

| Component | Tool | Cost |
|---|---|---|
| JSON extraction | Ollama + `llama3.2:3b` | Free, local, CPU |
| Reasoning generation | Ollama + `llama3.2:3b` (same model) | Free, local, CPU |
| Semantic similarity | `sentence-transformers` (`all-MiniLM-L6-v2`) | Free, local, CPU |
| Keyword matching | Plain Python set operations | Free |
| Report rendering | Plain Python string templating (no framework) | Free |

No vector database, no RAG framework, no paid API calls anywhere in this pipeline.

## Explicit non-approaches (and why)

- **No RAG.** RAG solves "retrieve relevant context from a large corpus I can't fit in a
  prompt." Here, both documents (one resume, one JD) are small and already fully known — there's
  nothing to retrieve. What might look like RAG (an embedding similarity step) is here used
  purely as a *scoring signal*, not as context retrieval for generation.
- **No vector database.** At this scale (one JD, ~10 resumes) all embeddings fit trivially in
  memory; brute-force cosine similarity is instant. A vector index (FAISS, pgvector) would only
  earn its cost at hundreds/thousands of resumes needing sub-linear search — see "Scaling notes."
- **No keyword-only or semantic-only matching.** Keyword-only misses synonyms/paraphrasing.
  Semantic-only can be diluted or gamed (see the ranking note in Stage 2). Both signals are
  needed together.

## Scaling notes (if this grows to many resumes x many job descriptions)

The current implementation is built for "one JD, several resumes." At larger scale:
1. Add an **embedding pre-filter**: before running the full hybrid-scoring + LLM-reasoning
   pipeline (expensive), embed all resumes once and store in an ANN index (FAISS/pgvector), then
   retrieve only the top-N candidates per JD by cosine similarity before doing detailed scoring.
   This bounds LLM reasoning cost regardless of total resume pool size.
2. Consider a cheaper **category pre-filter** (a small trained classifier bucketing resumes into
   job categories) as an alternative/complement to the embedding pre-filter, if resumes/JDs fall
   into clean categories and labeled training data is available.
3. Consider a **cross-encoder reranking** step on the shortlist from step 1 — cross-encoders
   score resume/JD pairs jointly and are more accurate than independent embeddings, but don't
   scale to the full pool since they can't be pre-computed/indexed.

## Known limitations / ideas for improving accuracy

- **Scoring weights are hand-picked, not tuned.** `kw_weight=0.45`, `sem_weight=0.55` in
  `match.py:combined_score` should ideally be calibrated against a labeled set of human
  good-fit/bad-fit judgments rather than guessed.
- **Small local LLM (3B params) is the weakest link.** It's fast and free but less accurate at
  extraction (years-of-experience inference, skill normalization) than a larger local model or a
  hosted frontier model would be. This is a deliberate cost/speed tradeoff, not a hard
  constraint of the architecture — swapping the model in `ollama_client.py` requires no other
  changes.
- **No skill taxonomy normalization.** Synonym handling currently relies entirely on the
  semantic embedding step. A curated skill synonym map (or an external taxonomy like ESCO/O*NET)
  applied before matching would catch synonyms deterministically instead of only probabilistically.
- **Single-pass extraction.** No self-consistency/majority-voting across multiple LLM extraction
  calls to reduce single-pass noise.
- **No human feedback loop.** Recruiter accept/reject decisions aren't currently fed back into
  weight calibration or model fine-tuning.

## File reference (for integration)

| File | Responsibility |
|---|---|
| `src/ollama_client.py` | Thin HTTP wrapper around local Ollama API (`generate_json`, `generate_text`) |
| `src/extract.py` | Prompts + schema for resume/JD → JSON extraction |
| `src/match.py` | Keyword score, semantic score, experience gate, combined scoring |
| `src/reasoning.py` | Prompt + call for generating the recruiter-facing explanation |
| `src/report.py` | HTML report rendering (ranked cards, score bars, reasoning) |
| `src/pipeline.py` | Orchestrates the full run: extract (cached) → score → reason → write outputs |
| `data/job_description.txt` | Input JD (plain text) |
| `data/resumes/*.txt` | Input resumes (plain text) |
| `output/extracted/*.json` | Cached extraction results |
| `output/results.json` | Full structured output of a pipeline run |
| `output/report.html` | Final rendered report |

## Requirements to run

- Python 3.x with `sentence-transformers`, `scikit-learn`, `numpy`, `requests` (see
  `requirements.txt`)
- [Ollama](https://ollama.com) installed and running locally, with `llama3.2:3b` pulled
  (`ollama pull llama3.2:3b`)
- Run: `python src/pipeline.py` from the project root
