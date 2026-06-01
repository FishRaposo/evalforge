"""SQLite-backed evaluation history storage."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any


class HistoryStore:
    """Persistent store for evaluation run history.

    Uses SQLite for lightweight, zero-config storage.
    """

    def __init__(self, db_path: str = "evalforge_history.db") -> None:
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    suite_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    backend TEXT,
                    total_tests INTEGER,
                    passed INTEGER,
                    failed INTEGER,
                    pass_rate REAL,
                    avg_score REAL,
                    report_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    suite_name TEXT NOT NULL UNIQUE,
                    timestamp TEXT NOT NULL,
                    report_json TEXT NOT NULL
                )
                """
            )

    def save_run(self, report: dict[str, Any]) -> int:
        """Save a report and return the run ID.

        Args:
            report: Evaluation report dictionary.

        Returns:
            The inserted run ID.
        """
        summary = report.get("summary", {})
        with sqlite3.connect(self._db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO runs
                (suite_name, timestamp, backend, total_tests, passed,
                 failed, pass_rate, avg_score, report_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report.get("suite_name", "unknown"),
                    datetime.now().isoformat(),
                    report.get("backend"),
                    summary.get("total_tests", 0),
                    summary.get("passed", 0),
                    summary.get("failed", 0),
                    summary.get("pass_rate", 0.0),
                    summary.get("avg_score", 0.0),
                    json.dumps(report),
                ),
            )
            return cur.lastrowid or 0

    def get_runs(
        self, suite_name: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Fetch recent runs, optionally filtered by suite name.

        Args:
            suite_name: Optional suite name filter.
            limit: Maximum rows to return.

        Returns:
            List of run dictionaries.
        """
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            if suite_name:
                rows = conn.execute(
                    "SELECT * FROM runs WHERE suite_name = ? ORDER BY timestamp DESC LIMIT ?",
                    (suite_name, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM runs ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [dict(row) for row in rows]

    def get_run(self, run_id: int) -> dict[str, Any] | None:
        """Fetch a single run by ID.

        Args:
            run_id: The run ID.

        Returns:
            Run dictionary or None.
        """
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM runs WHERE id = ?", (run_id,)
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    def set_baseline(self, suite_name: str, report: dict[str, Any]) -> None:
        """Save or overwrite a baseline for a suite.

        Args:
            suite_name: The suite name.
            report: The baseline report.
        """
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO baselines (suite_name, timestamp, report_json)
                VALUES (?, ?, ?)
                ON CONFLICT(suite_name) DO UPDATE SET
                    timestamp=excluded.timestamp,
                    report_json=excluded.report_json
                """,
                (suite_name, datetime.now().isoformat(), json.dumps(report)),
            )

    def get_baseline(self, suite_name: str) -> dict[str, Any] | None:
        """Fetch the stored baseline for a suite.

        Args:
            suite_name: The suite name.

        Returns:
            Baseline report dictionary or None.
        """
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT report_json FROM baselines WHERE suite_name = ?", (suite_name,)
            ).fetchone()
        if row is None:
            return None
        data = json.loads(row["report_json"])
        if isinstance(data, dict):
            return data
        return None


def init_db(db_path: str = "evalforge_history.db") -> None:
    """Initialize the history database.

    Args:
        db_path: Path to the SQLite database.
    """
    HistoryStore(db_path)
    # Table creation happens in __init__
