"""Background execution of a screening run, invoked via FastAPI BackgroundTasks.

Status is tracked directly on the ScreeningRun DB row (queued/running/done/
error) rather than a separate in-memory table, so it survives across
requests within the same process without extra infra.
"""
from __future__ import annotations

import datetime

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import CandidateScore, Resume, ScreeningRun
from app.services.pipeline import run_screening


def execute_run(run_id: int, resume_ids: list[int]) -> None:
    db: Session = SessionLocal()
    try:
        run = db.get(ScreeningRun, run_id)
        if run is None:
            return
        run.status = "running"
        db.commit()

        resumes = db.query(Resume).filter(Resume.id.in_(resume_ids)).all()
        resume_payload = [{"id": r.id, "text": r.raw_text} for r in resumes]

        try:
            result = run_screening(run.job_description.raw_text, resume_payload)
        except Exception as exc:  # noqa: BLE001
            run.status = "error"
            run.error_message = str(exc)
            db.commit()
            return

        run.job_description.extracted_json = result["jd_json"]

        for candidate in result["candidates"]:
            db.add(
                CandidateScore(
                    run_id=run.id,
                    resume_id=candidate.resume_id,
                    keyword_score=candidate.score.keyword_score,
                    semantic_score=candidate.score.semantic_score,
                    experience_penalty=candidate.score.experience_penalty,
                    combined_score=candidate.score.combined_score,
                    matched_required=candidate.score.matched_required,
                    missing_required=candidate.score.missing_required,
                    matched_nice_to_have=candidate.score.matched_nice_to_have,
                    prefiltered_out=candidate.prefiltered_out,
                    reasoning_text=candidate.reasoning,
                )
            )
            resume = db.get(Resume, candidate.resume_id)
            if resume is not None:
                resume.extracted_json = candidate.resume_json

        run.status = "done"
        run.completed_at = datetime.datetime.utcnow()
        db.commit()
    finally:
        db.close()
