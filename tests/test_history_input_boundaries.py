"""Malformed report imports cannot poison the local history read surface."""

import json

import pytest
from fastapi.testclient import TestClient

from evalforge.server.app import create_app
from evalforge.storage.history import HistoryStore


@pytest.mark.parametrize(
    "changes",
    [
        {"results": [None]},
        {"results": {}},
        {"metadata": []},
        {"summary": None},
        {"results": [{"judge_details": None}]},
        {"results": [{"backend_metadata": []}]},
        {"results": [{"backend_metadata": {"retrieved_sources": "bad"}}]},
        {"metadata": {"provenance": []}},
        {"results": [{"test_case_id": {"bad": "id"}}]},
        {"results": [{"test_case_id": ["bad-id"]}]},
        {"suite_name": []},
        {"suite_name": None},
        {"backend": {"provider": "saved"}},
        {"metadata": {"backend": ["saved"]}},
        {"summary": {"total": []}},
        {"summary": {"total_tests": {}}},
        {"summary": {"passed": None}},
        {"summary": {"failed": "one"}},
    ],
)
def test_invalid_legacy_import_does_not_create_history(tmp_path, changes):
    with TestClient(
        create_app(str(tmp_path / "history.db")), raise_server_exceptions=False
    ) as client:
        response = client.post("/api/runs", json={"suite_name": "bad", **changes})
        assert response.status_code in {400, 422}
        assert client.get("/api/runs").json() == []


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"backend": None},
        {"summary": {"total_tests": 1}, "results": [{"test_case_id": 17}]},
    ],
)
def test_omitted_storage_defaults_and_valid_legacy_integer_ids_are_preserved(
    tmp_path, payload
):
    with TestClient(create_app(str(tmp_path / "history.db"))) as client:
        response = client.post("/api/runs", json=payload)
        assert response.status_code == 200
        row = client.get(f"/api/runs/{response.json()['id']}").json()
        assert json.loads(row["report_json"]) == payload
        assert row["suite_name"] == "unknown"


def test_preexisting_invalid_identity_is_not_a_comparable_contract(tmp_path):
    path = str(tmp_path / "history.db")
    report = {
        "suite_name": "bad-id",
        "metadata": {"dataset_revision": "1", "suite_contract": "1"},
        "results": [{"test_case_id": {"bad": "id"}}],
    }
    run_id = HistoryStore(path).save_run(report)
    with TestClient(create_app(path), raise_server_exceptions=False) as client:
        response = client.post(
            "/api/runs/compare", json={"run_a_id": run_id, "run_b_id": run_id}
        )
        assert response.status_code == 200
        assert response.json()["comparable"] is False
        row = client.get(f"/api/runs/{run_id}").json()
        assert json.loads(row["report_json"]) == report
        assert row["cases"][0]["outcome"] == "error"


def test_preexisting_invalid_row_preserves_raw_json_and_other_runs(tmp_path):
    path = str(tmp_path / "history.db")
    history = HistoryStore(path)
    valid = history.save_run({"suite_name": "valid", "results": []})
    malformed = {"suite_name": "bad", "results": [None]}
    bad = history.save_run(malformed)
    with TestClient(create_app(path), raise_server_exceptions=False) as client:
        response = client.get("/api/runs")
        assert response.status_code == 200
        rows = {row["id"]: row for row in response.json()}
        assert set(rows) == {valid, bad}
        assert json.loads(rows[bad]["report_json"]) == malformed
        assert rows[bad]["gate"] is None
        assert rows[bad]["provenance"]["origin"] == "unknown"
        assert rows[bad]["cases"][0]["outcome"] == "error"
        assert client.get(f"/api/runs/{valid}").status_code == 200
        comparison = client.post(
            "/api/runs/compare", json={"run_a_id": valid, "run_b_id": bad}
        )
        assert comparison.status_code == 200
        assert comparison.json()["comparable"] is False
