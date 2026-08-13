"""Tests for reproducible evaluation evidence bundles."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from evalforge.cli import app
from evalforge.drift import DriftResult
from evalforge.evidence import (
    EvidenceVerificationError,
    build_evidence_bundle,
    redact_secrets,
    reproducibility_hash,
    verify_evidence_bundle,
)
from evalforge.models.report import Report, ReportSummary
from evalforge.models.test_result import TestResult

runner = CliRunner()


def _report(
    *, timestamp: datetime, execution_time_ms: float, suite_path: str
) -> Report:
    return Report(
        suite_name="Evidence Suite",
        timestamp=timestamp,
        summary=ReportSummary(
            total=1,
            passed=1,
            failed=0,
            skipped=0,
            pass_rate=1.0,
            avg_score=1.0,
        ),
        results=[
            TestResult(
                test_case_id="tc-1",
                test_case_name="Stable result",
                passed=True,
                score=1.0,
                actual_response="stable",
                execution_time_ms=execution_time_ms,
                backend_metadata={"model": "mock", "latency_ms": execution_time_ms},
            )
        ],
        metadata={"backend": "mock", "suite_path": suite_path},
    )


def test_reproducibility_hash_ignores_runtime_noise_and_paths(tmp_path: Path) -> None:
    first = _report(
        timestamp=datetime(2026, 1, 1),
        execution_time_ms=1.0,
        suite_path=str(tmp_path / "one" / "suite.yaml"),
    )
    second = _report(
        timestamp=datetime(2026, 1, 2),
        execution_time_ms=999.0,
        suite_path=str(tmp_path / "two" / "suite.yaml"),
    )

    assert reproducibility_hash(first) == reproducibility_hash(second)


def test_redact_secrets_recurses_without_mutating_input() -> None:
    value = {
        "api_key": "secret",
        "nested": {"authorization": "Bearer token", "safe": "value"},
        "items": [{"webhook_url": "https://example.test/hook"}],
    }

    redacted = redact_secrets(value)

    assert redacted == {
        "api_key": "[REDACTED]",
        "nested": {"authorization": "[REDACTED]", "safe": "value"},
        "items": [{"webhook_url": "[REDACTED]"}],
    }
    assert value["api_key"] == "secret"


def test_redact_secrets_handles_camel_case_credential_keys() -> None:
    assert redact_secrets({"apiKey": "secret", "accessToken": "token"}) == {
        "apiKey": "[REDACTED]",
        "accessToken": "[REDACTED]",
    }


def test_bundle_writes_expected_files_and_verifies(tmp_path: Path) -> None:
    suite_path = tmp_path / "suite.yaml"
    suite_path.write_text("name: Evidence Suite\ntest_cases: []\n", encoding="utf-8")
    output_dir = tmp_path / "evidence"
    report = _report(
        timestamp=datetime.now(),
        execution_time_ms=2.0,
        suite_path=str(suite_path),
    )

    manifest = build_evidence_bundle(
        output_dir=output_dir,
        report=report,
        suite_path=suite_path,
        backend="mock",
        mode="sim",
        model="mock",
        seed=42,
        config={"EVALFORGE_OPENAI_API_KEY": "should-not-ship"},
    )

    assert manifest.reproducibility_hash == reproducibility_hash(report)
    assert {
        "manifest.json",
        "report.json",
        "report.md",
        "checksums.sha256",
    } == {path.name for path in output_dir.iterdir()}
    verified = verify_evidence_bundle(output_dir)
    assert verified.report_hash == manifest.report_hash


def test_bundle_verification_rejects_tampering(tmp_path: Path) -> None:
    suite_path = tmp_path / "suite.yaml"
    suite_path.write_text("name: Evidence Suite\ntest_cases: []\n", encoding="utf-8")
    output_dir = tmp_path / "evidence"
    build_evidence_bundle(
        output_dir=output_dir,
        report=_report(
            timestamp=datetime.now(),
            execution_time_ms=2.0,
            suite_path=str(suite_path),
        ),
        suite_path=suite_path,
        backend="mock",
        mode="sim",
        model="mock",
        seed=42,
    )
    report_path = output_dir / "report.json"
    report_path.write_text(
        report_path.read_text(encoding="utf-8") + "\n", encoding="utf-8"
    )

    with pytest.raises(EvidenceVerificationError, match="Checksum"):
        verify_evidence_bundle(output_dir)


def test_bundle_verification_rejects_malformed_manifest(tmp_path: Path) -> None:
    output_dir = tmp_path / "evidence"
    output_dir.mkdir()
    (output_dir / "manifest.json").write_text("not-json", encoding="utf-8")

    with pytest.raises(EvidenceVerificationError, match="manifest"):
        verify_evidence_bundle(output_dir)


def test_bundle_verification_rejects_missing_payload(tmp_path: Path) -> None:
    suite_path = tmp_path / "suite.yaml"
    suite_path.write_text("name: Evidence Suite\ntest_cases: []\n", encoding="utf-8")
    output_dir = tmp_path / "evidence"
    build_evidence_bundle(
        output_dir=output_dir,
        report=_report(
            timestamp=datetime.now(),
            execution_time_ms=2.0,
            suite_path=str(suite_path),
        ),
        suite_path=suite_path,
        backend="mock",
    )
    (output_dir / "report.md").unlink()

    with pytest.raises(EvidenceVerificationError, match="missing"):
        verify_evidence_bundle(output_dir)


def test_bundle_includes_optional_drift_payload(tmp_path: Path) -> None:
    suite_path = tmp_path / "suite.yaml"
    suite_path.write_text("name: Evidence Suite\ntest_cases: []\n", encoding="utf-8")
    output_dir = tmp_path / "evidence"
    drift = DriftResult(
        suite_name="Evidence Suite",
        baseline_timestamp="2026-01-01T00:00:00",
        current_timestamp="2026-01-02T00:00:00",
        pass_rate_delta=-0.5,
        avg_score_delta=-0.2,
        is_regression=True,
        added_tests=["new"],
        removed_tests=["old"],
        score_deltas=[
            {
                "test_case_id": "stable",
                "test_case_name": "Stable",
                "baseline_score": 0.9,
                "current_score": 0.7,
                "score_delta": -0.2,
            }
        ],
    )

    manifest = build_evidence_bundle(
        output_dir=output_dir,
        report=_report(
            timestamp=datetime.now(),
            execution_time_ms=2.0,
            suite_path=str(suite_path),
        ),
        suite_path=suite_path,
        backend="mock",
        drift=drift,
    )

    assert (output_dir / "drift.json").is_file()
    assert manifest.decision == "regression"
    assert verify_evidence_bundle(output_dir).drift == drift.model_dump(mode="json")

    build_evidence_bundle(
        output_dir=output_dir,
        report=_report(
            timestamp=datetime.now(),
            execution_time_ms=2.0,
            suite_path=str(suite_path),
        ),
        suite_path=suite_path,
        backend="mock",
    )
    assert not (output_dir / "drift.json").exists()


def test_cli_generates_and_verifies_evidence_bundle(tmp_path: Path) -> None:
    suite_path = tmp_path / "suite.yaml"
    suite_path.write_text(
        """
name: CLI Evidence Suite
test_cases:
  - id: tc-1
    name: Stable response
    type: exact_answer
    input: hello
    expected: This is a mock response.
""".strip(),
        encoding="utf-8",
    )
    evidence_dir = tmp_path / "evidence"

    result = runner.invoke(
        app,
        [
            "eval",
            str(suite_path),
            "--backend",
            "mock",
            "--no-save",
            "--format",
            "json",
            "--output",
            str(tmp_path / "reports"),
            "--evidence-dir",
            str(evidence_dir),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert verify_evidence_bundle(evidence_dir).suite_hash

    verify_result = runner.invoke(app, ["evidence", "verify", str(evidence_dir)])
    assert verify_result.exit_code == 0, verify_result.stdout
    assert "Evidence verified" in verify_result.stdout


def test_identical_offline_cli_runs_have_same_reproducibility_hash(
    tmp_path: Path,
) -> None:
    suite_path = tmp_path / "suite.yaml"
    suite_path.write_text(
        """
name: Stable CLI Suite
test_cases:
  - id: tc-1
    name: Stable response
    type: exact_answer
    input: hello
    expected: This is a mock response.
""".strip(),
        encoding="utf-8",
    )
    hashes: list[str] = []

    for index in range(2):
        evidence_dir = tmp_path / f"evidence-{index}"
        result = runner.invoke(
            app,
            [
                "eval",
                str(suite_path),
                "--backend",
                "mock",
                "--no-save",
                "--format",
                "json",
                "--output",
                str(tmp_path / f"reports-{index}"),
                "--evidence-dir",
                str(evidence_dir),
            ],
        )
        assert result.exit_code == 0, result.stdout
        hashes.append(verify_evidence_bundle(evidence_dir).reproducibility_hash)

    assert hashes[0] == hashes[1]


def test_cli_evidence_verify_returns_nonzero_for_missing_file(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / "manifest.json").write_text("{}", encoding="utf-8")

    result = runner.invoke(app, ["evidence", "verify", str(evidence_dir)])

    assert result.exit_code == 2
    assert "Evidence verification failed" in result.stdout
