"""Golden-output tests pinning score-sensitive semantic-match values.

These tests lock the exact numeric scores produced by the bespoke
``SemanticMatchJudge`` TF-IDF fallback so that any future convergence onto
``shared_core.embeddings`` is gated: the refactor is only allowed if these
values stay byte-for-byte identical. The TF-IDF IDF formula in EvalForge
(``log(1 + doc_count / df)``) differs from the one in ``shared_core``; rerouting
without preserving these numbers would silently shift stored baselines.
"""

from __future__ import annotations

import pytest

from evalforge.judges.semantic_match import SemanticMatchJudge
from evalforge.models.test_case import TestCase, TestCaseType


def _semantic_case(expected: str, threshold: float = 0.3) -> TestCase:
    return TestCase(
        id="golden",
        name="Golden semantic case",
        type=TestCaseType.SEMANTIC_ANSWER,
        input="question",
        expected=expected,
        metadata={"threshold": threshold},
    )


@pytest.mark.parametrize(
    ("expected", "response", "golden_score"),
    [
        (
            "Gravity is a fundamental force that attracts objects with mass",
            "Gravity is a fundamental force that attracts objects with mass "
            "toward each other",
            0.7551,
        ),
        (
            "The quick brown fox jumps over the lazy dog",
            "The quick brown fox jumps",
            0.6808,
        ),
        (
            "hello world foo",
            "hello world bar baz",
            0.3553,
        ),
    ],
)
def test_tfidf_scores_are_pinned(
    expected: str, response: str, golden_score: float
) -> None:
    """The TF-IDF fallback must produce these exact (4-dp) scores."""
    judge = SemanticMatchJudge(threshold=0.0)
    result = judge.judge(_semantic_case(expected), response)
    assert result.score == pytest.approx(golden_score, abs=1e-4)


def test_identical_text_scores_one() -> None:
    judge = SemanticMatchJudge()
    result = judge.judge(_semantic_case("identical text here"), "identical text here")
    assert result.score == pytest.approx(1.0, abs=1e-4)


def test_disjoint_text_scores_zero() -> None:
    judge = SemanticMatchJudge()
    result = judge.judge(_semantic_case("alpha beta gamma"), "delta epsilon zeta")
    assert result.score == pytest.approx(0.0, abs=1e-4)


def test_empty_expected_and_response_scores_one() -> None:
    judge = SemanticMatchJudge()
    tc = TestCase(
        id="empty",
        name="Empty",
        type=TestCaseType.SEMANTIC_ANSWER,
        input="q",
        expected="",
    )
    result = judge.judge(tc, "")
    assert result.score == pytest.approx(1.0, abs=1e-4)


def test_threshold_decides_pass_fail() -> None:
    """A score of 0.7551 passes at 0.7 but fails at 0.8."""
    expected = "Gravity is a fundamental force that attracts objects with mass"
    response = (
        "Gravity is a fundamental force that attracts objects with mass "
        "toward each other"
    )
    passing = SemanticMatchJudge().judge(_semantic_case(expected, 0.7), response)
    failing = SemanticMatchJudge().judge(_semantic_case(expected, 0.8), response)
    assert passing.passed is True
    assert failing.passed is False
