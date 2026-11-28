"""DBA-Pulse backend API (FastAPI). All SQL stays in database.py."""
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src import database

REPORT_PATH = Path(__file__).resolve().parent.parent / "data" / "report.html"

app = FastAPI(
    title="DBA-Pulse API",
    description="REST API for DBA-Pulse analysis runs and findings.",
    version="1.0",
)

Status = Literal["OK", "WARNING", "CRITICAL"]
Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]


class FindingIn(BaseModel):
    area: Optional[str] = Field(None, examples=["Backups"])
    severity: Severity
    message: str = Field(..., min_length=1)


class RunIn(BaseModel):
    overall_status: Status
    analyzed_at: Optional[str] = None
    findings: List[FindingIn] = []


class StatusUpdate(BaseModel):
    overall_status: Status


def _get_run_or_404(run_id: int):
    run = database.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return dict(run)


@app.on_event("startup")
def startup():
    database.init_db()


@app.get("/")
def health():
    return {"service": "DBA-Pulse API", "status": "running"}


@app.get("/runs")
def list_runs(limit: int = 20):
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")
    return [dict(r) for r in database.list_runs(limit)]


@app.get("/runs/{run_id}")
def get_run(run_id: int):
    return _get_run_or_404(run_id)


@app.get("/runs/{run_id}/findings")
def get_findings(run_id: int):
    _get_run_or_404(run_id)
    return [dict(f) for f in database.get_findings(run_id)]


@app.post("/runs", status_code=201)
def create_run(body: RunIn):
    run_id = database.save_run(body.model_dump())
    return {"message": "Run created", "run_id": run_id}


@app.put("/runs/{run_id}/status")
def update_status(run_id: int, body: StatusUpdate):
    _get_run_or_404(run_id)
    database.update_run_status(run_id, body.overall_status)
    return {"message": "Status updated", "run_id": run_id,
            "overall_status": body.overall_status}


@app.delete("/runs/{run_id}")
def delete_run(run_id: int):
    _get_run_or_404(run_id)
    database.delete_run(run_id)
    return {"message": f"Run {run_id} and its findings deleted"}


@app.get("/report")
def latest_report():
    if not REPORT_PATH.exists():
        raise HTTPException(status_code=404, detail="Report not generated yet")
    return FileResponse(REPORT_PATH, media_type="text/html") 

app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")
