"""Independent review regressions, observed failing before their repairs."""

import json

import pytest
import yaml
from typer.testing import CliRunner

from evalforge.cli import app
from evalforge.evaluation import evaluate_saved
from evalforge.evidence import verify_evidence_bundle
from tests.test_strict_gate import input_pair


@pytest.mark.parametrize("field", ["dataset_revision", "label_origin", "origin"])
def test_missing_provenance_dominates_a_definite_wrong_answer(tmp_path, field):
    def incomplete_wrong(record):
        record["answer"] = "Refunds take 70 days."
        record["provenance"].pop(field)

    outcome = evaluate_saved(*input_pair(tmp_path, change=incomplete_wrong))
    assert outcome.exit_code == 2
    assert outcome.report.results[0].outcome == "indeterminate"


@pytest.mark.parametrize("mutation", ["revision", "contract"])
def test_saved_baseline_refuses_noncomparable_data_before_writing_report(
    tmp_path, mutation
):
    suite, responses = input_pair(tmp_path)
    baseline = evaluate_saved(suite, responses).report
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(baseline.model_dump_json())
    raw = yaml.safe_load(suite.read_text())
    if mutation == "revision":
        raw["version"] = "test-v2"
        record = json.loads(responses.read_text())
        record["provenance"]["dataset_revision"] = "test-v2"
        responses.write_text(json.dumps(record))
    else:
        raw["test_cases"][0]["input"] = "A changed input contract"
    suite.write_text(yaml.safe_dump(raw))
    output = tmp_path / "reports"
    result = CliRunner().invoke(
        app,
        [
            "eval",
            str(suite),
            "--backend",
            "saved",
            "--response-file",
            str(responses),
            "--strict-evidence",
            "--baseline",
            str(baseline_path),
            "--no-save",
            "--format",
            "json",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 2, result.stdout
    assert "not comparable" in result.stdout
    assert not output.exists()


def test_nonstrict_saved_legacy_checks_disclose_mode_and_evidence_replays_same_mode(
    tmp_path,
):
    suite, responses = input_pair(tmp_path)
    raw = yaml.safe_load(suite.read_text())
    raw["test_cases"][0].update(type="exact_answer", expected="Refunds take 7 days.")
    suite.write_text(yaml.safe_dump(raw))
    output = tmp_path / "reports"
    evidence = tmp_path / "bundle"
    result = CliRunner().invoke(
        app,
        [
            "eval",
            str(suite),
            "--backend",
            "saved",
            "--response-file",
            str(responses),
            "--no-save",
            "--format",
            "json",
            "--output",
            str(output),
            "--evidence-dir",
            str(evidence),
        ],
    )
    assert result.exit_code == 0, result.stdout
    manifest = verify_evidence_bundle(evidence)
    report = json.loads(next(output.glob("*.json")).read_text())
    assert report["metadata"]["strict_evidence"] is False
    assert report["metadata"]["judge_method"] == "legacy_saved_checks"
    assert report["metadata"]["gate"]["status"] == "cannot_evaluate"
    assert report["metadata"]["gate"]["exit_code"] == 2
    assert report["results"][0]["passed"] is True
    assert (
        report["results"][0]["judge_details"]["assessment"]["method"] == "exact_answer"
    )
    assert "Strict evidence: passed" not in result.stdout
    assert "Saved evaluation" in result.stdout
    assert manifest.schema_version == 3


def test_matching_saved_contract_still_compares_a_real_regression(tmp_path):
    suite, responses = input_pair(tmp_path)
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(evaluate_saved(suite, responses).report.model_dump_json())
    record = json.loads(responses.read_text())
    record["answer"] = "Refunds take 70 days."
    responses.write_text(json.dumps(record))
    evidence = tmp_path / "evidence"
    result = CliRunner().invoke(
        app,
        [
            "eval",
            str(suite),
            "--backend",
            "saved",
            "--response-file",
            str(responses),
            "--strict-evidence",
            "--no-save",
            "--baseline",
            str(baseline_path),
            "--evidence-dir",
            str(evidence),
            "--output",
            str(tmp_path / "reports"),
        ],
    )
    assert result.exit_code == 1, result.stdout
    manifest = verify_evidence_bundle(evidence)
    assert manifest.drift["is_regression"] is True
    assert manifest.gate["status"] == "failed"


@pytest.mark.parametrize("failed_export", ["report", "evidence"])
@pytest.mark.parametrize("persist", [False, True])
def test_strict_export_io_failure_returns_execution_error_without_success_claim(
    tmp_path, failed_export, persist
):
    suite, responses = input_pair(tmp_path)
    obstacle = tmp_path / "existing-file"
    obstacle.write_text("Keep this file intact.")
    reports = obstacle if failed_export == "report" else tmp_path / "reports"
    evidence = obstacle if failed_export == "evidence" else tmp_path / "evidence"
    history = tmp_path / "history.db"
    history_args = ["--db", str(history)] if persist else ["--no-save"]
    result = CliRunner().invoke(
        app,
        [
            "eval",
            str(suite),
            "--backend",
            "saved",
            "--response-file",
            str(responses),
            "--strict-evidence",
            *history_args,
            "--format",
            "json",
            "--output",
            str(reports),
            "--evidence-dir",
            str(evidence),
        ],
    )
    assert result.exit_code == 2, result.stdout
    assert "Could not export completed evaluation" in result.stdout
    assert "Report saved to:" not in result.stdout
    assert "Strict evidence: passed" not in result.stdout
    assert "Traceback" not in result.stdout
    assert obstacle.read_text() == "Keep this file intact."
    if persist:
        from evalforge.storage.history import HistoryStore

        runs = HistoryStore(str(history)).get_runs()
        assert len(runs) == 1
        assert json.loads(runs[0]["report_json"])["metadata"]["gate"]["exit_code"] == 0
        assert "assessment remains saved in history" in result.stdout
    else:
        assert not history.exists()
