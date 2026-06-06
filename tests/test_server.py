"""Tests for the FastAPI server app."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from evalforge.server.app import create_app


class TestServerApp:
    """Tests for FastAPI server endpoints."""

    @pytest.fixture
    def client(self, tmp_path: Path) -> TestClient:
        db_path = tmp_path / "test_history.db"
        app = create_app(db_path=str(db_path))
        return TestClient(app)

    def test_health_endpoint(self, client: TestClient) -> None:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_runs_endpoints(self, client: TestClient) -> None:
        # Initial empty runs
        response = client.get("/api/runs")
        assert response.status_code == 200
        assert response.json() == []

        # Save a run
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
        post_response = client.post("/api/runs", json=report)
        assert post_response.status_code == 200
        run_id = post_response.json()["id"]
        assert run_id > 0

        # Fetch all runs
        get_response = client.get("/api/runs")
        assert get_response.status_code == 200
        runs = get_response.json()
        assert len(runs) == 1
        assert runs[0]["suite_name"] == "basic_suite"

        # Fetch specific run
        get_single = client.get(f"/api/runs/{run_id}")
        assert get_single.status_code == 200
        assert get_single.json()["id"] == run_id

        # Fetch nonexistent run
        get_nonexistent = client.get("/api/runs/9999")
        assert get_nonexistent.status_code == 404

    def test_compare_endpoints(self, client: TestClient) -> None:
        # Save run A
        report_a = {
            "suite_name": "suite",
            "summary": {"total": 5, "passed": 3, "failed": 2, "pass_rate": 0.6, "avg_score": 0.6},
            "results": [],
        }
        res_a = client.post("/api/runs", json=report_a)
        run_a_id = res_a.json()["id"]

        # Save run B
        report_b = {
            "suite_name": "suite",
            "summary": {"total": 5, "passed": 4, "failed": 1, "pass_rate": 0.8, "avg_score": 0.8},
            "results": [],
        }
        res_b = client.post("/api/runs", json=report_b)
        run_b_id = res_b.json()["id"]

        # Compare
        compare_payload = {"run_a_id": run_a_id, "run_b_id": run_b_id}
        res_compare = client.post("/api/runs/compare", json=compare_payload)
        assert res_compare.status_code == 200
        assert res_compare.json()["pass_rate_delta"] == pytest.approx(0.2)
        assert res_compare.json()["avg_score_delta"] == pytest.approx(0.2)

        # Compare with invalid IDs
        res_invalid = client.post("/api/runs/compare", json={"run_a_id": 9999, "run_b_id": run_b_id})
        assert res_invalid.status_code == 404

    def test_baselines_endpoints(self, client: TestClient) -> None:
        # Get nonexistent baseline
        get_res = client.get("/api/baselines/suite_x")
        assert get_res.status_code == 404

        # Set baseline
        report = {"suite_name": "suite_x", "summary": {"total": 10}}
        set_res = client.post("/api/baselines/suite_x", json=report)
        assert set_res.status_code == 200
        assert set_res.json() == {"status": "saved"}

        # Get baseline
        get_res_ok = client.get("/api/baselines/suite_x")
        assert get_res_ok.status_code == 200
        assert get_res_ok.json()["suite_name"] == "suite_x"
