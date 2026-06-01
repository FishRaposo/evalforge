"""RAG test runner for single-turn question-answer evaluation."""

from __future__ import annotations

import time
from typing import Any

from evalforge.backends.base import BaseBackend
from evalforge.judges.base import BaseJudge
from evalforge.judges.registry import _JUDGE_MAP
from evalforge.models.test_case import TestCase, TestCaseType
from evalforge.models.test_result import TestResult
from evalforge.runners.base import BaseRunner


class RAGRunner(BaseRunner):
    """Runner for RAG-style single-turn question-answer evaluation.

    Sends each test case's input to the backend, receives a response,
    and uses the appropriate judge to evaluate the response quality.

    Args:
        backend: The AI backend to use for queries.
    """

    def __init__(self, backend: BaseBackend) -> None:
        """Initialize the RAG runner.

        Args:
            backend: The backend instance for making AI queries.
        """
        super().__init__(backend)
        self._judges: dict[TestCaseType, BaseJudge] = {
            tt: judge_cls() for tt, judge_cls in _JUDGE_MAP.items()
        }

    async def run(self, test_case: TestCase) -> TestResult:
        """Execute a single RAG test case.

        Sends the input to the backend, judges the response, and
        returns a TestResult with the evaluation outcome.

        Args:
            test_case: The test case to execute.

        Returns:
            The evaluation result.
        """
        start = time.monotonic()

        try:
            response = await self._run_single(test_case)
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return self._create_result(
                test_case=test_case,
                passed=False,
                score=0.0,
                response="",
                error=str(exc),
                elapsed_ms=elapsed,
            )

        elapsed = (time.monotonic() - start) * 1000
        judge = self._judges.get(test_case.type)

        if judge is None:
            return self._create_result(
                test_case=test_case,
                passed=False,
                score=0.0,
                response=response.content,
                error=f"No judge found for type: {test_case.type}",
                elapsed_ms=elapsed,
            )

        judge_result = judge.judge(test_case, response.content)
        return self._create_result(
            test_case=test_case,
            passed=judge_result.passed,
            score=judge_result.score,
            response=response.content,
            judge_details=judge_result.details,
            elapsed_ms=elapsed,
        )

    async def _run_single(self, test_case: TestCase) -> Any:
        """Execute a single test case against the backend.

        Args:
            test_case: The test case to execute.

        Returns:
            The backend response.
        """
        context = test_case.metadata.get("context")
        return await self._backend.query(test_case.input, context)
