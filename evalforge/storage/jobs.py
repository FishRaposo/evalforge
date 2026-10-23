"""SQLite job ledger; claims and report completion are single transactions."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from evalforge.storage.history import HistoryStore, database_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ActiveJobError(ValueError):
    """A different request already owns the global active job slot."""

    def __init__(self, active_job_id: str) -> None:
        super().__init__("Another local evaluation is active")
        self.active_job_id = active_job_id


class RequestConflictError(ValueError):
    """The request UUID has already been used for another profile."""


class JobStore:
    """Persistent jobs shared by connections to the same history database."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.history = HistoryStore(db_path)
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS evaluation_jobs (
                    id TEXT PRIMARY KEY,
                    profile_id TEXT NOT NULL,
                    request_id TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    completed_cases INTEGER NOT NULL DEFAULT 0,
                    total_cases INTEGER NOT NULL,
                    run_id INTEGER REFERENCES runs(id),
                    exit_code INTEGER,
                    gate_json TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS evaluation_one_active
                ON evaluation_jobs ((1)) WHERE status IN ('queued', 'running');
            """)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with database_connection(self.db_path, timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            yield conn

    @staticmethod
    def _public(row: sqlite3.Row) -> dict[str, Any]:
        job = dict(row)
        job["gate"] = json.loads(job.pop("gate_json")) if job["gate_json"] else None
        job.pop("gate_json", None)
        return job

    def get(self, job_id: str) -> dict[str, Any] | None:
        """Return durable state, or None for an unknown job."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM evaluation_jobs WHERE id=?", (job_id,)
            ).fetchone()
        return self._public(row) if row else None

    def get_by_request(self, request_id: str) -> dict[str, Any] | None:
        """Idempotent retries read the original job without reopening its inputs."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM evaluation_jobs WHERE request_id=?", (request_id,)
            ).fetchone()
        return self._public(row) if row else None

    def claim(
        self, profile_id: str, request_id: str, total_cases: int
    ) -> tuple[dict[str, Any], bool]:
        """Claim one global active slot, with UUID idempotency before busy checks."""
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT * FROM evaluation_jobs WHERE request_id=?", (request_id,)
            ).fetchone()
            if existing:
                if existing["profile_id"] != profile_id:
                    raise RequestConflictError(
                        "Request UUID belongs to another profile"
                    )
                return self._public(existing), False
            active = conn.execute(
                "SELECT id FROM evaluation_jobs WHERE status IN ('queued','running')"
            ).fetchone()
            if active:
                raise ActiveJobError(active["id"])
            job_id, now = str(uuid4()), _now()
            conn.execute(
                """INSERT INTO evaluation_jobs
                (id,profile_id,request_id,status,total_cases,created_at,updated_at)
                VALUES (?,?,?,'queued',?,?,?)""",
                (job_id, profile_id, request_id, total_cases, now, now),
            )
            row = conn.execute(
                "SELECT * FROM evaluation_jobs WHERE id=?", (job_id,)
            ).fetchone()
            assert row is not None
            return self._public(row), True

    def start(self, job_id: str) -> bool:
        """Only the worker that transitions queued to running may execute."""
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE evaluation_jobs SET status='running',updated_at=? "
                "WHERE id=? AND status='queued'",
                (_now(), job_id),
            )
            return cur.rowcount == 1

    def progress(self, job_id: str, completed: int, total: int) -> None:
        """Persist monotonic counts; never accept a fabricated total or overflow."""
        with self._connect() as conn:
            conn.execute(
                """UPDATE evaluation_jobs SET completed_cases=?,updated_at=?
                WHERE id=? AND status='running' AND total_cases=?
                AND completed_cases<=? AND ?>=0 AND ?<=total_cases""",
                (completed, _now(), job_id, total, completed, completed, completed),
            )

    def finish(self, job_id: str, report: dict[str, Any], exit_code: int) -> int | None:
        """Commit the report and terminal job together, exactly once even in a race."""
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM evaluation_jobs WHERE id=?", (job_id,)
            ).fetchone()
            if not row or row["status"] != "running":
                return row["run_id"] if row else None
            run_id = self.history.save_run_in_connection(conn, report)
            gate = report.get("metadata", {}).get("gate")
            conn.execute(
                """UPDATE evaluation_jobs SET status='completed',
                completed_cases=total_cases,run_id=?,exit_code=?,gate_json=?,updated_at=?
                WHERE id=? AND status='running'""",
                (
                    run_id,
                    exit_code,
                    json.dumps(gate) if gate is not None else None,
                    _now(),
                    job_id,
                ),
            )
            return run_id

    def fail(self, job_id: str, error: str) -> None:
        """Record an infrastructure failure without fabricating a report or gate."""
        with self._connect() as conn:
            conn.execute(
                """UPDATE evaluation_jobs SET status='failed',error=?,updated_at=?
                WHERE id=? AND status IN ('queued','running')""",
                (error, _now(), job_id),
            )

    def interrupt_pending(self) -> int:
        """Preserve partial progress on restart; require an explicit retry."""
        with self._connect() as conn:
            cur = conn.execute(
                """UPDATE evaluation_jobs SET status='interrupted',
                error='Service restarted; launch a new request to retry',updated_at=?
                WHERE status IN ('queued','running')""",
                (_now(),),
            )
            return cur.rowcount
