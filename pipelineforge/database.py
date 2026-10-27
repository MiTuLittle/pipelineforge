import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Any

from pipelineforge.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    git_url TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS release_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    git_ref TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'succeeded', 'failed')),
    detail TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);
"""


BUSY_TIMEOUT_SECONDS = 5.0


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or settings.db_path
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path), timeout=BUSY_TIMEOUT_SECONDS, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    # WAL keeps readers from blocking on writers; the mode is persisted per database file.
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    return connection


@contextmanager
def session(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Yield a connection that commits on success, rolls back on error, and always closes."""
    connection = connect(db_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize(db_path: Path | None = None) -> None:
    with session(db_path) as connection:
        connection.executescript(SCHEMA)


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with closing(connect()) as connection:
        row = connection.execute(query, params).fetchone()
        return dict(row) if row else None


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with closing(connect()) as connection:
        return [dict(row) for row in connection.execute(query, params).fetchall()]


def ping() -> None:
    """Raise if the database cannot be reached."""
    fetch_one("SELECT 1 AS alive")


def execute(query: str, params: tuple[Any, ...] = ()) -> int:
    with session() as connection:
        cursor = connection.execute(query, params)
        return int(cursor.lastrowid or 0)


def execute_affected(query: str, params: tuple[Any, ...] = ()) -> int:
    """Run a write statement and return the number of rows it affected."""
    with session() as connection:
        return int(connection.execute(query, params).rowcount)
