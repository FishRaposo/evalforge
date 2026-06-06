"""Tests for the SQLite-backed HistoryStore."""

from __future__ import annotations

from pathlib import Path

import pytest

from evalforge.storage.history import HistoryStore, init_db


class TestHistoryStore:
    """Tests for HistoryStore."""

    @pytest.fixture
    def db_path(self, tmp_path: Path) -> str:
        return str(tmp_path / "test_history.db")

    def test_init_db(self, db_path: str) -> None:
        init_db(db_path)
        assert Path(db_path).exists()

    def test_save_and_get_runs(self, db_path: str) -> None:
        store = HistoryStore(db_path)
        report = {
            "suite_name": "basic_suite",
            "backend": "mock",
            "summary": {
                "total": 5,
                "passed": 4,
                "failed": 1,
                "pass_rate": 0.8,
                "avg_score": 0.75,
            },
            "results": [],
        }

        run_id = store.save_run(report)
        assert run_id > 0

        runs = store.get_runs()
        assert len(runs) == 1
        assert runs[0]["suite_name"] == "basic_suite"
        assert runs[0]["backend"] == "mock"
        assert runs[0]["total_tests"] == 5
        assert runs[0]["passed"] == 4
        assert runs[0]["failed"] == 1
        assert runs[0]["pass_rate"] == 0.8
        assert runs[0]["avg_score"] == 0.75

        run = store.get_run(run_id)
        assert run is not None
        assert run["id"] == run_id

        # Nonexistent run
        assert store.get_run(9999) is None

    def test_get_runs_with_suite_filter(self, db_path: str) -> None:
        store = HistoryStore(db_path)
        store.save_run({"suite_name": "suite_a", "summary": {"total": 1}})
        store.save_run({"suite_name": "suite_b", "summary": {"total": 2}})

        runs_a = store.get_runs(suite_name="suite_a")
        assert len(runs_a) == 1
        assert runs_a[0]["suite_name"] == "suite_a"

        all_runs = store.get_runs()
        assert len(all_runs) == 2

    def test_baselines(self, db_path: str) -> None:
        store = HistoryStore(db_path)
        report = {"suite_name": "suite_a", "summary": {"total": 10}}

        store.set_baseline("suite_a", report)
        baseline = store.get_baseline("suite_a")
        assert baseline is not None
        assert baseline["suite_name"] == "suite_a"
        assert baseline["summary"]["total"] == 10

        # Overwrite
        report_new = {"suite_name": "suite_a", "summary": {"total": 20}}
        store.set_baseline("suite_a", report_new)
        baseline_new = store.get_baseline("suite_a")
        assert baseline_new is not None
        assert baseline_new["summary"]["total"] == 20

        # Nonexistent baseline
        assert store.get_baseline("nonexistent") is None
