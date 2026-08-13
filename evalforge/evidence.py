"""Reproducible, inspectable evidence bundles for evaluation runs."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Mapping

from pydantic import BaseModel, Field, ValidationError

from evalforge import __version__
from evalforge.models.report import Report

EVIDENCE_SCHEMA_VERSION = 1
_SECRET_PARTS = {
    "authorization",
    "cookie",
    "key",
    "password",
    "secret",
    "token",
    "webhook",
}
_RUNTIME_KEYS = {
    "completed_at",
    "duration_ms",
    "duration_seconds",
    "execution_time_ms",
    "generated_at",
    "latency_ms",
    "report_path",
    "started_at",
    "suite_path",
    "timestamp",
}


class EvidenceVerificationError(ValueError):
    """Raised when an evidence bundle is missing, malformed, or tampered with."""


class EvidenceManifest(BaseModel):
    """Machine-readable provenance and integrity metadata for one run."""

    schema_version: int = EVIDENCE_SCHEMA_VERSION
    suite_name: str
    suite_hash: str
    report_hash: str
    result_hash: str | None = None
    reproducibility_hash: str
    evalforge_version: str = __version__
    git_sha: str | None = None
    backend: str
    mode: str = "sim"
    model: str | None = None
    seed: int | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    baseline_hash: str | None = None
    drift: dict[str, Any] | None = None
    decision: Literal["passed", "failed", "regression"] = "passed"
    regression_decision: Literal["passed", "failed", "regression"] | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    files: dict[str, str] = Field(default_factory=dict)


def _key_parts(key: str) -> set[str]:
    return {part for part in re.split(r"[^a-z0-9]+", key.lower()) if part}


def _is_secret_key(key: str) -> bool:
    parts = _key_parts(key)
    compact = re.sub(r"[^a-z0-9]", "", key.lower())
    compact_patterns = {
        "apikey",
        "accesstoken",
        "authtoken",
        "clientsecret",
        "privatekey",
        "webhookurl",
    }
    return bool(parts & _SECRET_PARTS) or compact in compact_patterns


def redact_secrets(value: Any) -> Any:
    """Return a recursively redacted copy of configuration or metadata."""
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if _is_secret_key(str(key)) else redact_secrets(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_secrets(item) for item in value)
    return value


def _canonicalize(value: Any, *, strip_runtime: bool = False) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            key_str = str(key)
            if strip_runtime and key_str.lower() in _RUNTIME_KEYS:
                continue
            result[key_str] = _canonicalize(item, strip_runtime=strip_runtime)
        return result
    if isinstance(value, list):
        return [_canonicalize(item, strip_runtime=strip_runtime) for item in value]
    if isinstance(value, tuple):
        return [_canonicalize(item, strip_runtime=strip_runtime) for item in value]
    return value


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize a value deterministically for hashing."""
    return json.dumps(
        _canonicalize(value),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        default=str,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    """Return a lowercase SHA-256 digest for bytes."""
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    """Return a lowercase SHA-256 digest for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_report_payload(report: Report) -> dict[str, Any]:
    """Return report data with runtime-only noise removed."""
    payload = report.model_dump(mode="json")
    return _canonicalize(payload, strip_runtime=True)


def reproducibility_hash(report: Report) -> str:
    """Hash score/decision content while ignoring runtime-only fields."""
    return sha256_bytes(canonical_json_bytes(canonical_report_payload(report)))


def resolve_git_sha(path: Path | None = None) -> str | None:
    """Resolve the containing repository's current commit when available."""
    cwd = path if path is not None else Path.cwd()
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            check=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    sha = completed.stdout.strip()
    return sha or None


def _render_markdown(report: Report) -> str:
    lines = [
        f"# Evaluation Report: {report.suite_name}",
        "",
        f"**Generated**: {report.timestamp.isoformat()}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total | {report.summary.total} |",
        f"| Passed | {report.summary.passed} |",
        f"| Failed | {report.summary.failed} |",
        f"| Skipped | {report.summary.skipped} |",
        f"| Pass Rate | {report.summary.pass_rate:.1%} |",
        f"| Avg Score | {report.summary.avg_score:.2f} |",
        "",
        "## Results",
        "",
        "| ID | Name | Status | Score | Time (ms) |",
        "|----|------|--------|-------|-----------|",
    ]
    for result in report.results:
        lines.append(
            f"| {result.test_case_id} | {result.test_case_name} | "
            f"{'PASS' if result.passed else 'FAIL'} | {result.score:.2f} | "
            f"{result.execution_time_ms:.0f} |"
        )
    return "\n".join(lines) + "\n"


def _write_checksums(output_dir: Path, files: dict[str, str]) -> None:
    contents = "".join(f"{digest}  {name}\n" for name, digest in sorted(files.items()))
    (output_dir / "checksums.sha256").write_text(contents, encoding="utf-8")


def build_evidence_bundle(
    *,
    output_dir: Path,
    report: Report,
    suite_path: Path,
    backend: str,
    mode: str = "sim",
    model: str | None = None,
    seed: int | None = None,
    config: Mapping[str, Any] | None = None,
    baseline_path: Path | None = None,
    drift: Any | None = None,
    git_sha: str | None = None,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
) -> EvidenceManifest:
    """Write a canonical evidence bundle and return its manifest."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename in (
        "manifest.json",
        "report.json",
        "report.md",
        "drift.json",
        "checksums.sha256",
    ):
        stale_file = output_dir / filename
        if stale_file.is_file():
            stale_file.unlink()
    report_path = output_dir / "report.json"
    report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    (output_dir / "report.md").write_text(_render_markdown(report), encoding="utf-8")

    drift_data: dict[str, Any] | None = None
    if drift is not None:
        drift_data = (
            drift.model_dump(mode="json")
            if isinstance(drift, BaseModel)
            else dict(drift)
        )
        (output_dir / "drift.json").write_text(
            json.dumps(drift_data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    payload_files = {
        name: sha256_file(output_dir / name)
        for name in ("report.json", "report.md", "drift.json")
        if (output_dir / name).exists()
    }
    report_failed = report.summary.failed > 0
    decision: Literal["passed", "failed", "regression"] = (
        "regression"
        if drift_data and drift_data.get("is_regression")
        else "failed"
        if report_failed
        else "passed"
    )
    manifest = EvidenceManifest(
        suite_name=report.suite_name,
        suite_hash=sha256_file(suite_path),
        report_hash=payload_files["report.json"],
        result_hash=payload_files["report.json"],
        reproducibility_hash=reproducibility_hash(report),
        git_sha=git_sha if git_sha is not None else resolve_git_sha(suite_path.parent),
        backend=backend,
        mode=mode,
        model=model,
        seed=seed,
        config=redact_secrets(dict(config or {})),
        baseline_hash=sha256_file(baseline_path) if baseline_path else None,
        drift=drift_data,
        decision=decision,
        regression_decision=decision,
        started_at=started_at or datetime.now(timezone.utc),
        completed_at=completed_at or datetime.now(timezone.utc),
        files=payload_files,
    )
    (output_dir / "manifest.json").write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )
    _write_checksums(output_dir, payload_files)
    return manifest


def _safe_file_path(directory: Path, name: str) -> Path:
    path = Path(name)
    if path.is_absolute() or path.name != name or ".." in path.parts:
        raise EvidenceVerificationError(f"Unsafe evidence file name: {name}")
    return directory / path


def verify_evidence_bundle(directory: Path) -> EvidenceManifest:  # noqa: C901
    """Verify bundle structure, checksums, report schema, and reproducibility hash."""
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        raise EvidenceVerificationError("manifest.json is missing")
    try:
        manifest = EvidenceManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
    except (OSError, ValueError, ValidationError) as exc:
        raise EvidenceVerificationError(f"Invalid manifest: {exc}") from exc

    checksums_path = directory / "checksums.sha256"
    if not checksums_path.is_file():
        raise EvidenceVerificationError("checksums.sha256 is missing")
    checksum_lines: dict[str, str] = {}
    for line in checksums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            digest, name = line.split("  ", 1)
        except ValueError as exc:
            raise EvidenceVerificationError("Malformed checksum entry") from exc
        checksum_lines[name] = digest

    if checksum_lines != manifest.files:
        raise EvidenceVerificationError(
            "Checksum manifest does not match manifest.json"
        )
    for name, expected_digest in manifest.files.items():
        path = _safe_file_path(directory, name)
        if not path.is_file():
            raise EvidenceVerificationError(f"Evidence file is missing: {name}")
        actual_digest = sha256_file(path)
        if actual_digest != expected_digest:
            raise EvidenceVerificationError(f"Checksum mismatch for {name}")

    report_path = _safe_file_path(directory, "report.json")
    if manifest.report_hash != sha256_file(report_path):
        raise EvidenceVerificationError("Report hash does not match manifest.json")
    if manifest.result_hash and manifest.result_hash != sha256_file(report_path):
        raise EvidenceVerificationError("Result hash does not match manifest.json")
    try:
        report = Report.model_validate_json(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, ValidationError) as exc:
        raise EvidenceVerificationError(f"Invalid report.json: {exc}") from exc
    if reproducibility_hash(report) != manifest.reproducibility_hash:
        raise EvidenceVerificationError(
            "Reproducibility hash does not match manifest.json"
        )
    return manifest
