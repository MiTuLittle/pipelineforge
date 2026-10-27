from pathlib import Path

from fastapi.testclient import TestClient

from pipelineforge import config, database
from pipelineforge.main import app


def make_client(tmp_path: Path, monkeypatch) -> TestClient:
    monkeypatch.setattr(database, "settings", config.Settings(db_path=tmp_path / "test.db"))
    return TestClient(app)


def test_health(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_project_and_release_lifecycle(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        response = client.post(
            "/api/v1/projects",
            json={"name": "demo-api", "git_url": "https://github.com/example/demo-api"},
        )
        assert response.status_code == 201
        project = response.json()
        response = client.post(f"/api/v1/projects/{project['id']}/runs", json={"git_ref": "main"})
        assert response.status_code == 201
        run = response.json()
        assert run["status"] == "pending"
        response = client.post(
            f"/api/v1/runs/{run['id']}/transition",
            json={"status": "running", "detail": "Build started"},
        )
        assert response.status_code == 200
        response = client.post(
            f"/api/v1/runs/{run['id']}/transition",
            json={"status": "succeeded", "detail": "Checks passed"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "succeeded"


def test_duplicate_project_is_conflict(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        payload = {"name": "demo-api", "git_url": "https://github.com/example/demo-api"}
        assert client.post("/api/v1/projects", json=payload).status_code == 201
        response = client.post("/api/v1/projects", json=payload)
    assert response.status_code == 409


def test_invalid_transition_is_rejected(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        project = client.post(
            "/api/v1/projects",
            json={"name": "demo-api", "git_url": "https://github.com/example/demo-api"},
        ).json()
        run = client.post(f"/api/v1/projects/{project['id']}/runs", json={"git_ref": "main"}).json()
        response = client.post(f"/api/v1/runs/{run['id']}/transition", json={"status": "succeeded"})
    assert response.status_code == 409


def test_missing_project_returns_404(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        response = client.post("/api/v1/projects/999/runs", json={"git_ref": "main"})
    assert response.status_code == 404
