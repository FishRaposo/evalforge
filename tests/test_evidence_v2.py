"""Evidence schema v2 compatibility and metadata checks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evalforge.evidence import (
    EvidenceVerificationError,
    build_evidence_bundle,
    reproducibility_hash,
    sha256_file,
    verify_evidence_bundle,
)
from evalforge.models.report import Report, ReportSummary
from evalforge.models.test_result import TestResult
from evalforge.models.trace import AgentTrace


def _report() -> Report:
    return Report(
        suite_name="v2",
        summary=ReportSummary(
            total=1, passed=1, failed=0, pass_rate=1.0, avg_score=1.0
        ),
        results=[
            TestResult(
                test_case_id="one",
                test_case_name="One",
                passed=True,
                score=1.0,
                actual_response="ok",
                agent_trace=AgentTrace(
                    final_response="ok",
                    steps=[],
                    assertions={"passed": True},
                ),
            )
        ],
        metadata={"provider": "mock", "model": "fixture"},
    )


def test_v2_bundle_records_calibration_trace_and_compatibility_metadata(
    tmp_path: Path,
) -> None:
    suite = tmp_path / "suite.yaml"
    suite.write_text("name: v2\n", encoding="utf-8")
    output = tmp_path / "evidence"
    manifest = build_evidence_bundle(
        output_dir=output,
        report=_report(),
        suite_path=suite,
        backend="mock",
        calibration={"sample_count": 2, "agreement": "high"},
        trace={"schema_version": 1, "steps": []},
        compatibility_layer="evalforge.core",
        provider_metadata={"provider": "mock", "cache_hit": False},
    )

    assert manifest.schema_version == 2
    assert manifest.calibration == {"sample_count": 2, "agreement": "high"}
    assert manifest.compatibility_layer == "evalforge.core"
    assert (output / "calibration.json").is_file()
    assert (output / "trace.json").is_file()
    assert verify_evidence_bundle(output).schema_version == 2


def test_v1_manifest_still_verifies(tmp_path: Path) -> None:
    suite = tmp_path / "suite.yaml"
    suite.write_text("name: v1\n", encoding="utf-8")
    output = tmp_path / "evidence"
    build_evidence_bundle(
        output_dir=output, report=_report(), suite_path=suite, backend="mock"
    )
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 1
    for key in (
        "calibration",
        "agent_trace_schema_version",
        "compatibility_layer",
        "provider_metadata",
    ):
        manifest.pop(key, None)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    assert verify_evidence_bundle(output).schema_version == 1


def test_trace_runtime_fields_do_not_change_reproducibility_hash() -> None:
    first = _report()
    second = _report()
    assert first.results[0].agent_trace is not None
    assert second.results[0].agent_trace is not None
    first.results[0].agent_trace.steps = []
    second.results[0].agent_trace.steps = []
    first.results[0].agent_trace.assertions["runtime"] = {"duration_ms": 1.0}
    second.results[0].agent_trace.assertions["runtime"] = {"duration_ms": 99.0}
    assert reproducibility_hash(first) == reproducibility_hash(second)


def test_unknown_schema_is_rejected(tmp_path: Path) -> None:
    output = tmp_path / "evidence"
    output.mkdir()
    (output / "manifest.json").write_text('{"schema_version": 99}', encoding="utf-8")
    with pytest.raises(EvidenceVerificationError, match="schema"):
        verify_evidence_bundle(output)


def _resign_file(output: Path, name: str) -> None:
    """Update the bundle's declared digest after intentionally changing a file."""
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][name] = sha256_file(output / name)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    checksums = "".join(
        f"{digest}  {filename}\n"
        for filename, digest in sorted(manifest["files"].items())
    )
    (output / "checksums.sha256").write_text(checksums, encoding="utf-8")


def test_malformed_calibration_payload_is_rejected(tmp_path: Path) -> None:
    suite = tmp_path / "suite.yaml"
    suite.write_text("name: malformed-calibration\n", encoding="utf-8")
    output = tmp_path / "evidence"
    build_evidence_bundle(
        output_dir=output,
        report=_report(),
        suite_path=suite,
        backend="mock",
        calibration={"schema_version": 1, "results": []},
    )
    (output / "calibration.json").write_text(
        json.dumps({"schema_version": 1, "results": "not-a-list"}),
        encoding="utf-8",
    )
    _resign_file(output, "calibration.json")

    with pytest.raises(EvidenceVerificationError, match="calibration"):
        verify_evidence_bundle(output)


def test_malformed_trace_payload_is_rejected(tmp_path: Path) -> None:
    suite = tmp_path / "suite.yaml"
    suite.write_text("name: malformed-trace\n", encoding="utf-8")
    output = tmp_path / "evidence"
    build_evidence_bundle(
        output_dir=output,
        report=_report(),
        suite_path=suite,
        backend="mock",
        trace={"schema_version": 1, "results": []},
    )
    (output / "trace.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "results": [{"test_case_id": "one", "trace": {"steps": "not-a-list"}}],
            }
        ),
        encoding="utf-8",
    )
    _resign_file(output, "trace.json")

    with pytest.raises(EvidenceVerificationError, match="trace"):
        verify_evidence_bundle(output)
