"""Citation check judge for verifying source references."""

from __future__ import annotations

import re

from evalforge.judges.base import BaseJudge, JudgeResult
from evalforge.judges.source_ids import normalize_source_id, resolve_match_mode
from evalforge.models.test_case import TestCase

_LABEL_PREFIX = re.compile(
    r"^(?:(?:sources?|refs?|references?|citations?|docs?|documents?|cited)\s*:|see\b)\s*",
    re.IGNORECASE,
)
_PIECE_SPLIT = re.compile(r"[;,|]")


class CitationCheckJudge(BaseJudge):
    """Judge that verifies the response cites the required sources.

    Strict mode (the default) only counts citations inside citation markers
    (``[...]``, ``(...)`` or quotes) whose normalized identifier equals the
    expected source, so a correct answer that cites the wrong document, the
    wrong year or the wrong version fails, and so does an answer that merely
    mentions the source's words in prose. The historical substring and
    word-overlap matching is available per case with ``metadata: {match: fuzzy}``.
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

        try:
            mode = resolve_match_mode(test_case.metadata)
        except ValueError as exc:
            return JudgeResult(passed=False, score=0.0, details={"error": str(exc)})

        found_citations = self._extract_citations(response)
        cited_ids = self._cited_ids(found_citations)
        matched: list[str] = []
        unmatched: list[str] = []

        for source in expected_sources:
            if mode == "fuzzy":
                hit = self._match_source(source, found_citations, response)
            else:
                hit = normalize_source_id(source) in cited_ids
            if hit:
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
                "match_mode": mode,
            },
        )

    def _extract_citations(self, response: str) -> list[str]:
        """Extract the contents of citation markers from the response.

        Markers are square brackets, parentheses, and straight or curly
        double quotes.

        Args:
            response: The response text to scan for citations.

        Returns:
            A list of extracted citation strings.
        """
        citations: list[str] = []
        citations.extend(re.findall(r"\[([^\]]+)\]", response))
        citations.extend(re.findall(r"\(([^)]+)\)", response))
        citations.extend(re.findall(r'"([^"]+)"', response))
        citations.extend(re.findall(r"\u201c([^\u201d]+)\u201d", response))
        return citations

    @staticmethod
    def _cited_ids(citations: list[str]) -> set[str]:
        """Normalized identifiers named by the extracted citation markers.

        Each marker counts as a whole and split on ``;``, ``,`` and ``|`` so
        ``[CDC; WHO]`` cites both, and a leading label such as ``Source:`` or
        ``see`` is ignored.
        """
        ids: set[str] = set()
        for citation in citations:
            for piece in [citation, *_PIECE_SPLIT.split(citation)]:
                cleaned = _LABEL_PREFIX.sub("", piece.strip())
                normalized = normalize_source_id(cleaned)
                if normalized:
                    ids.add(normalized)
        return ids

    def _match_source(self, source: str, citations: list[str], response: str) -> bool:
        """Fuzzy (opt-in) check that a source is referenced anywhere in the response.

        Accepts a substring of any citation or of the full text, or a 60%
        word overlap for multi-word sources. Only used with ``match: fuzzy``.

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
