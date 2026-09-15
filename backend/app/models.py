from __future__ import annotations

import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    raw_text: Mapped[str] = mapped_column(Text)
    extracted_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=_now)

    runs: Mapped[list["ScreeningRun"]] = relationship(back_populates="job_description")


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    raw_text: Mapped[str] = mapped_column(Text)
    used_ocr: Mapped[bool] = mapped_column(Boolean, default=False)
    extraction_failed: Mapped[bool] = mapped_column(Boolean, default=False)
    extracted_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=_now)


class ScreeningRun(Base):
    __tablename__ = "screening_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_description_id: Mapped[int] = mapped_column(ForeignKey("job_descriptions.id"))
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued|running|done|error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=_now)
    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    job_description: Mapped["JobDescription"] = relationship(back_populates="runs")
    candidate_scores: Mapped[list["CandidateScore"]] = relationship(back_populates="run")


class CandidateScore(Base):
    __tablename__ = "candidate_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("screening_runs.id"), index=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"))
    keyword_score: Mapped[float] = mapped_column(Float)
    semantic_score: Mapped[float] = mapped_column(Float)
    experience_penalty: Mapped[float] = mapped_column(Float)
    combined_score: Mapped[float] = mapped_column(Float, index=True)
    matched_required: Mapped[list] = mapped_column(JSON, default=list)
    missing_required: Mapped[list] = mapped_column(JSON, default=list)
    matched_nice_to_have: Mapped[list] = mapped_column(JSON, default=list)
    prefiltered_out: Mapped[bool] = mapped_column(Boolean, default=False)
    reasoning_text: Mapped[str] = mapped_column(Text)

    run: Mapped["ScreeningRun"] = relationship(back_populates="candidate_scores")
    resume: Mapped["Resume"] = relationship()
