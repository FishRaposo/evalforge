"""FastAPI app for EvalForge history and comparison API."""

from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from evalforge.storage.history import HistoryStore


class RunIn(BaseModel):
    """Request model for saving a run."""

    suite_name: str
    backend: str | None = None
    summary: dict[str, Any] = {}
    results: list[dict[str, Any]] = []


class CompareIn(BaseModel):
    """Request model for comparing two runs."""

    run_a_id: int
    run_b_id: int


def create_app(db_path: str = "evalforge_history.db") -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        db_path: Path to the SQLite history database.

    Returns:
        Configured FastAPI app.
    """
    app = FastAPI(title="EvalForge API", version="0.1.0")
    store = HistoryStore(db_path)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/runs")
    def list_runs(suite_name: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """List recent evaluation runs."""
        return store.get_runs(suite_name=suite_name, limit=limit)

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: int) -> dict[str, Any]:
        """Get a single run by ID."""
        run = store.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return run

    @app.post("/api/runs")
    def save_run(body: dict[str, Any]) -> dict[str, int]:
        """Save a new evaluation run."""
        run_id = store.save_run(body)
        return {"id": run_id}

    @app.post("/api/runs/compare")
    def compare_runs(body: CompareIn) -> dict[str, Any]:
        """Compare two runs and return deltas."""
        a = store.get_run(body.run_a_id)
        b = store.get_run(body.run_b_id)
        if a is None or b is None:
            raise HTTPException(status_code=404, detail="One or both runs not found")

        a_summary = json.loads(a["report_json"]).get("summary", {})
        b_summary = json.loads(b["report_json"]).get("summary", {})

        return {
            "run_a_id": body.run_a_id,
            "run_b_id": body.run_b_id,
            "pass_rate_delta": b_summary.get("pass_rate", 0.0) - a_summary.get("pass_rate", 0.0),
            "avg_score_delta": b_summary.get("avg_score", 0.0) - a_summary.get("avg_score", 0.0),
        }

    @app.get("/api/baselines/{suite_name}")
    def get_baseline(suite_name: str) -> dict[str, Any]:
        """Get the stored baseline for a suite."""
        baseline = store.get_baseline(suite_name)
        if baseline is None:
            raise HTTPException(status_code=404, detail="Baseline not found")
        return baseline

    @app.post("/api/baselines/{suite_name}")
    def set_baseline(suite_name: str, body: dict[str, Any]) -> dict[str, str]:
        """Set the baseline for a suite."""
        store.set_baseline(suite_name, body)
        return {"status": "saved"}

    return app
