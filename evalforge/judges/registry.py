"""Central judge registry — maps TestCaseType to judge classes."""

from __future__ import annotations

from evalforge.judges.base import BaseJudge
from evalforge.judges.citation_check import CitationCheckJudge
from evalforge.judges.exact_match import ExactMatchJudge
from evalforge.judges.forbidden_content import ForbiddenContentJudge
from evalforge.judges.refusal_check import RefusalCheckJudge
from evalforge.judges.retrieval_check import RetrievalCheckJudge
from evalforge.judges.semantic_match import SemanticMatchJudge
from evalforge.judges.structured_output import StructuredOutputJudge
from evalforge.models.test_case import TestCaseType

_JUDGE_MAP: dict[TestCaseType, type[BaseJudge]] = {
    TestCaseType.EXACT_ANSWER: ExactMatchJudge,
    TestCaseType.SEMANTIC_ANSWER: SemanticMatchJudge,
    TestCaseType.MUST_CITE: CitationCheckJudge,
    TestCaseType.MUST_REFUSE: RefusalCheckJudge,
    TestCaseType.MUST_RETRIEVE: RetrievalCheckJudge,
    TestCaseType.FORBIDDEN_CONTENT: ForbiddenContentJudge,
    TestCaseType.STRUCTURED_OUTPUT: StructuredOutputJudge,
}


def get_judge(test_case_type: TestCaseType) -> BaseJudge:
    """Return a fresh judge instance for the given test case type.

    Args:
        test_case_type: The evaluation type.

    Returns:
        A new judge instance.

    Raises:
        ValueError: If the type has no registered judge.
    """
    judge_cls = _JUDGE_MAP.get(test_case_type)
    if judge_cls is None:
        raise ValueError(f"No judge registered for type: {test_case_type}")
    return judge_cls()


def register_judge(test_case_type: TestCaseType, judge_cls: type[BaseJudge]) -> None:
    """Register a custom judge class for a test case type.

    Args:
        test_case_type: The type to register for.
        judge_cls: The judge class to instantiate.
    """
    _JUDGE_MAP[test_case_type] = judge_cls


def list_judges() -> dict[TestCaseType, type[BaseJudge]]:
    """Return a copy of the current judge mapping."""
    return dict(_JUDGE_MAP)
