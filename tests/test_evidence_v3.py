"""Portable strict evidence retains and rechecks the actual saved inputs."""

import json

import pytest

from evalforge.evaluation import evaluate_saved
from evalforge.evidence import (
    EvidenceVerificationError,
    build_evidence_bundle,
    sha256_file,
    verify_evidence_bundle,
)
from evalforge.portfolio import get_portfolio_profiles


def test_strict_bundle_copies_inputs_and_verifies_without_original_files(tmp_path):
    profile = get_portfolio_profiles()[1]
    outcome = evaluate_saved(profile["suite_path"], profile["response_path"])
    destination = tmp_path / "evidence"
    manifest = build_evidence_bundle(
        output_dir=destination,
        report=outcome.report,
        suite_path=profile["suite_path"],
        backend="saved",
        mode="saved",
        source_artifacts={
            "suite.yaml": profile["suite_path"],
            "responses.jsonl": profile["response_path"],
        },
    )
    assert manifest.schema_version == 3
    assert manifest.source_artifacts["responses.jsonl"] == sha256_file(
        profile["response_path"]
    )
    assert manifest.gate["exit_code"] == 1
    assert verify_evidence_bundle(destination).schema_version == 3
    assert (destination / "suite.yaml").is_file()


def test_v3_rejects_source_tampering_even_when_file_checksums_are_updated(tmp_path):
    profile = get_portfolio_profiles()[0]
    outcome = evaluate_saved(profile["suite_path"], profile["response_path"])
    destination = tmp_path / "evidence"
    build_evidence_bundle(
        output_dir=destination,
        report=outcome.report,
        suite_path=profile["suite_path"],
        backend="saved",
        mode="saved",
        source_artifacts={
            "suite.yaml": profile["suite_path"],
            "responses.jsonl": profile["response_path"],
        },
    )
    responses = destination / "responses.jsonl"
    lines = responses.read_text().splitlines()
    first = json.loads(lines[0])
    first["answer"] = "Fabricated answer"
    lines[0] = json.dumps(first)
    responses.write_text("\n".join(lines) + "\n")
    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"]["responses.jsonl"] = sha256_file(responses)
    manifest["source_artifacts"]["responses.jsonl"] = sha256_file(responses)
    manifest_path.write_text(json.dumps(manifest))
    (destination / "checksums.sha256").write_text(
        "".join(f"{h}  {n}\n" for n, h in sorted(manifest["files"].items()))
    )
    with pytest.raises(EvidenceVerificationError, match="input|replay|source"):
        verify_evidence_bundle(destination)
