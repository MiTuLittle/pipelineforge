import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from pipelineforge.database import initialize, ping
from pipelineforge.schemas import ProjectCreate, ProjectRead, RunCreate, RunRead, RunTransition
from pipelineforge.service import (
    create_project,
    create_run,
    get_run,
    list_projects,
    transition_run,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize()
    yield


app = FastAPI(
    title="PipelineForge API",
    version="0.1.0",
    description="MVP API for CI/CD project and release-run tracking.",
    lifespan=lifespan,
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    try:
        ping()
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    return {"status": "ok"}


@app.post(
    "/api/v1/projects",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    tags=["projects"],
)
def post_project(payload: ProjectCreate):
    return create_project(payload.name, str(payload.git_url))


@app.get("/api/v1/projects", response_model=list[ProjectRead], tags=["projects"])
def get_projects():
    return list_projects()


@app.post(
    "/api/v1/projects/{project_id}/runs",
    response_model=RunRead,
    status_code=status.HTTP_201_CREATED,
    tags=["release-runs"],
)
def post_run(project_id: int, payload: RunCreate):
    return create_run(project_id, payload.git_ref)


@app.get("/api/v1/runs/{run_id}", response_model=RunRead, tags=["release-runs"])
def read_run(run_id: int):
    return get_run(run_id)


@app.post("/api/v1/runs/{run_id}/transition", response_model=RunRead, tags=["release-runs"])
def post_transition(run_id: int, payload: RunTransition):
    return transition_run(run_id, payload.status, payload.detail)
