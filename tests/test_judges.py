"""Tests for evaluation judges."""

from __future__ import annotations

from evalforge.judges.exact_match import ExactMatchJudge
from evalforge.judges.semantic_match import SemanticMatchJudge
from evalforge.judges.citation_check import CitationCheckJudge
from evalforge.judges.refusal_check import RefusalCheckJudge
from evalforge.judges.retrieval_check import RetrievalCheckJudge
from evalforge.judges.forbidden_content import ForbiddenContentJudge
from evalforge.models.test_case import TestCase, TestCaseType


class TestExactMatchJudge:
    """Tests for ExactMatchJudge."""

    def test_exact_match_pass(self) -> None:
        """Should pass when response matches expected exactly."""
        judge = ExactMatchJudge()
        test_case = TestCase(
            id="em-001",
            name="Exact match test",
            type=TestCaseType.EXACT_ANSWER,
            input="What is the capital of France?",
            expected="Paris",
        )

        result = judge.judge(test_case, "Paris")

        assert result.passed is True
        assert result.score == 1.0

    def test_exact_match_fail(self) -> None:
        """Should fail when response differs from expected."""
        judge = ExactMatchJudge()
        test_case = TestCase(
            id="em-002",
            name="Exact match fail",
            type=TestCaseType.EXACT_ANSWER,
            input="What is the capital of France?",
            expected="Paris",
        )

        result = judge.judge(test_case, "London")

        assert result.passed is False
        assert result.score == 0.0

    def test_exact_match_case_insensitive(self) -> None:
        """Should pass regardless of case differences."""
        judge = ExactMatchJudge()
        test_case = TestCase(
            id="em-003",
            name="Case insensitive",
            type=TestCaseType.EXACT_ANSWER,
            input="Question",
            expected="Paris",
        )

        result = judge.judge(test_case, "paris")

        assert result.passed is True

    def test_exact_match_whitespace_normalization(self) -> None:
        """Should normalize whitespace before comparing."""
        judge = ExactMatchJudge()
        test_case = TestCase(
            id="em-004",
            name="Whitespace test",
            type=TestCaseType.EXACT_ANSWER,
            input="Question",
            expected="hello world",
        )

        result = judge.judge(test_case, "  Hello   World  ")

        assert result.passed is True


class TestSemanticMatchJudge:
    """Tests for SemanticMatchJudge."""

    def test_semantic_match_pass(self) -> None:
        """Should pass when similarity exceeds threshold."""
        judge = SemanticMatchJudge(threshold=0.3)
        test_case = TestCase(
            id="sm-001",
            name="Semantic pass",
            type=TestCaseType.SEMANTIC_ANSWER,
            input="What is gravity?",
            expected="Gravity is a fundamental force that attracts objects with mass",
        )

        result = judge.judge(test_case, "Gravity is a fundamental force that attracts objects with mass toward each other")

        assert result.passed is True
        assert result.score > 0.3

    def test_semantic_match_threshold(self) -> None:
        """Should respect custom threshold from test metadata."""
        judge = SemanticMatchJudge(threshold=0.9)
        test_case = TestCase(
            id="sm-002",
            name="High threshold",
            type=TestCaseType.SEMANTIC_ANSWER,
            input="Question",
            expected="The quick brown fox jumps over the lazy dog",
            metadata={"threshold": 0.3},
        )

        result = judge.judge(test_case, "The quick brown fox jumps")

        assert result.score < 0.9
        assert result.details["threshold"] == 0.3


class TestCitationCheckJudge:
    """Tests for CitationCheckJudge."""

    def test_citation_check_found(self) -> None:
        """Should pass when all required sources are cited."""
        judge = CitationCheckJudge()
        test_case = TestCase(
            id="cc-001",
            name="Citation found",
            type=TestCaseType.MUST_CITE,
            input="Climate change question",
            expected={"sources": ["NASA Climate Data"]},
        )

        result = judge.judge(test_case, "According to NASA Climate Data, temperatures are rising.")

        assert result.passed is True
        assert result.score == 1.0

    def test_citation_check_missing(self) -> None:
        """Should fail when required sources are missing."""
        judge = CitationCheckJudge()
        test_case = TestCase(
            id="cc-002",
            name="Citation missing",
            type=TestCaseType.MUST_CITE,
            input="Climate question",
            expected={"sources": ["IPCC AR6 Report", "NASA Climate Data"]},
        )

        result = judge.judge(test_case, "Temperatures have been rising steadily.")

        assert result.passed is False
        assert "unmatched_sources" in result.details


class TestRefusalCheckJudge:
    """Tests for RefusalCheckJudge."""

    def test_refusal_detected(self) -> None:
        """Should pass when refusal is correctly detected."""
        judge = RefusalCheckJudge()
        test_case = TestCase(
            id="rc-001",
            name="Refuse detected",
            type=TestCaseType.MUST_REFUSE,
            input="Harmful request",
            expected=None,
        )

        result = judge.judge(test_case, "I cannot assist with that request.")

        assert result.passed is True
        assert result.score == 1.0

    def test_refusal_not_detected(self) -> None:
        """Should fail when refusal is expected but not detected."""
        judge = RefusalCheckJudge()
        test_case = TestCase(
            id="rc-002",
            name="No refusal",
            type=TestCaseType.MUST_REFUSE,
            input="Harmful request",
            expected=None,
        )

        result = judge.judge(test_case, "Here is how you would do that.")

        assert result.passed is False
        assert result.score == 0.0

    def test_refusal_various_phrases(self) -> None:
        """Should detect various refusal phrase patterns."""
        judge = RefusalCheckJudge()
        test_case = TestCase(
            id="rc-003",
            name="Various refusals",
            type=TestCaseType.MUST_REFUSE,
            input="Bad request",
            expected=None,
        )

        refusals = [
            "I'm not able to help with that.",
            "I must decline this request.",
            "I'm unable to provide that information.",
            "I won't assist with that.",
        ]

        for refusal in refusals:
            result = judge.judge(test_case, refusal)
            assert result.passed is True, f"Failed to detect refusal: {refusal}"


class TestRetrievalCheckJudge:
    """Tests for RetrievalCheckJudge."""

    def test_retrieval_found(self) -> None:
        """Should pass when expected documents are referenced."""
        judge = RetrievalCheckJudge()
        test_case = TestCase(
            id="ret-001",
            name="Document retrieved",
            type=TestCaseType.MUST_RETRIEVE,
            input="Policy question",
            expected={"documents": ["refund_policy_v3.pdf"]},
        )

        result = judge.judge(test_case, "According to refund_policy_v3.pdf, customers can return items within 30 days.")

        assert result.passed is True

    def test_retrieval_missing(self) -> None:
        """Should fail when expected documents are not referenced."""
        judge = RetrievalCheckJudge()
        test_case = TestCase(
            id="ret-002",
            name="Document missing",
            type=TestCaseType.MUST_RETRIEVE,
            input="Policy question",
            expected={"documents": ["refund_policy_v3.pdf", "customer_rights.pdf"]},
        )

        result = judge.judge(test_case, "Our policy allows returns.")

        assert result.passed is False
        assert len(result.details["missing_documents"]) > 0


class TestForbiddenContentJudge:
    """Tests for ForbiddenContentJudge."""

    def test_forbidden_content_detected(self) -> None:
        """Should fail when forbidden content is found."""
        judge = ForbiddenContentJudge()
        test_case = TestCase(
            id="fc-001",
            name="Forbidden found",
            type=TestCaseType.FORBIDDEN_CONTENT,
            input="Medical question",
            expected={"forbidden": ["take aspirin", "specific dosage"]},
        )

        result = judge.judge(test_case, "You should take aspirin at a specific dosage of 500mg.")

        assert result.passed is False
        assert result.score == 0.0
        assert len(result.details["violations"]) > 0

    def test_forbidden_content_clean(self) -> None:
        """Should pass when no forbidden content is present."""
        judge = ForbiddenContentJudge()
        test_case = TestCase(
            id="fc-002",
            name="Clean response",
            type=TestCaseType.FORBIDDEN_CONTENT,
            input="Medical question",
            expected={"forbidden": ["prescribe medication", "specific dosage"]},
        )

        result = judge.judge(test_case, "Please consult a healthcare professional for medical advice.")

        assert result.passed is True
        assert result.score == 1.0
        assert len(result.details["violations"]) == 0

    def test_forbidden_no_patterns(self) -> None:
        """Should pass when no forbidden patterns are defined."""
        judge = ForbiddenContentJudge()
        test_case = TestCase(
            id="fc-003",
            name="No patterns",
            type=TestCaseType.FORBIDDEN_CONTENT,
            input="Question",
            expected={},
        )

        result = judge.judge(test_case, "Any response here.")

        assert result.passed is True
