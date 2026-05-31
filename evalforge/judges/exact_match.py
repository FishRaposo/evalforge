"""Exact match judge for precise string comparison."""

from __future__ import annotations

import re

from evalforge.judges.base import BaseJudge, JudgeResult
from evalforge.models.test_case import TestCase


class ExactMatchJudge(BaseJudge):
    """Judge that checks for exact string match (case-insensitive).

    Normalizes both the expected and actual responses by converting
    to lowercase and stripping whitespace before comparison.
    """

    def judge(self, test_case: TestCase, response: str) -> JudgeResult:
        """Evaluate whether the response exactly matches the expected answer.

        Args:
            test_case: The test case with the expected answer.
            response: The actual AI response.

        Returns:
            JudgeResult with score 1.0 for match, 0.0 otherwise.
        """
        expected = str(test_case.expected) if test_case.expected is not None else ""
        normalized_expected = self._normalize(expected)
        normalized_response = self._normalize(response)

        passed = normalized_expected == normalized_response
        score = 1.0 if passed else 0.0

        return JudgeResult(
            passed=passed,
            score=score,
            details={
                "expected": normalized_expected,
                "actual": normalized_response,
                "match_type": "exact",
            },
        )

    def _normalize(self, text: str) -> str:
        """Normalize text for comparison.

        Converts to lowercase, strips leading/trailing whitespace,
        and collapses multiple spaces into single spaces.

        Args:
            text: The text to normalize.

        Returns:
            Normalized text string.
        """
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        return text
