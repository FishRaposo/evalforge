"""Supplemental post-implementation boundary and fault characterization tests."""

import pytest
import yaml

from evalforge.evaluation import evaluate_saved, validate_saved_inputs
from evalforge.judges.evidence_support import EvidenceSupportJudge
from evalforge.models.test_case import TestCase
from tests.test_strict_gate import input_pair


def test_text_only_judging_cannot_infer_structured_evidence():
    case = TestCase(id="a", name="a", type="evidence_support", input="question")
    result = EvidenceSupportJudge().judge(case, "A plausible quotation")
    assert result.details["outcome"] == "indeterminate"
    assert result.passed is False


@pytest.mark.parametrize(
    "changes",
    [
        {"evaluation_mode": "sim"},
        {"quality_scoring": "simulated"},
        {"dataset_revision": "unknown"},
        {"label_origin": ""},
    ],
)
def test_simulated_or_incomplete_quality_evidence_cannot_pass(tmp_path, changes):
    result = evaluate_saved(
        *input_pair(tmp_path, change=lambda r: r["provenance"].update(changes))
    )
    assert result.exit_code == 2
    assert result.report.results[0].outcome == "indeterminate"


def test_non_exhaustive_unlisted_answer_needs_review(tmp_path):
    suite, responses = input_pair(
        tmp_path, change=lambda r: r.update(answer="Seven days for the refund.")
    )
    raw = yaml.safe_load(suite.read_text())
    raw["test_cases"][0]["expected"]["answer_contract"]["exhaustive"] = False
    suite.write_text(yaml.safe_dump(raw))
    result = evaluate_saved(suite, responses)
    assert result.exit_code == 2
    assert result.report.results[0].outcome == "indeterminate"


def test_judge_error_retains_actual_answer_and_evidence_and_dominates_gate(
    tmp_path, monkeypatch
):
    def broken_judge(*args):
        raise ValueError("Declared test-only judge failure")

    monkeypatch.setattr(EvidenceSupportJudge, "judge_record", broken_judge)
    result = evaluate_saved(*input_pair(tmp_path))
    assert result.exit_code == 2
    case = result.report.results[0]
    assert case.outcome == "error"
    assert case.actual_response == "Refunds take 7 days."
    assert case.backend_metadata["citations"][0]["source_id"] == "policy"
    assert case.error == "Declared test-only judge failure"


def test_malformed_judge_result_is_error_never_a_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(
        EvidenceSupportJudge, "judge_record", lambda *args: {"passed": True}
    )
    result = evaluate_saved(*input_pair(tmp_path))
    assert result.exit_code == 2
    assert result.report.metadata["gate"]["counts"]["error"] == 1


@pytest.mark.parametrize(
    "mutation",
    [
        lambda e: e.update(sources="not a list"),
        lambda e: e["sources"].append(e["sources"][0].copy()),
        lambda e: e["answer_contract"].update(accepted_answers=[]),
        lambda e: e["answer_contract"].update(exhaustive="true"),
        lambda e: e["answer_contract"].update(claims=[]),
        lambda e: e["answer_contract"]["claims"][0].update(quote="fabricated"),
        lambda e: e["answer_contract"]["accepted_answers"].__setitem__(
            0, "unrelated answer"
        ),
    ],
)
def test_invalid_trusted_contract_is_rejected_before_evaluation(tmp_path, mutation):
    suite, responses = input_pair(tmp_path)
    raw = yaml.safe_load(suite.read_text())
    mutation(raw["test_cases"][0]["expected"])
    suite.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError):
        validate_saved_inputs(suite, responses, web=True)


@pytest.mark.parametrize(
    "contents", [b"\xff", b"name: [broken", b"- not-a-mapping", b"a: &a {b: *a}"]
)
def test_web_invalid_utf8_yaml_and_cycles_are_validation_errors(tmp_path, contents):
    suite, responses = input_pair(tmp_path)
    suite.write_bytes(contents)
    with pytest.raises(ValueError):
        validate_saved_inputs(suite, responses, web=True)


def test_web_case_limit_is_checked_before_record_dispatch(tmp_path):
    suite, responses = input_pair(tmp_path)
    raw = yaml.safe_load(suite.read_text())
    original = raw["test_cases"][0]
    raw["test_cases"] = [{**original, "id": f"case-{i}"} for i in range(501)]

    class NoAliases(yaml.SafeDumper):
        def ignore_aliases(self, data):
            return True

    suite.write_text(yaml.dump(raw, Dumper=NoAliases))
    with pytest.raises(ValueError, match="500"):
        validate_saved_inputs(suite, responses, web=True)


def test_saved_input_byte_caps_precede_parsing(tmp_path):
    suite, responses = input_pair(tmp_path)
    suite.write_bytes(b" " * (2 * 1024 * 1024 + 1))
    with pytest.raises(ValueError, match="2 MiB"):
        validate_saved_inputs(suite, responses, web=True)
    suite, responses = input_pair(tmp_path)
    responses.write_bytes(b" " * (10 * 1024 * 1024 + 1))
    with pytest.raises(ValueError, match="10 MiB"):
        validate_saved_inputs(suite, responses, web=True)


def test_saved_legacy_check_remains_available_but_strict_quality_is_indeterminate(
    tmp_path,
):
    suite, responses = input_pair(tmp_path)
    raw = yaml.safe_load(suite.read_text())
    raw["test_cases"][0].update(type="exact_answer", expected="Refunds take 7 days.")
    suite.write_text(yaml.safe_dump(raw))
    assert (
        evaluate_saved(suite, responses, strict=False).report.results[0].passed is True
    )
    strict = evaluate_saved(suite, responses)
    assert strict.exit_code == 2
    assert strict.report.results[0].outcome == "indeterminate"


def test_missing_retrieved_passage_and_unapproved_claim_cannot_pass(tmp_path):
    result = evaluate_saved(
        *input_pair(
            tmp_path,
            change=lambda r: r["citations"][0].update(claim="Refunds take 70 days."),
        )
    )
    assert result.exit_code == 1
    result = evaluate_saved(
        *input_pair(tmp_path, change=lambda r: r.update(retrieved_sources=[]))
    )
    assert result.exit_code == 1
