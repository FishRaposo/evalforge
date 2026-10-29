"""Retrieval check judge for verifying document retrieval correctness."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from evalforge.judges.base import BaseJudge, JudgeResult
from evalforge.judges.source_ids import normalize_source_id, resolve_match_mode
from evalforge.models.test_case import TestCase

RETRIEVED_IDS_KEY = "retrieved_ids"


class RetrievalCheckJudge(BaseJudge):
    """Judge that verifies the correct documents were retrieved.

    When the backend reports the documents it retrieved
    (``BackendResponse.metadata["retrieved_ids"]``), the score comes from that
    structured list: every expected document must be present by normalized ID,
    whatever the answer text says. Without it the judge falls back to the
    answer text and, in strict mode (the default), requires each expected
    document identifier verbatim (case-insensitive, on token boundaries), so
    ``refund_policy_v1.md`` does not satisfy ``refund_policy_v2.md`` and an
    answer that only paraphrases the topic does not count as a retrieval. The
    historical stem and word-overlap matching on the answer text is available
    per case with ``metadata: {match: fuzzy}``.
    """

    def judge(self, test_case: TestCase, response: str) -> JudgeResult:
        """Evaluate retrieval from the answer text alone (no backend metadata).

        Args:
            test_case: The test case with expected documents.
            response: The actual AI response to check.

        Returns:
            JudgeResult with retrieval match ratio.
        """
        return self.judge_with_context(test_case, response, None)

    def judge_with_context(
        self,
        test_case: TestCase,
        response: str,
        backend_metadata: Mapping[str, Any] | None = None,
    ) -> JudgeResult:
        """Evaluate whether the expected documents were retrieved.

        Args:
            test_case: The test case with expected documents.
            response: The actual AI response to check.
            backend_metadata: Backend response metadata; ``retrieved_ids`` is
                used when present.

        Returns:
            JudgeResult with retrieval match ratio.
        """
        expected_data = test_case.expected or {}
        expected_docs: list[str] = (
            expected_data.get("documents", [])
            if isinstance(expected_data, dict)
            else []
        )

        if not expected_docs:
            return JudgeResult(
                passed=True,
                score=1.0,
                details={"message": "No documents required"},
            )

        try:
            mode = resolve_match_mode(test_case.metadata)
            retrieved_ids = self._retrieved_ids(backend_metadata)
        except ValueError as exc:
            return JudgeResult(passed=False, score=0.0, details={"error": str(exc)})

        extra: dict[str, Any] = {"match_mode": mode}
        if retrieved_ids is not None:
            retrieved = self._check_retrieved_ids(expected_docs, retrieved_ids)
            extra["evidence"] = RETRIEVED_IDS_KEY
            extra["retrieved_ids"] = retrieved_ids
        elif mode == "fuzzy":
            retrieved = self._check_retrieval_list(expected_docs, response)
            extra["evidence"] = "response_text"
        else:
            retrieved = self._check_response_ids(expected_docs, response)
            extra["evidence"] = "response_text"

        score = len(retrieved["found"]) / len(expected_docs) if expected_docs else 1.0
        passed = len(retrieved["missing"]) == 0

        return JudgeResult(
            passed=passed,
            score=score,
            details={
                "found_documents": retrieved["found"],
                "missing_documents": retrieved["missing"],
                "total_expected": len(expected_docs),
                "total_found": len(retrieved["found"]),
                **extra,
            },
        )

    @staticmethod
    def _retrieved_ids(
        backend_metadata: Mapping[str, Any] | None,
    ) -> list[str] | None:
        """Return the backend's retrieved document IDs, or None if not reported.

        Raises:
            ValueError: If ``retrieved_ids`` is present but not a list of IDs.
        """
        if not backend_metadata or RETRIEVED_IDS_KEY not in backend_metadata:
            return None
        raw = backend_metadata[RETRIEVED_IDS_KEY]
        if not isinstance(raw, (list, tuple)) or not all(
            isinstance(item, (str, int)) for item in raw
        ):
            raise ValueError(
                f"backend metadata '{RETRIEVED_IDS_KEY}' must be a list of "
                f"document IDs, got {type(raw).__name__}"
            )
        return [str(item) for item in raw]

    @staticmethod
    def _check_retrieved_ids(
        expected_docs: list[str], retrieved_ids: list[str]
    ) -> dict[str, list[str]]:
        """Match expected documents to structured retrieved IDs by normalized ID."""
        retrieved = {normalize_source_id(doc_id) for doc_id in retrieved_ids}
        found = [doc for doc in expected_docs if normalize_source_id(doc) in retrieved]
        missing = [doc for doc in expected_docs if doc not in found]
        return {"found": found, "missing": missing}

    @staticmethod
    def _check_response_ids(
        expected_docs: list[str], response: str
    ) -> dict[str, list[str]]:
        """Strict text fallback: each expected ID must appear verbatim in the answer.

        Case-insensitive, bounded so ``policy.pdf`` does not match inside
        ``old_policy.pdf`` and ``v2.md`` does not match ``v2.mdx``.
        """
        found: list[str] = []
        missing: list[str] = []
        for doc in expected_docs:
            pattern = (
                r"(?<![0-9A-Za-z_\-])" + re.escape(doc.strip()) + r"(?![0-9A-Za-z_\-])"
            )
            if doc.strip() and re.search(pattern, response, re.IGNORECASE):
                found.append(doc)
            else:
                missing.append(doc)
        return {"found": found, "missing": missing}

    def _check_retrieval_list(
        self, expected_docs: list[str], response: str
    ) -> dict[str, list[str]]:
        """Fuzzy (opt-in) check of which expected documents the answer mentions.

        Accepts the full name or its stem as a substring, or a 50% word
        overlap with the stem. Only used with ``match: fuzzy``.

        Args:
            expected_docs: List of expected document identifiers.
            response: The response text to search for references.

        Returns:
            Dict with 'found' and 'missing' document lists.
        """
        found: list[str] = []
        missing: list[str] = []
        response_lower = response.lower()

        for doc in expected_docs:
            doc_lower = doc.lower()
            doc_stem = doc_lower.rsplit(".", 1)[0] if "." in doc_lower else doc_lower

            if doc_lower in response_lower or doc_stem in response_lower:
                found.append(doc)
            else:
                doc_words = doc_stem.replace("_", " ").replace("-", " ").split()
                word_matches = sum(1 for w in doc_words if w in response_lower)
                if doc_words and word_matches / len(doc_words) >= 0.5:
                    found.append(doc)
                else:
                    missing.append(doc)

        return {"found": found, "missing": missing}
