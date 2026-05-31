"""Citation check judge for verifying source references."""

from __future__ import annotations

import re
from typing import Any

from evalforge.judges.base import BaseJudge, JudgeResult
from evalforge.models.test_case import TestCase


class CitationCheckJudge(BaseJudge):
    """Judge that verifies the response cites the required sources.

    Checks that all expected source citations are present in the
    response text, using flexible matching for citation formats.
    """

    def judge(self, test_case: TestCase, response: str) -> JudgeResult:
        """Evaluate whether the response includes required citations.

        Args:
            test_case: The test case with expected sources to cite.
            response: The actual AI response to check.

        Returns:
            JudgeResult with citation match ratio and details.
        """
        expected_data = test_case.expected or {}
        expected_sources: list[str] = (
            expected_data.get("sources", []) if isinstance(expected_data, dict) else []
        )

        if not expected_sources:
            return JudgeResult(
                passed=True,
                score=1.0,
                details={"message": "No sources required"},
            )

        found_citations = self._extract_citations(response)
        matched: list[str] = []
        unmatched: list[str] = []

        for source in expected_sources:
            if self._match_source(source, found_citations, response):
                matched.append(source)
            else:
                unmatched.append(source)

        score = len(matched) / len(expected_sources) if expected_sources else 1.0
        passed = len(unmatched) == 0

        return JudgeResult(
            passed=passed,
            score=score,
            details={
                "matched_sources": matched,
                "unmatched_sources": unmatched,
                "found_citations": found_citations,
                "total_expected": len(expected_sources),
                "total_matched": len(matched),
            },
        )

    def _extract_citations(self, response: str) -> list[str]:
        """Extract citation-like patterns from the response.

        Identifies common citation formats including bracketed numbers,
        parenthetical references, and quoted source names.

        Args:
            response: The response text to scan for citations.

        Returns:
            A list of extracted citation strings.
        """
        citations: list[str] = []

        bracket_pattern = re.findall(r"\[([^\]]+)\]", response)
        citations.extend(bracket_pattern)

        paren_pattern = re.findall(r"\(([A-Z][^)]*?\d{4}[^)]*)\)", response)
        citations.extend(paren_pattern)

        quote_pattern = re.findall(r'"([^"]+)"', response)
        citations.extend(quote_pattern)

        return citations

    def _match_source(
        self, source: str, citations: list[str], response: str
    ) -> bool:
        """Check if a source is referenced in the response.

        Uses both citation list matching and direct text search
        for flexible source detection.

        Args:
            source: The expected source name.
            citations: Extracted citations from the response.
            response: The full response text.

        Returns:
            True if the source is found.
        """
        source_lower = source.lower()

        for citation in citations:
            if source_lower in citation.lower():
                return True

        if source_lower in response.lower():
            return True

        source_words = source_lower.split()
        if len(source_words) > 1:
            word_matches = sum(1 for w in source_words if w in response.lower())
            if word_matches / len(source_words) >= 0.6:
                return True

        return False
