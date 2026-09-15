from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict


class JobDescriptionCreate(BaseModel):
    title: str
    raw_text: str


class JobDescriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    raw_text: str
    extracted_json: dict | None
    created_at: datetime.datetime


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    used_ocr: bool
    extraction_failed: bool
    extracted_json: dict | None
    created_at: datetime.datetime


class RunCreate(BaseModel):
    job_description_id: int
    resume_ids: list[int] | None = None  # None = use all resumes


class RunStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    error_message: str | None
    resume_count: int
    created_at: datetime.datetime
    completed_at: datetime.datetime | None


class CandidateScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resume_id: int
    keyword_score: float
    semantic_score: float
    experience_penalty: float
    combined_score: float
    matched_required: list[str]
    missing_required: list[str]
    matched_nice_to_have: list[str]
    prefiltered_out: bool
    reasoning_text: str


class RunResultsOut(BaseModel):
    run: RunStatusOut
    job_description: JobDescriptionOut
    candidates: list[CandidateScoreOut]


class RunSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    resume_count: int
    created_at: datetime.datetime
    completed_at: datetime.datetime | None
    job_description_id: int
