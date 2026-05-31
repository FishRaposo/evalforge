"""Forbidden content judge for detecting policy violations."""

from __future__ import annotations

import re

from evalforge.judges.base import BaseJudge, JudgeResult
from evalforge.models.test_case import TestCase


class ForbiddenContentJudge(BaseJudge):
    """Judge that checks responses for forbidden content or claims.

    Ensures the AI response does not contain any prohibited patterns,
    claims, or content as specified in the test case.
    """

    def judge(self, test_case: TestCase, response: str) -> JudgeResult:
        """Evaluate whether the response contains forbidden content.

        Args:
            test_case: The test case with forbidden patterns to check.
            response: The actual AI response to evaluate.

        Returns:
            JudgeResult indicating whether any forbidden content was found.
        """
        expected_data = test_case.expected or {}
        forbidden: list[str] = (
            expected_data.get("forbidden", []) if isinstance(expected_data, dict) else []
        )

        if not forbidden:
            return JudgeResult(
                passed=True,
                score=1.0,
                details={"message": "No forbidden patterns defined"},
            )

        violations = self._check_forbidden(forbidden, response)
        passed = len(violations) == 0
        score = 1.0 if passed else 0.0

        return JudgeResult(
            passed=passed,
            score=score,
            details={
                "violations": violations,
                "total_forbidden": len(forbidden),
                "total_violations": len(violations),
            },
        )

    def _check_forbidden(
        self, forbidden_patterns: list[str], response: str
    ) -> list[dict[str, str]]:
        """Check the response against forbidden patterns.

        Uses both direct substring matching and regex patterns
        for flexible forbidden content detection.

        Args:
            forbidden_patterns: List of forbidden text patterns.
            response: The response text to check.

        Returns:
            A list of violation dictionaries with pattern and match info.
        """
        violations: list[dict[str, str]] = []
        response_lower = response.lower()

        for pattern in forbidden_patterns:
            pattern_lower = pattern.lower()

            if pattern_lower in response_lower:
                violations.append(
                    {"pattern": pattern, "match_type": "substring"}
                )
                continue

            try:
                regex_match = re.search(pattern, response, re.IGNORECASE)
                if regex_match:
                    violations.append(
                        {
                            "pattern": pattern,
                            "match_type": "regex",
                            "matched_text": regex_match.group(0),
                        }
                    )
            except re.error:
                continue

        return violations
