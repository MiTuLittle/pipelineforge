from fastapi import HTTPException

from pipelineforge.database import execute, fetch_all, fetch_one

ALLOWED_TRANSITIONS = {
    "pending": {"running", "failed"},
    "running": {"succeeded", "failed"},
    "succeeded": set(),
    "failed": set(),
}


def create_project(name: str, git_url: str) -> dict:
    try:
        project_id = execute(
            "INSERT INTO projects(name, git_url) VALUES (?, ?)", (name, git_url)
        )
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=409, detail="Project name already exists") from exc
        raise
    project = fetch_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    assert project is not None
    return project


def list_projects() -> list[dict]:
    return fetch_all("SELECT * FROM projects ORDER BY id DESC")


def create_run(project_id: int, git_ref: str) -> dict:
    if fetch_one("SELECT id FROM projects WHERE id = ?", (project_id,)) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    run_id = execute(
        "INSERT INTO release_runs(project_id, git_ref, status) VALUES (?, ?, 'pending')",
        (project_id, git_ref),
    )
    run = fetch_one("SELECT * FROM release_runs WHERE id = ?", (run_id,))
    assert run is not None
    return run


def get_run(run_id: int) -> dict:
    run = fetch_one("SELECT * FROM release_runs WHERE id = ?", (run_id,))
    if run is None:
        raise HTTPException(status_code=404, detail="Release run not found")
    return run


def transition_run(run_id: int, target: str, detail: str | None) -> dict:
    run = get_run(run_id)
    if target not in ALLOWED_TRANSITIONS[run["status"]]:
        raise HTTPException(
            status_code=409,
            detail=f"Invalid transition: {run['status']} -> {target}",
        )
    execute(
        """UPDATE release_runs
           SET status = ?, detail = ?, updated_at = CURRENT_TIMESTAMP
           WHERE id = ?""",
        (target, detail, run_id),
    )
    return get_run(run_id)
