from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import ALLOWED_RESUME_EXTENSIONS, MAX_UPLOAD_BYTES, UPLOAD_DIR
from app.db import get_db
from app.models import Resume
from app.schemas import ResumeOut
from app.services.pdf_extract import extract_text

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("", response_model=list[ResumeOut])
async def upload_resumes(files: list[UploadFile], db: Session = Depends(get_db)):
    created: list[Resume] = []
    for file in files:
        ext = Path(file.filename or "").suffix.lower()
        if ext not in ALLOWED_RESUME_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")

        content = await file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=400, detail=f"File too large: {file.filename}")

        content_hash = hashlib.sha256(content).hexdigest()
        existing = db.query(Resume).filter(Resume.content_hash == content_hash).first()
        if existing is not None:
            created.append(existing)
            continue

        dest_path = UPLOAD_DIR / f"{content_hash}{ext}"
        dest_path.write_bytes(content)

        used_ocr = False
        extraction_failed = False
        try:
            if ext == ".pdf":
                text, used_ocr = extract_text(str(dest_path))
            else:
                text = content.decode("utf-8", errors="replace")
            if not text.strip():
                extraction_failed = True
        except Exception:  # noqa: BLE001
            text = ""
            extraction_failed = True

        resume = Resume(
            filename=file.filename or dest_path.name,
            file_path=str(dest_path),
            raw_text=text,
            used_ocr=used_ocr,
            extraction_failed=extraction_failed,
            content_hash=content_hash,
        )
        db.add(resume)
        created.append(resume)

    db.commit()
    for r in created:
        db.refresh(r)
    return created


@router.get("", response_model=list[ResumeOut])
def list_resumes(db: Session = Depends(get_db)):
    return db.query(Resume).order_by(Resume.created_at.desc()).all()


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.get(Resume, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume
