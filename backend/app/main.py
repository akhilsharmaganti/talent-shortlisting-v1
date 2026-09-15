from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routers import health, job_descriptions, resumes, runs

app = FastAPI(title="Resume Screening API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(job_descriptions.router)
app.include_router(resumes.router)
app.include_router(runs.router)


@app.on_event("startup")
def on_startup():
    init_db()
