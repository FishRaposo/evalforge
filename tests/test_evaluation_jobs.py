"""Durable job behavior: atomic claims, persistence, and once-only report writes."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from uuid import uuid4

import pytest

from evalforge.storage.history import HistoryStore


def stores(tmp_path: Path):
    from evalforge.storage.jobs import JobStore

    path = str(tmp_path / "jobs.db")
    history = HistoryStore(path)
    return JobStore(path), history, path


def test_claim_deduplicates_request_before_global_busy_check(tmp_path):
    jobs, _, _ = stores(tmp_path)
    request = str(uuid4())
    first, created = jobs.claim("baseline", request, 6)
    assert created and first["status"] == "queued"
    repeat, created = jobs.claim("baseline", request, 6)
    assert not created and repeat["id"] == first["id"]
    from evalforge.storage.jobs import ActiveJobError, RequestConflictError

    with pytest.raises(RequestConflictError):
        jobs.claim("candidate", request, 6)
    with pytest.raises(ActiveJobError) as error:
        jobs.claim("candidate", str(uuid4()), 6)
    assert error.value.active_job_id == first["id"]


def test_separate_connections_claim_exactly_one_active_job(tmp_path):
    jobs, _, path = stores(tmp_path)
    from evalforge.storage.jobs import ActiveJobError, JobStore

    def launch(_):
        try:
            return JobStore(path).claim("baseline", str(uuid4()), 6)[0]["id"]
        except ActiveJobError:
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(launch, range(8)))
    assert sum(value is not None for value in results) == 1


def test_finish_race_inserts_one_history_row_and_preserves_gate(tmp_path):
    jobs, history, path = stores(tmp_path)
    job, _ = jobs.claim("baseline", str(uuid4()), 2)
    assert jobs.start(job["id"])
    jobs.progress(job["id"], 1, 2)
    report = {
        "suite_name": "fixture",
        "summary": {"total": 2},
        "metadata": {"gate": {"status": "cannot_evaluate", "exit_code": 2}},
    }
    from evalforge.storage.jobs import JobStore

    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(
            pool.map(lambda _: JobStore(path).finish(job["id"], report, 2), range(2))
        )
    assert ids[0] == ids[1] and ids[0] > 0
    assert len(history.get_runs()) == 1
    saved = jobs.get(job["id"])
    assert saved["status"] == "completed"
    assert saved["completed_cases"] == 2
    assert saved["gate"] == {"status": "cannot_evaluate", "exit_code": 2}
    assert saved["exit_code"] == 2


def test_failed_atomic_finish_rolls_back_and_can_retry(tmp_path):
    jobs, history, _ = stores(tmp_path)
    job, _ = jobs.claim("baseline", str(uuid4()), 1)
    jobs.start(job["id"])
    with pytest.raises(TypeError):
        jobs.finish(job["id"], {"suite_name": "bad", "not_json": object()}, 0)
    assert history.get_runs() == []
    assert jobs.get(job["id"])["status"] == "running"
    run_id = jobs.finish(job["id"], {"suite_name": "good", "summary": {"total": 1}}, 0)
    assert history.get_run(run_id)["suite_name"] == "good"


def test_restart_interrupts_pending_without_running_or_saving(tmp_path):
    jobs, history, path = stores(tmp_path)
    job, _ = jobs.claim("baseline", str(uuid4()), 6)
    jobs.start(job["id"])
    jobs.progress(job["id"], 3, 6)
    from evalforge.storage.jobs import JobStore

    restarted = JobStore(path)
    assert restarted.interrupt_pending() == 1
    saved = restarted.get(job["id"])
    assert saved["status"] == "interrupted" and saved["completed_cases"] == 3
    assert saved["run_id"] is None and history.get_runs() == []
    assert restarted.finish(job["id"], {"suite_name": "late"}, 0) is None
    new, _ = restarted.claim("baseline", str(uuid4()), 6)
    assert new["id"] != job["id"]


def test_progress_monotonic_and_failure_is_terminal(tmp_path):
    jobs, history, _ = stores(tmp_path)
    job, _ = jobs.claim("baseline", str(uuid4()), 6)
    assert jobs.start(job["id"])
    assert not jobs.start(job["id"])
    jobs.progress(job["id"], 4, 6)
    jobs.progress(job["id"], 1, 6)
    jobs.progress(job["id"], 99, 6)
    assert jobs.get(job["id"])["completed_cases"] == 4
    jobs.fail(job["id"], "Local evaluation failed")
    assert jobs.get(job["id"])["status"] == "failed"
    assert jobs.finish(job["id"], {"suite_name": "late"}, 0) is None
    assert jobs.get("missing") is None and history.get_runs() == []


def test_report_insert_rolls_back_when_terminal_job_update_is_rejected(tmp_path):
    import sqlite3

    jobs, history, path = stores(tmp_path)
    job, _ = jobs.claim("baseline", str(uuid4()), 1)
    jobs.start(job["id"])
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute("""CREATE TRIGGER reject_completion
            BEFORE UPDATE ON evaluation_jobs WHEN NEW.status='completed'
            BEGIN SELECT RAISE(ABORT, 'injected storage failure'); END""")
    with pytest.raises(sqlite3.IntegrityError, match="injected storage failure"):
        jobs.finish(job["id"], {"suite_name": "atomic", "summary": {"total": 1}}, 0)
    assert history.get_runs() == []
    assert jobs.get(job["id"])["status"] == "running"
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute("DROP TRIGGER reject_completion")
    saved = jobs.finish(job["id"], {"suite_name": "atomic", "summary": {"total": 1}}, 0)
    assert saved > 0 and len(history.get_runs()) == 1
