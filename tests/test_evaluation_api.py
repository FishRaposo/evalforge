"""HTTP contracts preserve legacy reports while adding evidence and durable launches."""

import json
import time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from evalforge.server.app import create_app


def report(case_id="case-a", passed=True, revision="revision-1", contract="contract-1"):
    return {
        "suite_name": "evidence",
        "summary": {
            "total": 1,
            "passed": int(passed),
            "failed": int(not passed),
            "pass_rate": float(passed),
            "avg_score": float(passed),
        },
        "metadata": {
            "dataset_revision": revision,
            "suite_contract": contract,
            "origin": "synthetic",
            "gate": {"status": "passed" if passed else "failed"},
            "provenance": {"origin": "synthetic"},
        },
        "results": [
            {
                "test_case_id": case_id,
                "test_case_name": "Source check",
                "passed": passed,
                "score": float(passed),
                "outcome": "passed" if passed else "failed",
                "actual_response": "The plan lasts 30 days.",
                "judge_details": {"method": "source_contract"},
                "backend_metadata": {
                    "input": "How long?",
                    "expected": {"claim": "30 days"},
                    "category": "answerable",
                    "retrieved_sources": [{"id": "source", "version": "1"}],
                    "citations": [
                        {
                            "source_id": "source",
                            "source_version": "1",
                            "quote": "30 days",
                        }
                    ],
                    "authoritative_sources": [
                        {"id": "source", "version": "1", "content": "30 days"}
                    ],
                    "provenance": {"origin": "synthetic"},
                },
            }
        ],
    }


def test_history_http_keeps_raw_keys_and_exposes_case_evidence(tmp_path):
    with TestClient(create_app(str(tmp_path / "api.db"))) as client:
        original = report()
        run_id = client.post("/api/runs", json=original).json()["id"]
        row = client.get(f"/api/runs/{run_id}").json()
        assert json.loads(row["report_json"]) == original
        assert row["total_tests"] == 1 and row["gate"]["status"] == "passed"
        case = row["cases"][0]
        assert case["id"] == "case-a" and case["input"] == "How long?"
        assert case["expected"] == {"claim": "30 days"}
        assert case["retrieved_sources"] == [{"id": "source", "version": "1"}]
        assert case["citations"][0]["quote"] == "30 days"
        assert case["authoritative_sources"][0]["content"] == "30 days"
        assert case["judges"][0]["details"] == {"method": "source_contract"}
        assert client.get("/api/runs").json()[0]["cases"] == row["cases"]


def test_legacy_history_marks_missing_evidence_unknown(tmp_path):
    with TestClient(create_app(str(tmp_path / "api.db"))) as client:
        run_id = client.post(
            "/api/runs",
            json={
                "suite_name": "old",
                "results": [{"test_case_id": "legacy", "passed": False, "score": 0.0}],
            },
        ).json()["id"]
        row = client.get(f"/api/runs/{run_id}").json()
        assert row["gate"] is None and row["provenance"]["origin"] == "unknown"
        case = row["cases"][0]
        assert case["input"] is None and case["retrieved_sources"] == []
        assert case["provenance"]["origin"] == "unknown"
        assert case["judges"][0]["judge"] == "unknown"


def test_comparison_aligns_case_ids_and_requires_matching_contract(tmp_path):
    with TestClient(create_app(str(tmp_path / "api.db"))) as client:
        baseline = report()
        candidate = report(passed=False)
        candidate["results"].append({"test_case_id": "new", "passed": True, "score": 1})
        a = client.post("/api/runs", json=baseline).json()["id"]
        b = client.post("/api/runs", json=candidate).json()["id"]
        comparison = client.post(
            "/api/runs/compare", json={"run_a_id": a, "run_b_id": b}
        ).json()
        assert comparison["comparable"] is True
        assert [
            (row["case_id"], row["change"]) for row in comparison["case_deltas"]
        ] == [("case-a", "regressed"), ("new", "added")]
        assert comparison["pass_rate_delta"] == -1.0
        other = report(revision="different")
        c = client.post("/api/runs", json=other).json()["id"]
        mismatch = client.post(
            "/api/runs/compare", json={"run_a_id": a, "run_b_id": c}
        ).json()
        assert mismatch["comparable"] is False and mismatch["reason"]


SUITE = b"""name: Local upload
backend: saved
test_cases:
  - id: local-one
    name: Exact contract
    type: evidence_support
    input: Say Paris
    expected:
      sources:
        - {id: atlas, version: '1', content: 'Paris is the capital.'}
      answer_contract:
        kind: answer
        exhaustive: true
        accepted_answers: [Paris]
        claims:
          - {text: Paris, source_id: atlas, source_version: '1', quote: Paris}
"""
RESPONSES = (
    json.dumps(
        {
            "schema_version": 1,
            "case_id": "local-one",
            "answer": "Paris",
            "retrieved_sources": [
                {"id": "atlas", "version": "1", "content": "Paris is the capital."}
            ],
            "citations": [
                {
                    "source_id": "atlas",
                    "source_version": "1",
                    "claim": "Paris",
                    "quote": "Paris",
                }
            ],
            "provenance": {
                "origin": "recorded",
                "dataset_revision": "upload-fixture-1",
                "label_origin": "test fixture",
            },
        }
    )
    + "\n"
).encode()


def upload(client, suite=SUITE, responses=RESPONSES, name="suite.yaml"):
    return client.post(
        "/api/evaluation-profiles",
        files={
            "suite": (name, suite, "application/yaml"),
            "responses": ("responses.jsonl", responses, "application/json"),
        },
    )


def terminal(client, job_id):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        job = client.get(f"/api/evaluations/{job_id}").json()
        if job["status"] not in {"queued", "running"}:
            return job
        time.sleep(0.01)
    pytest.fail("Local evaluation did not finish within 10 seconds")


def test_upload_registers_validated_files_and_actual_job_saves_report_once(tmp_path):
    db = str(tmp_path / "api.db")
    root = tmp_path / "uploads"
    with TestClient(create_app(db, upload_dir=root)) as client:
        response = upload(client, name="../../outside.yaml")
        assert response.status_code == 201
        profile = response.json()
        assert profile["uploaded"] is True and profile["case_count"] == 1
        assert profile["origin"] == "recorded"
        assert "suite_path" not in profile and str(tmp_path) not in response.text
        request = {"profile_id": profile["id"], "request_id": str(uuid4())}
        launch = client.post("/api/evaluations", json=request)
        assert launch.status_code == 202
        job = terminal(client, launch.json()["id"])
        assert job["status"] == "completed" and job["exit_code"] == 0
        assert job["completed_cases"] == job["total_cases"] == 1
        row = client.get(f"/api/runs/{job['run_id']}").json()
        assert row["cases"][0]["actual"] == "Paris"
        assert row["gate"]["status"] == "passed"
        duplicate = client.post("/api/evaluations", json=request)
        assert duplicate.status_code == 200 and duplicate.json()["id"] == job["id"]
        assert len(client.get("/api/runs").json()) == 1
    assert not (tmp_path / "outside.yaml").exists()
    assert all(
        path.resolve().is_relative_to(root.resolve()) for path in root.rglob("*")
    )
    with TestClient(create_app(db, upload_dir=root)) as restarted:
        assert profile["id"] in [
            p["id"]
            for p in restarted.get("/api/evaluation-profiles").json()["profiles"]
        ]
        assert (
            restarted.get(f"/api/evaluations/{job['id']}").json()["run_id"]
            == job["run_id"]
        )


@pytest.mark.parametrize(
    "suite,responses",
    [
        (b"includes: ['../../outside.yaml']\n" + SUITE, RESPONSES),
        (b"!!python/object/apply:os.system ['whoami']", RESPONSES),
        (SUITE.replace(b"backend: saved", b"backend: openai"), RESPONSES),
        (SUITE, RESPONSES.replace(b"local-one", b"wrong-case")),
        (SUITE, b"not json"),
        (b"\xff", RESPONSES),
        (b"name: root\nplugins: ['evil.module']\ntest_cases: []", RESPONSES),
    ],
)
def test_upload_rejects_unsafe_or_unmapped_inputs_without_registration(
    tmp_path, suite, responses
):
    root = tmp_path / "uploads"
    with TestClient(create_app(str(tmp_path / "api.db"), upload_dir=root)) as client:
        response = upload(client, suite, responses)
        assert response.status_code in {400, 422}
        assert not [
            p
            for p in client.get("/api/evaluation-profiles").json()["profiles"]
            if p["uploaded"]
        ]
        assert client.get("/api/runs").json() == []
    assert not list(root.rglob("*.yaml"))


@pytest.mark.parametrize(
    "field,size", [("suite", 2 * 1024 * 1024 + 1), ("responses", 10 * 1024 * 1024 + 1)]
)
def test_upload_enforces_each_file_byte_cap(tmp_path, field, size):
    with TestClient(
        create_app(str(tmp_path / "api.db"), upload_dir=tmp_path / "uploads")
    ) as client:
        response = upload(
            client,
            suite=b"x" * size if field == "suite" else SUITE,
            responses=b"x" * size if field == "responses" else RESPONSES,
        )
        assert response.status_code == 413
        assert client.get("/api/runs").json() == []


def test_origin_and_cors_allow_only_explicit_local_browser_configuration(tmp_path):
    with TestClient(
        create_app(
            str(tmp_path / "api.db"),
            upload_dir=tmp_path / "uploads",
            allowed_origins=["http://localhost:3303"],
        )
    ) as client:
        denied = client.post(
            "/api/evaluations",
            json={"profile_id": "baseline", "request_id": str(uuid4())},
            headers={"Origin": "https://attacker.example"},
        )
        assert denied.status_code == 403
        preflight = client.options(
            "/api/evaluations",
            headers={
                "Origin": "http://localhost:3303",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert (
            preflight.headers["access-control-allow-origin"] == "http://localhost:3303"
        )
        assert client.get("/api/evaluation-profiles").status_code == 200
        assert upload(client).status_code == 201


def test_unknown_or_invalid_launch_creates_no_jobs_and_checks_profile_integrity(
    tmp_path,
):
    root = tmp_path / "uploads"
    with TestClient(create_app(str(tmp_path / "api.db"), upload_dir=root)) as client:
        assert (
            client.post(
                "/api/evaluations",
                json={"profile_id": "missing", "request_id": str(uuid4())},
            ).status_code
            == 404
        )
        assert (
            client.post(
                "/api/evaluations", json={"profile_id": "baseline", "request_id": "bad"}
            ).status_code
            == 422
        )
        assert client.get("/api/evaluations/missing").status_code == 404
        profile = upload(client).json()
        next(root.rglob("suite.yaml")).write_text("name: changed\ntest_cases: []")
        response = client.post(
            "/api/evaluations",
            json={"profile_id": profile["id"], "request_id": str(uuid4())},
        )
        assert response.status_code == 400
        assert client.get("/api/runs").json() == []


@pytest.mark.parametrize(
    "suite",
    [
        SUITE.replace(b"backend: saved", b"backend: {provider: openai}"),
        SUITE.replace(b"backend: saved", b"backend: [saved]"),
        b"metadata: " + b"[" * 2000 + b"0" + b"]" * 2000,
    ],
)
def test_malformed_backend_and_deep_yaml_return_input_error(tmp_path, suite):
    with TestClient(
        create_app(str(tmp_path / "api.db"), upload_dir=tmp_path / "uploads")
    ) as client:
        response = upload(client, suite=suite)
        assert response.status_code == 400
        assert client.get("/api/runs").json() == []


def test_http_contention_dedupes_busy_and_releases_slot_after_real_completion(
    tmp_path, monkeypatch
):
    from threading import Event

    from evalforge import evaluation

    entered, release = Event(), Event()
    actual = evaluation.evaluate_saved

    def blocked(*args, **kwargs):
        entered.set()
        assert release.wait(10), "Test must release local evaluation"
        return actual(*args, **kwargs)

    monkeypatch.setattr(evaluation, "evaluate_saved", blocked)
    with TestClient(
        create_app(str(tmp_path / "api.db"), upload_dir=tmp_path / "uploads")
    ) as client:
        profile = upload(client).json()
        request = {"profile_id": profile["id"], "request_id": str(uuid4())}
        try:
            first = client.post("/api/evaluations", json=request)
            assert first.status_code == 202 and entered.wait(5)
            repeated = client.post("/api/evaluations", json=request)
            assert (
                repeated.status_code == 200
                and repeated.json()["id"] == first.json()["id"]
            )
            busy = client.post(
                "/api/evaluations",
                json={"profile_id": profile["id"], "request_id": str(uuid4())},
            )
            assert busy.status_code == 409
            assert busy.json()["detail"]["active_job_id"] == first.json()["id"]
            conflict = client.post(
                "/api/evaluations",
                json={"profile_id": "candidate", "request_id": request["request_id"]},
            )
            assert conflict.status_code == 409
            assert client.get("/api/runs").json() == []
        finally:
            release.set()
        finished = terminal(client, first.json()["id"])
        assert finished["exit_code"] == 0
        assert len(client.get("/api/runs").json()) == 1
        again = client.post(
            "/api/evaluations",
            json={"profile_id": profile["id"], "request_id": str(uuid4())},
        )
        assert again.status_code == 202
        assert terminal(client, again.json()["id"])["status"] == "completed"
        assert len(client.get("/api/runs").json()) == 2


def test_worker_infrastructure_failure_is_terminal_without_fake_report(
    tmp_path, monkeypatch
):
    from evalforge import evaluation

    def unavailable(*args, **kwargs):
        raise OSError("private C:/host-path/secret response")

    monkeypatch.setattr(evaluation, "evaluate_saved", unavailable)
    with TestClient(
        create_app(str(tmp_path / "api.db"), upload_dir=tmp_path / "uploads")
    ) as client:
        profile = upload(client).json()
        launched = client.post(
            "/api/evaluations",
            json={"profile_id": profile["id"], "request_id": str(uuid4())},
        )
        job = terminal(client, launched.json()["id"])
        assert job["status"] == "failed" and job["run_id"] is None
        assert job["gate"] is None and job["exit_code"] is None
        assert "OSError" in job["error"] and "secret" not in job["error"]
        assert client.get("/api/runs").json() == []


def test_startup_marks_persisted_pending_job_interrupted_without_autorun(tmp_path):
    db = str(tmp_path / "api.db")
    app = create_app(db, upload_dir=tmp_path / "uploads")
    seeded, _ = app.state.job_store.claim("baseline", str(uuid4()), 100)
    with TestClient(app) as client:
        job = client.get(f"/api/evaluations/{seeded['id']}").json()
        assert job["status"] == "interrupted" and job["completed_cases"] == 0
        assert job["run_id"] is None and client.get("/api/runs").json() == []


def test_preset_jobs_execute_actual_corpus_and_keep_gate_separate_from_job_status(
    tmp_path,
):
    with TestClient(
        create_app(str(tmp_path / "api.db"), upload_dir=tmp_path / "uploads")
    ) as client:
        profiles = client.get("/api/evaluation-profiles").json()["profiles"]
        assert {p["id"] for p in profiles} == {
            "baseline",
            "candidate",
            "repaired",
            "indeterminate",
        }
        assert all(
            p["origin"] == "synthetic" and p["case_count"] == 100 for p in profiles
        )
        run_ids = {}
        for profile_id, expected_code, expected_gate in [
            ("baseline", 0, "passed"),
            ("candidate", 1, "failed"),
            ("repaired", 0, "passed"),
            ("indeterminate", 2, "cannot_evaluate"),
        ]:
            launch = client.post(
                "/api/evaluations",
                json={"profile_id": profile_id, "request_id": str(uuid4())},
            )
            assert launch.status_code == 202
            job = terminal(client, launch.json()["id"])
            assert job["status"] == "completed" and job["exit_code"] == expected_code
            assert job["gate"]["status"] == expected_gate
            assert job["gate"]["quality_validated"] is False
            assert job["completed_cases"] == job["total_cases"] == 100
            run_ids[profile_id] = job["run_id"]
        compared = client.post(
            "/api/runs/compare",
            json={"run_a_id": run_ids["baseline"], "run_b_id": run_ids["candidate"]},
        ).json()
        assert compared["comparable"] is True
        assert sum(row["change"] == "regressed" for row in compared["case_deltas"]) == 6


def test_upload_rejects_501_cases_and_yaml_aliases(tmp_path):
    import yaml

    case = yaml.safe_load(SUITE)["test_cases"][0]
    cases = [{**json.loads(json.dumps(case)), "id": f"case-{n}"} for n in range(501)]
    suite = yaml.safe_dump({"name": "too many", "test_cases": cases}).encode()
    # No shared objects/aliases: the case limit, rather than aliases, must reject this.
    with TestClient(
        create_app(str(tmp_path / "api.db"), upload_dir=tmp_path / "uploads")
    ) as client:
        assert upload(client, suite=suite).status_code == 400
        aliased = b"name: alias\ntest_cases: &cases []\nmetadata: {copy: *cases}"
        assert upload(client, suite=aliased).status_code == 400
        assert not [
            p
            for p in client.get("/api/evaluation-profiles").json()["profiles"]
            if p["uploaded"]
        ]


def test_multipart_total_cap_and_invalid_parts_are_rejected_without_parsing(tmp_path):
    with TestClient(
        create_app(str(tmp_path / "api.db"), upload_dir=tmp_path / "uploads")
    ) as client:
        oversized = client.post(
            "/api/evaluation-profiles",
            content=(b"x" * (1024 * 1024) for _ in range(14)),
            headers={"Content-Type": "multipart/form-data; boundary=stream"},
        )
        assert oversized.status_code == 413
        missing = client.post(
            "/api/evaluation-profiles", files={"suite": ("suite.yaml", SUITE)}
        )
        assert missing.status_code == 400
        assert upload(client, name="suite.exe").status_code == 400
        assert client.get("/api/runs").json() == []


def test_second_live_service_cannot_interrupt_active_database_owner(tmp_path):
    db = str(tmp_path / "api.db")
    first = create_app(db, upload_dir=tmp_path / "uploads")
    with TestClient(first) as client:
        queued, _ = first.state.job_store.claim("baseline", str(uuid4()), 100)
        second = create_app(db, upload_dir=tmp_path / "uploads")
        with pytest.raises(RuntimeError, match="already in use"):
            with TestClient(second):
                pass
        assert (
            client.get(f"/api/evaluations/{queued['id']}").json()["status"] == "queued"
        )
    # The process lock is released after shutdown; recovery then becomes safe.
    with TestClient(create_app(db, upload_dir=tmp_path / "uploads")) as restarted:
        assert (
            restarted.get(f"/api/evaluations/{queued['id']}").json()["status"]
            == "interrupted"
        )


@pytest.mark.parametrize(
    "responses",
    [
        b'{"nested":' + b"[" * 2000 + b"0" + b"]" * 2000 + b"}",
        RESPONSES.replace(
            b'"origin": "recorded"', b'"origin": {"provider": "unknown"}'
        ),
        RESPONSES.replace(b'"origin": "recorded"', b'"origin": ["recorded"]'),
    ],
)
def test_malformed_saved_json_is_an_input_error_without_job(tmp_path, responses):
    with TestClient(
        create_app(str(tmp_path / "api.db"), upload_dir=tmp_path / "uploads")
    ) as client:
        assert upload(client, responses=responses).status_code == 400
        assert client.get("/api/runs").json() == []


def test_duplicate_request_returns_original_job_even_if_inputs_later_change(tmp_path):
    root = tmp_path / "uploads"
    with TestClient(create_app(str(tmp_path / "api.db"), upload_dir=root)) as client:
        profile = upload(client).json()
        request = {"profile_id": profile["id"], "request_id": str(uuid4())}
        first = client.post("/api/evaluations", json=request)
        terminal(client, first.json()["id"])
        next(root.rglob("suite.yaml")).write_text("invalid replacement")
        repeated = client.post("/api/evaluations", json=request)
        assert (
            repeated.status_code == 200 and repeated.json()["id"] == first.json()["id"]
        )
        assert len(client.get("/api/runs").json()) == 1


def test_api_shutdown_releases_database_handles_without_garbage_collection(tmp_path):
    import gc

    db = tmp_path / "released.db"
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        with TestClient(create_app(str(db), upload_dir=tmp_path / "uploads")) as client:
            profile = upload(client).json()
            launched = client.post(
                "/api/evaluations",
                json={"profile_id": profile["id"], "request_id": str(uuid4())},
            )
            job = terminal(client, launched.json()["id"])
            assert job["status"] == "completed"
            assert len(client.get("/api/runs").json()) == 1
            assert client.get(f"/api/runs/{job['run_id']}").status_code == 200
            assert (
                client.post(
                    "/api/baselines/fixture", json={"suite_name": "fixture"}
                ).status_code
                == 200
            )
            assert client.get("/api/baselines/fixture").status_code == 200
            assert client.get("/api/evaluation-profiles").status_code == 200
        db.unlink()
        assert not db.exists()
    finally:
        if was_enabled:
            gc.enable()
