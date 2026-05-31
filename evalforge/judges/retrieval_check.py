"""Retrieval check judge for verifying document retrieval correctness."""

from __future__ import annotations

from evalforge.judges.base import BaseJudge, JudgeResult
from evalforge.models.test_case import TestCase


class RetrievalCheckJudge(BaseJudge):
    """Judge that verifies the correct documents were retrieved.

    Checks whether the response includes references to or content
    from the expected set of documents.
    """

    def judge(self, test_case: TestCase, response: str) -> JudgeResult:
        """Evaluate whether the expected documents were retrieved.

        Args:
            test_case: The test case with expected documents.
            response: The actual AI response to check.

        Returns:
            JudgeResult with retrieval match ratio.
        """
        expected_data = test_case.expected or {}
        expected_docs: list[str] = (
            expected_data.get("documents", []) if isinstance(expected_data, dict) else []
        )

        if not expected_docs:
            return JudgeResult(
                passed=True,
                score=1.0,
                details={"message": "No documents required"},
            )

        retrieved = self._check_retrieval_list(expected_docs, response)
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
            },
        )

    def _check_retrieval_list(
        self, expected_docs: list[str], response: str
    ) -> dict[str, list[str]]:
        """Check which expected documents are referenced in the response.

        Uses flexible matching that handles partial document names
        and common file reference formats.

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
