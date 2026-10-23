# PipelineForge

A lightweight CI/CD release-management starter for containerized applications.

## MVP scope
FastAPI API, SQLite persistence, project registry, release-run state machine, tests, lint/format checks, Dockerfile, Compose, and GitHub Actions CI. It records release metadata only; it does not execute arbitrary shell commands or deploy to production.

## Quick start

Python 3.11+ recommended.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
uvicorn pipelineforge.main:app --reload
```

Open http://127.0.0.1:8000/docs.

## Checks

```bash
ruff check .
ruff format --check .
pytest
```

## Docker Compose

```bash
docker compose up --build
```

## API
- `GET /health`
- `POST /api/v1/projects`
- `GET /api/v1/projects`
- `POST /api/v1/projects/{project_id}/runs`
- `GET /api/v1/runs/{run_id}`
- `POST /api/v1/runs/{run_id}/transition`

Example project:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/projects \\
  -H 'Content-Type: application/json' \\
  -d '{"name":"demo-api","git_url":"https://github.com/example/demo-api"}'
```

## Run lifecycle
`pending -> running -> succeeded|failed`. Invalid transitions return HTTP 409.

## Security boundaries
- Never run untrusted repository scripts in the API process.
- Do not mount `/var/run/docker.sock` into the API container.
- Use immutable image digests for deployment promotion.
- Store credentials in a secret manager, never in Git.
- Pin GitHub Actions to reviewed commit SHAs before production use.

## Roadmap
1. MVP API, validation, persistence and CI.
2. Image build metadata, digest tracking and build logs.
3. Isolated deployment runner, health checks and rollback.
4. RBAC, audit events, scanning and integration tests.
