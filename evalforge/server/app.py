"""FastAPI app for EvalForge history and comparison API."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from uuid import UUID

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.datastructures import UploadFile

from evalforge.server.boundaries import LocalMutationBoundary
from evalforge.server.jobs import EvaluationExecutor
from evalforge.server.locking import database_service_lock
from evalforge.server.profiles import RESPONSE_LIMIT, SUITE_LIMIT, ProfileManager
from evalforge.server.views import compare_view, run_view
from evalforge.shared_core.errors import BaseApplicationError, application_error_handler
from evalforge.shared_core.logging import RequestLoggingMiddleware
from evalforge.storage.history import HistoryStore
from evalforge.storage.jobs import ActiveJobError, JobStore, RequestConflictError


class RunIn(BaseModel):
    """Request model for saving a run."""

    suite_name: str
    backend: str | None = None
    summary: dict[str, Any] = {}
    results: list[dict[str, Any]] = []


class EvaluationIn(BaseModel):
    """One explicit browser/CLI launch with an idempotency UUID."""

    profile_id: str
    request_id: UUID


class CompareIn(BaseModel):
    """Request model for comparing two runs."""

    run_a_id: int
    run_b_id: int


async def _application_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Adapt the vendored typed handler to FastAPI's broad handler protocol."""

    if isinstance(exc, BaseApplicationError):
        return await application_error_handler(request, exc)
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_SERVER_ERROR", "message": "Internal server error"},
    )


def create_app(  # noqa: C901
    db_path: str = "evalforge_history.db",
    *,
    upload_dir: str | Path | None = None,
    allowed_origins: list[str] | None = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        db_path: Path to the SQLite history database.

    Returns:
        Configured FastAPI app.
    """
    store = HistoryStore(db_path)
    jobs = JobStore(db_path)
    root = Path(
        upload_dir
        or os.environ.get("EVALFORGE_UPLOAD_DIR")
        or Path(db_path).parent / "evalforge_uploads"
    )
    profiles = ProfileManager(db_path, root)
    executor = EvaluationExecutor(jobs)
    origins = (
        allowed_origins
        if allowed_origins is not None
        else [
            item.strip()
            for item in os.environ.get(
                "EVALFORGE_ALLOWED_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000",
            ).split(",")
            if item.strip()
        ]
    )
    if any(origin == "*" for origin in origins):
        raise ValueError("Configure explicit browser origins; wildcard is unsupported")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        with database_service_lock(db_path):
            jobs.interrupt_pending()
            try:
                yield
            finally:
                executor.close()

    app = FastAPI(title="EvalForge API", version="0.1.0", lifespan=lifespan)
    app.state.job_store = jobs
    app.state.profile_manager = profiles
    app.add_middleware(LocalMutationBoundary, allowed_origins=origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    app.add_exception_handler(BaseApplicationError, _application_error_handler)
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/evaluation-profiles")
    def list_profiles() -> dict[str, Any]:
        return {"profiles": profiles.list()}

    @app.post("/api/evaluation-profiles", status_code=201)
    async def upload_profile(request: Request) -> dict[str, Any]:
        try:
            async with request.form(max_files=2, max_fields=0) as form:
                if set(form) != {"suite", "responses"} or len(form.multi_items()) != 2:
                    raise HTTPException(400, "Supply exactly suite and responses files")
                suite, responses = form["suite"], form["responses"]
                if not isinstance(suite, UploadFile) or not isinstance(
                    responses, UploadFile
                ):
                    raise HTTPException(400, "Both fields must be uploaded files")
                if (
                    Path(suite.filename or "").suffix.lower() not in {".yaml", ".yml"}
                    or Path(responses.filename or "").suffix.lower() != ".jsonl"
                ):
                    raise HTTPException(
                        400, "Upload a .yaml/.yml suite and .jsonl saved responses"
                    )
                suite_raw = await suite.read(SUITE_LIMIT + 1)
                response_raw = await responses.read(RESPONSE_LIMIT + 1)
                if len(suite_raw) > SUITE_LIMIT or len(response_raw) > RESPONSE_LIMIT:
                    raise HTTPException(
                        413, "Suite limit is 2 MiB; saved responses limit is 10 MiB"
                    )
                return profiles.upload(suite_raw, response_raw)
        except (ValueError, OSError, yaml.YAMLError) as exc:
            raise HTTPException(
                400,
                "Invalid saved inputs; check UTF-8, schema, case IDs and evidence",
            ) from exc

    @app.post("/api/evaluations")
    def launch_evaluation(body: EvaluationIn) -> JSONResponse:
        try:
            previous = jobs.get_by_request(str(body.request_id))
            if previous is not None:
                if previous["profile_id"] != body.profile_id:
                    raise RequestConflictError(
                        "Request UUID belongs to another profile"
                    )
                return JSONResponse(previous, status_code=200)
            profile = profiles.get(body.profile_id)
            if profile is None:
                raise HTTPException(404, "Evaluation profile not found")
            info = profiles.validate(profile)
            job, created = jobs.claim(
                body.profile_id, str(body.request_id), info["case_count"]
            )
        except ActiveJobError as exc:
            raise HTTPException(
                409, {"message": str(exc), "active_job_id": exc.active_job_id}
            ) from exc
        except RequestConflictError as exc:
            raise HTTPException(409, str(exc)) from exc
        except (ValueError, OSError, yaml.YAMLError) as exc:
            raise HTTPException(
                400,
                "Profile inputs are invalid or changed; upload a new validated profile",
            ) from exc
        if created:
            try:
                executor.submit(job["id"], profile)
            except RuntimeError:
                jobs.fail(
                    job["id"],
                    "Local executor is stopping; launch a new request after restart",
                )
                raise HTTPException(503, "Local executor is stopping") from None
        return JSONResponse(job, status_code=202 if created else 200)

    @app.get("/api/evaluations/{job_id}")
    def get_evaluation(job_id: str) -> dict[str, Any]:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(404, "Evaluation job not found")
        return job

    @app.get("/api/runs")
    def list_runs(
        suite_name: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """List recent evaluation runs."""
        return [
            run_view(row) for row in store.get_runs(suite_name=suite_name, limit=limit)
        ]

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: int) -> dict[str, Any]:
        """Get a single run by ID."""
        run = store.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return run_view(run)

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

        return compare_view(a, b)

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
