from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import JobDescription
from app.schemas import JobDescriptionCreate, JobDescriptionOut
from app.services.extraction import extract_jd_json

router = APIRouter(prefix="/job-descriptions", tags=["job-descriptions"])


@router.post("", response_model=JobDescriptionOut)
def create_job_description(payload: JobDescriptionCreate, db: Session = Depends(get_db)):
    extracted = extract_jd_json(payload.raw_text)
    jd = JobDescription(title=payload.title, raw_text=payload.raw_text, extracted_json=extracted)
    db.add(jd)
    db.commit()
    db.refresh(jd)
    return jd


@router.get("", response_model=list[JobDescriptionOut])
def list_job_descriptions(db: Session = Depends(get_db)):
    return db.query(JobDescription).order_by(JobDescription.created_at.desc()).all()


@router.get("/{jd_id}", response_model=JobDescriptionOut)
def get_job_description(jd_id: int, db: Session = Depends(get_db)):
    jd = db.get(JobDescription, jd_id)
    if jd is None:
        raise HTTPException(status_code=404, detail="Job description not found")
    return jd


@router.delete("/{jd_id}", status_code=204)
def delete_job_description(jd_id: int, db: Session = Depends(get_db)):
    jd = db.get(JobDescription, jd_id)
    if jd is None:
        raise HTTPException(status_code=404, detail="Job description not found")
    db.delete(jd)
    db.commit()
