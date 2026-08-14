"""Golden parity checks for the local judge/drift compatibility engines."""

from __future__ import annotations

import pytest

from evalforge.compatibility import RegistryDriftEngine, RegistryJudgeEngine
from evalforge.judges.registry import get_judge, list_judges
from evalforge.models.report import Report, ReportSummary
from evalforge.models.test_case import TestCase, TestCaseType
from evalforge.models.test_result import TestResult


@pytest.mark.parametrize("test_type", list(list_judges()))
def test_registry_engine_matches_builtin_judge(test_type: TestCaseType) -> None:
    expected: object
    if test_type is TestCaseType.EXACT_ANSWER:
        expected = "Paris"
    elif test_type is TestCaseType.SEMANTIC_ANSWER:
        expected = "Gravity is a force"
    elif test_type is TestCaseType.MUST_CITE:
        expected = {"sources": ["NASA"]}
    elif test_type is TestCaseType.MUST_RETRIEVE:
        expected = {"documents": ["policy.pdf"]}
    elif test_type is TestCaseType.FORBIDDEN_CONTENT:
        expected = {"forbidden": ["secret"]}
    elif test_type is TestCaseType.STRUCTURED_OUTPUT:
        expected = {"type": "object"}
    else:
        expected = None
    response = (
        "Paris"
        if test_type is TestCaseType.EXACT_ANSWER
        else "According to NASA policy.pdf"
    )
    case = TestCase(
        id=f"golden-{test_type.value}",
        name="golden",
        type=test_type,
        input="question",
        expected=expected,
    )
    direct = get_judge(test_type).judge(case, response)
    adapted = RegistryJudgeEngine().evaluate(case, response)
    assert adapted.model_dump() == direct.model_dump()


def _report(score: float, passed: bool) -> Report:
    return Report(
        suite_name="golden",
        summary=ReportSummary(
            total=1,
            passed=int(passed),
            failed=int(not passed),
            pass_rate=float(passed),
            avg_score=score,
        ),
        results=[
            TestResult(
                test_case_id="one",
                test_case_name="one",
                passed=passed,
                score=score,
            )
        ],
    )


def test_drift_engine_preserves_score_delta_and_decision() -> None:
    result = RegistryDriftEngine(threshold=0.1).compare(
        _report(0.9, True), _report(0.7, False)
    )
    assert result.is_regression is True
    assert result.score_deltas[0]["score_delta"] == -0.2
