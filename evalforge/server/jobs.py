"""Single local saved-evaluation executor; SQLite owns cross-request exclusion."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from evalforge.storage.jobs import JobStore


class EvaluationExecutor:
    """Run finite offline evaluations off the HTTP event loop and join on shutdown."""

    def __init__(self, jobs: JobStore) -> None:
        self.jobs = jobs
        self.pool = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="evalforge-local"
        )

    def submit(self, job_id: str, profile: dict[str, Any]) -> None:
        self.pool.submit(self._run, job_id, profile)

    def _run(self, job_id: str, profile: dict[str, Any]) -> None:
        if not self.jobs.start(job_id):
            return
        try:
            from evalforge.evaluation import evaluate_saved

            outcome = evaluate_saved(
                profile["suite_path"],
                profile["response_path"],
                strict=True,
                progress=lambda done, total: self.jobs.progress(job_id, done, total),
            )
            self.jobs.finish(
                job_id, outcome.report.model_dump(mode="json"), outcome.exit_code
            )
        except Exception as exc:
            # No host paths, credentials or uploaded response text in the public error.
            self.jobs.fail(
                job_id,
                f"Local evaluation failed ({type(exc).__name__}); "
                "review inputs and retry",
            )

    def close(self) -> None:
        self.pool.shutdown(wait=True, cancel_futures=False)
