"""Saved-response execution with complete evidence and explicit error outcomes."""

from __future__ import annotations

from typing import Any

from evalforge.backends.saved import CASE_ID_CONTEXT_KEY, SavedResponseBackend
from evalforge.judges.evidence_support import EvidenceSupportJudge
from evalforge.judges.registry import get_judge
from evalforge.models.test_case import TestCase, TestCaseType
from evalforge.models.test_result import TestResult
from evalforge.runners.base import BaseRunner


class SavedRunner(BaseRunner):
    """Keep saved evidence on every result, including a failed judge execution."""

    def __init__(self, backend: SavedResponseBackend, *, strict: bool = True) -> None:
        super().__init__(backend)
        self.strict = strict

    async def run(self, test_case: TestCase) -> TestResult:
        expected = test_case.expected
        metadata: dict[str, Any] = {
            "input": test_case.input,
            "expected": expected,
            "tags": test_case.tags,
            "category": test_case.metadata.get("category", "unknown"),
            "authoritative_sources": expected.get("sources", [])
            if isinstance(expected, dict)
            else [],
        }
        answer = ""
        try:
            response = await self._backend.query(
                test_case.input, {CASE_ID_CONTEXT_KEY: test_case.id}
            )
            answer = response.content
            metadata.update(response.metadata)
            if test_case.type == TestCaseType.EVIDENCE_SUPPORT:
                judged = EvidenceSupportJudge().judge_record(
                    test_case, response.metadata
                )
            else:
                judged = get_judge(test_case.type).judge(test_case, answer)
                judged.details.setdefault(
                    "assessment",
                    {
                        "method": test_case.type.value,
                        "version": "1",
                        "quality_validated": False,
                    },
                )
                if self.strict:
                    judged.passed = False
                    judged.score = 0
                    judged.details.update(
                        outcome="indeterminate",
                        message="Legacy judge is not a trusted evidence contract",
                        method="legacy_unvalidated",
                    )
            outcome = judged.details.get(
                "outcome", "passed" if judged.passed else "failed"
            )
            return TestResult(
                test_case_id=test_case.id,
                test_case_name=test_case.name,
                passed=judged.passed,
                score=judged.score,
                actual_response=answer,
                outcome=outcome,
                judge_details=judged.details,
                backend_metadata=metadata,
                error=None,
            )
        except Exception as exc:
            return TestResult(
                test_case_id=test_case.id,
                test_case_name=test_case.name,
                passed=False,
                score=0,
                actual_response=answer,
                outcome="error",
                error=str(exc),
                judge_details={"outcome": "error", "message": str(exc)},
                backend_metadata=metadata,
            )
