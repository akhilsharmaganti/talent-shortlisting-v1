from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.jobs import execute_run
from app.models import CandidateScore, JobDescription, Resume, ScreeningRun
from app.schemas import RunCreate, RunResultsOut, RunStatusOut, RunSummaryOut

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunStatusOut)
def create_run(payload: RunCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    jd = db.get(JobDescription, payload.job_description_id)
    if jd is None:
        raise HTTPException(status_code=404, detail="Job description not found")

    if payload.resume_ids:
        resumes = db.query(Resume).filter(Resume.id.in_(payload.resume_ids)).all()
    else:
        resumes = db.query(Resume).all()

    if not resumes:
        raise HTTPException(status_code=400, detail="No resumes available to screen")

    run = ScreeningRun(job_description_id=jd.id, status="queued", resume_count=len(resumes))
    db.add(run)
    db.commit()
    db.refresh(run)

    resume_ids = [r.id for r in resumes]
    background_tasks.add_task(execute_run, run.id, resume_ids)

    return run


@router.get("", response_model=list[RunSummaryOut])
def list_runs(db: Session = Depends(get_db)):
    return db.query(ScreeningRun).order_by(ScreeningRun.created_at.desc()).all()


@router.get("/{run_id}/status", response_model=RunStatusOut)
def get_run_status(run_id: int, db: Session = Depends(get_db)):
    run = db.get(ScreeningRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/{run_id}", response_model=RunResultsOut)
def get_run_results(run_id: int, db: Session = Depends(get_db)):
    run = db.get(ScreeningRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    candidates = (
        db.query(CandidateScore)
        .filter(CandidateScore.run_id == run_id)
        .order_by(CandidateScore.combined_score.desc())
        .all()
    )

    return {"run": run, "job_description": run.job_description, "candidates": candidates}
