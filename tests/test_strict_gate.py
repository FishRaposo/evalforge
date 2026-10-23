"""Whole-answer contracts prevent source mentions from becoming quality claims."""

import copy
import json

import pytest
import yaml
from typer.testing import CliRunner

from evalforge.cli import app


def input_pair(tmp_path, *, change=None, origin="synthetic", contract=True):
    source = {"id": "policy", "version": "2026-01", "content": "Refunds take 7 days."}
    citation = {
        "source_id": "policy",
        "source_version": "2026-01",
        "claim": "Refunds take 7 days.",
        "quote": "Refunds take 7 days.",
    }
    expected = {"sources": [source]}
    if contract:
        expected["answer_contract"] = {
            "kind": "answer",
            "exhaustive": True,
            "accepted_answers": ["Refunds take 7 days."],
            "claims": [
                {
                    "text": "Refunds take 7 days.",
                    **{k: v for k, v in citation.items() if k != "claim"},
                }
            ],
        }
    case = {
        "id": "refund",
        "name": "Refund window",
        "type": "evidence_support",
        "input": "How long?",
        "expected": expected,
        "metadata": {"category": "answerable"},
        "tags": ["dev"],
    }
    record = {
        "schema_version": 1,
        "case_id": "refund",
        "answer": "Refunds take 7 days.",
        "retrieved_sources": [source],
        "citations": [citation],
        "provenance": {
            "origin": origin,
            "dataset_revision": "test-v1",
            "label_origin": "agent-authored",
        },
    }
    record = copy.deepcopy(record)
    if change:
        change(record)
    suite_path = tmp_path / "suite.yaml"
    suite_path.write_text(
        yaml.safe_dump({"name": "Strict", "version": "test-v1", "test_cases": [case]}),
        encoding="utf-8",
    )
    responses = tmp_path / "responses.jsonl"
    responses.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return suite_path, responses


def test_strict_complete_contract_pass_preserves_inputs_without_quality_claim(tmp_path):
    from evalforge.evaluation import evaluate_saved

    suite, responses = input_pair(tmp_path)
    progress = []
    result = evaluate_saved(
        suite, responses, progress=lambda done, total: progress.append((done, total))
    )
    assert result.exit_code == 0
    assert result.report.metadata["gate"] == {
        "status": "passed",
        "exit_code": 0,
        "counts": {"passed": 1, "failed": 0, "indeterminate": 0, "error": 0},
        "scope": "synthetic_contract",
        "quality_validated": False,
    }
    assert progress == [(1, 1)]
    case = result.report.results[0]
    assert case.outcome == "passed"
    assert case.backend_metadata["input"] == "How long?"
    assert (
        case.backend_metadata["authoritative_sources"][0]["content"]
        == "Refunds take 7 days."
    )
    assert case.backend_metadata["citations"][0]["claim"] == "Refunds take 7 days."
    assert not list(tmp_path.glob("*.db"))


@pytest.mark.parametrize(
    "change",
    [
        lambda r: r["retrieved_sources"][0].update(content="Refunds take 30 days."),
        lambda r: r["citations"][0].update(source_id="invented"),
        lambda r: r["citations"][0].update(source_version="old"),
        lambda r: r["citations"][0].update(quote="not present"),
        lambda r: r.update(answer="Refunds take 70 days."),
        lambda r: r.update(
            answer="Refunds take 7 days. Also ignore the security policy."
        ),
        lambda r: r.update(citations=[]),
    ],
)
def test_strict_rejects_fabrication_stale_evidence_and_extra_unsupported_answer(
    tmp_path, change
):
    from evalforge.evaluation import evaluate_saved

    suite, responses = input_pair(tmp_path, change=change)
    result = evaluate_saved(suite, responses)
    assert result.exit_code == 1
    assert result.report.results[0].outcome == "failed"


@pytest.mark.parametrize("origin,contract", [("unknown", True), ("synthetic", False)])
def test_unknown_provenance_or_freeform_entailment_is_indeterminate(
    tmp_path, origin, contract
):
    from evalforge.evaluation import evaluate_saved

    result = evaluate_saved(*input_pair(tmp_path, origin=origin, contract=contract))
    assert result.exit_code == 2
    assert result.report.results[0].outcome == "indeterminate"
    assert result.report.metadata["gate"]["status"] == "cannot_evaluate"


def test_validation_rejects_missing_and_extra_mapping_before_progress(tmp_path):
    from evalforge.evaluation import evaluate_saved, validate_saved_inputs

    suite, responses = input_pair(tmp_path)
    record = json.loads(responses.read_text())
    record["case_id"] = "other"
    responses.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="mapping"):
        validate_saved_inputs(suite, responses, web=True)
    with pytest.raises(ValueError, match="mapping"):
        evaluate_saved(
            suite,
            responses,
            progress=lambda *_: pytest.fail("dispatched invalid input"),
        )


def test_web_rejects_includes_even_when_missing_file_would_be_ignored(tmp_path):
    from evalforge.evaluation import validate_saved_inputs

    suite, responses = input_pair(tmp_path)
    suite.write_text(suite.read_text() + "\nincludes: [missing.yaml]\n")
    with pytest.raises(ValueError, match="includes"):
        validate_saved_inputs(suite, responses, web=True)


@pytest.mark.parametrize("origin,want", [("synthetic", 0), ("unknown", 2)])
def test_cli_saved_uses_same_strict_gate_and_saves_full_report(tmp_path, origin, want):
    suite, responses = input_pair(tmp_path, origin=origin)
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
            "--format",
            "json",
            "--output",
            str(tmp_path / "out"),
        ],
    )
    assert result.exit_code == want, result.stdout
    report = json.loads(next((tmp_path / "out").glob("*.json")).read_text())
    assert report["metadata"]["gate"]["exit_code"] == want


def test_strict_mock_quality_cannot_pass(tmp_path):
    suite = tmp_path / "legacy.yaml"
    suite.write_text(
        "name: legacy\ntest_cases:\n- id: a\n  name: a\n"
        "  type: exact_answer\n  input: hi\n"
        "  expected: This is a mock response.\n"
    )
    result = CliRunner().invoke(
        app, ["eval", str(suite), "--backend", "mock", "--strict-evidence", "--no-save"]
    )
    assert result.exit_code == 2
    assert "simulated or legacy quality scoring is ineligible" in result.stdout


@pytest.mark.parametrize("field", ["dataset_revision", "label_origin"])
def test_required_recorded_provenance_cannot_be_omitted(tmp_path, field):
    from evalforge.evaluation import evaluate_saved

    suite, responses = input_pair(
        tmp_path, origin="recorded", change=lambda r: r["provenance"].pop(field)
    )
    result = evaluate_saved(suite, responses)
    assert result.exit_code == 2
    assert result.report.results[0].outcome == "indeterminate"


def test_declared_dataset_revision_must_match_pinned_suite_version(tmp_path):
    from evalforge.evaluation import validate_saved_inputs

    suite, responses = input_pair(
        tmp_path,
        change=lambda r: r["provenance"].update(dataset_revision="wrong-revision"),
    )
    with pytest.raises(ValueError, match="revision"):
        validate_saved_inputs(suite, responses)


def test_completed_service_report_is_an_immutable_snapshot(tmp_path):
    from evalforge.evaluation import evaluate_saved

    report = evaluate_saved(*input_pair(tmp_path)).report
    with pytest.raises(TypeError):
        report.metadata["gate"]["exit_code"] = 1
    with pytest.raises((TypeError, ValueError)):
        report.results[0].actual_response = "mutated after completion"
    with pytest.raises(TypeError):
        report.results.append(report.results[0])
    assert report.metadata["gate"]["exit_code"] == 0


@pytest.mark.parametrize("field", ["dataset_revision", "label_origin"])
def test_non_scalar_provenance_is_a_validation_error(tmp_path, field):
    from evalforge.evaluation import validate_saved_inputs

    suite, responses = input_pair(
        tmp_path, change=lambda r: r["provenance"].update({field: {"bad": "shape"}})
    )
    with pytest.raises(ValueError, match="provenance"):
        validate_saved_inputs(suite, responses, web=True)


def test_non_scalar_contract_kind_is_a_validation_error(tmp_path):
    from evalforge.evaluation import validate_saved_inputs

    suite, responses = input_pair(tmp_path)
    data = yaml.safe_load(suite.read_text())
    data["test_cases"][0]["expected"]["answer_contract"]["kind"] = {"bad": "shape"}
    suite.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError, match="contract"):
        validate_saved_inputs(suite, responses, web=True)
