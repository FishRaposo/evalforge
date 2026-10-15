"""Citation and retrieval judges must reject "same answer, wrong source" (EF-P0-2).

Each case below has an answer whose content is right; only the source is wrong
or missing. The historical substring/word-overlap matching passed all of them.
"""

from __future__ import annotations

from typing import Any

import pytest

from evalforge.backends.base import BackendResponse, BaseBackend
from evalforge.judges.citation_check import CitationCheckJudge
from evalforge.judges.retrieval_check import RetrievalCheckJudge
from evalforge.judges.source_ids import normalize_source_id, resolve_match_mode
from evalforge.models.test_case import TestCase, TestCaseType
from evalforge.runners.agent_runner import AgentRunner
from evalforge.runners.rag_runner import RAGRunner

ANSWER = "Customers can return items within 30 days for a full refund."


def _cite_case(sources: list[str], metadata: dict[str, Any] | None = None) -> TestCase:
    return TestCase(
        id="cite",
        name="cite",
        type=TestCaseType.MUST_CITE,
        input="What is the refund window?",
        expected={"sources": sources},
        metadata=metadata or {},
    )


def _retrieve_case(
    documents: list[str], metadata: dict[str, Any] | None = None
) -> TestCase:
    return TestCase(
        id="ret",
        name="ret",
        type=TestCaseType.MUST_RETRIEVE,
        input="What is the refund window?",
        expected={"documents": documents},
        metadata=metadata or {},
    )


class _StaticBackend(BaseBackend):
    def __init__(self, content: str, metadata: dict[str, Any]) -> None:
        self._content = content
        self._metadata = metadata

    async def query(
        self, prompt: str, context: dict[str, Any] | None = None
    ) -> BackendResponse:
        return BackendResponse(content=self._content, metadata=self._metadata)

    async def health_check(self) -> bool:
        return True


class TestCitationWrongSource:
    @pytest.mark.parametrize(
        "response",
        [
            f"{ANSWER} [Refund Policy 2023]",
            f"{ANSWER} (Refund Policy 2023)",
            f'{ANSWER} Source: "Refund Policy 2023".',
        ],
    )
    def test_wrong_year_fails(self, response: str) -> None:
        result = CitationCheckJudge().judge(
            _cite_case(["Refund Policy 2024"]), response
        )
        assert result.passed is False
        assert result.score == 0.0
        assert result.details["unmatched_sources"] == ["Refund Policy 2024"]

    def test_wrong_version_fails(self) -> None:
        result = CitationCheckJudge().judge(
            _cite_case(["refund_policy_v2.md"]), f"{ANSWER} [refund_policy_v1.md]"
        )
        assert result.passed is False

    def test_no_document_reference_fails(self) -> None:
        response = (
            "Under our 2024 refund policy, customers can return items in 30 days."
        )
        result = CitationCheckJudge().judge(
            _cite_case(["Refund Policy 2024"]), response
        )
        assert result.passed is False
        assert result.details["found_citations"] == []

    def test_prose_mention_is_not_a_citation(self) -> None:
        result = CitationCheckJudge().judge(
            _cite_case(["NASA Climate Data"]),
            "According to NASA Climate Data, temperatures are rising.",
        )
        assert result.passed is False

    def test_partial_credit_when_one_of_two_is_wrong(self) -> None:
        result = CitationCheckJudge().judge(
            _cite_case(["Refund Policy 2024", "Customer Rights"]),
            f"{ANSWER} [Refund Policy 2023; Customer Rights]",
        )
        assert result.passed is False
        assert result.score == 0.5
        assert result.details["matched_sources"] == ["Customer Rights"]


class TestCitationCorrectSource:
    @pytest.mark.parametrize(
        "response",
        [
            f"{ANSWER} [Refund Policy 2024]",
            f"{ANSWER} [refund policy 2024]",
            f"{ANSWER} (Refund Policy 2024)",
            f'{ANSWER} See "Refund Policy 2024".',
            f"{ANSWER} “Refund Policy 2024”",
            f"{ANSWER} [Source: Refund Policy 2024]",
            f"{ANSWER} [see Refund Policy 2024]",
        ],
    )
    def test_exact_citation_passes(self, response: str) -> None:
        result = CitationCheckJudge().judge(
            _cite_case(["Refund Policy 2024"]), response
        )
        assert result.passed is True
        assert result.score == 1.0
        assert result.details["match_mode"] == "strict"

    def test_normalized_id_passes(self) -> None:
        result = CitationCheckJudge().judge(
            _cite_case(["refund_policy_v2.md"]), f"{ANSWER} [Refund-Policy v2.MD]"
        )
        assert result.passed is True

    def test_multiple_sources_in_one_marker(self) -> None:
        result = CitationCheckJudge().judge(
            _cite_case(["CDC", "WHO"]), "Vaccines are effective [CDC; WHO]."
        )
        assert result.passed is True

    def test_source_containing_a_comma(self) -> None:
        result = CitationCheckJudge().judge(
            _cite_case(["Smith, 2020"]), "Effect confirmed (Smith, 2020)."
        )
        assert result.passed is True


class TestCitationFuzzyOptIn:
    def test_fuzzy_restores_prose_matching(self) -> None:
        result = CitationCheckJudge().judge(
            _cite_case(["NASA Climate Data"], {"match": "fuzzy"}),
            "According to NASA Climate Data, temperatures are rising.",
        )
        assert result.passed is True
        assert result.details["match_mode"] == "fuzzy"

    def test_fuzzy_is_lenient_about_year(self) -> None:
        # The behaviour strict mode exists to prevent; only reachable by opt-in.
        result = CitationCheckJudge().judge(
            _cite_case(["Refund Policy 2024"], {"match": "fuzzy"}),
            f"{ANSWER} [Refund Policy 2023]",
        )
        assert result.passed is True

    def test_unknown_mode_fails_loudly(self) -> None:
        result = CitationCheckJudge().judge(
            _cite_case(["Refund Policy 2024"], {"match": "loose"}),
            f"{ANSWER} [Refund Policy 2024]",
        )
        assert result.passed is False
        assert "Unknown match mode" in result.details["error"]


class TestRetrievalFromAnswerText:
    def test_wrong_version_fails(self) -> None:
        result = RetrievalCheckJudge().judge(
            _retrieve_case(["refund_policy_v2.md"]),
            f"{ANSWER} (from refund_policy_v1.md)",
        )
        assert result.passed is False
        assert result.details["missing_documents"] == ["refund_policy_v2.md"]
        assert result.details["evidence"] == "response_text"

    def test_no_document_reference_fails(self) -> None:
        result = RetrievalCheckJudge().judge(
            _retrieve_case(["refund_policy_v2.md"]),
            "Our refund policy (v2) allows returns within 30 days.",
        )
        assert result.passed is False

    def test_identifier_must_be_bounded(self) -> None:
        result = RetrievalCheckJudge().judge(
            _retrieve_case(["policy.pdf", "refund_policy_v2.md"]),
            "See old_policy.pdf and refund_policy_v2.mdx.",
        )
        assert result.passed is False
        assert result.score == 0.0

    def test_exact_identifier_passes(self) -> None:
        result = RetrievalCheckJudge().judge(
            _retrieve_case(["refund_policy_v2.md"]),
            f"{ANSWER} Source: docs/Refund_Policy_V2.md.",
        )
        assert result.passed is True

    def test_fuzzy_opt_in_restores_word_overlap(self) -> None:
        result = RetrievalCheckJudge().judge(
            _retrieve_case(["refund_policy_v2.md"], {"match": "fuzzy"}),
            "Our refund policy allows returns within 30 days.",
        )
        assert result.passed is True
        assert result.details["match_mode"] == "fuzzy"


class TestRetrievalFromRetrievedIds:
    def test_wrong_document_retrieved_fails_even_if_answer_names_right_one(
        self,
    ) -> None:
        result = RetrievalCheckJudge().judge_with_context(
            _retrieve_case(["refund_policy_v2.md"]),
            f"{ANSWER} [refund_policy_v2.md]",
            {"retrieved_ids": ["refund_policy_v1.md", "shipping.md"]},
        )
        assert result.passed is False
        assert result.details["evidence"] == "retrieved_ids"

    def test_right_document_retrieved_passes_without_text_reference(self) -> None:
        result = RetrievalCheckJudge().judge_with_context(
            _retrieve_case(["refund_policy_v2.md"]),
            ANSWER,
            {"retrieved_ids": ["shipping.md", "Refund_Policy_V2.md"]},
        )
        assert result.passed is True
        assert result.details["retrieved_ids"] == ["shipping.md", "Refund_Policy_V2.md"]

    def test_empty_retrieval_fails(self) -> None:
        result = RetrievalCheckJudge().judge_with_context(
            _retrieve_case(["refund_policy_v2.md"]),
            f"{ANSWER} refund_policy_v2.md",
            {"retrieved_ids": []},
        )
        assert result.passed is False

    def test_fuzzy_does_not_loosen_structured_ids(self) -> None:
        result = RetrievalCheckJudge().judge_with_context(
            _retrieve_case(["refund_policy_v2.md"], {"match": "fuzzy"}),
            ANSWER,
            {"retrieved_ids": ["refund_policy_v1.md"]},
        )
        assert result.passed is False

    def test_malformed_retrieved_ids_fail_loudly(self) -> None:
        result = RetrievalCheckJudge().judge_with_context(
            _retrieve_case(["refund_policy_v2.md"]),
            ANSWER,
            {"retrieved_ids": "refund_policy_v2.md"},
        )
        assert result.passed is False
        assert "retrieved_ids" in result.details["error"]

    def test_partial_retrieval_scores_ratio(self) -> None:
        result = RetrievalCheckJudge().judge_with_context(
            _retrieve_case(["a.md", "b.md"]), ANSWER, {"retrieved_ids": ["a.md"]}
        )
        assert result.passed is False
        assert result.score == 0.5


class TestRunnersPassRetrievedIds:
    async def test_rag_runner_scores_from_backend_retrieved_ids(self) -> None:
        backend = _StaticBackend(
            f"{ANSWER} [refund_policy_v2.md]",
            {"retrieved_ids": ["refund_policy_v1.md"]},
        )
        result = await RAGRunner(backend).run(_retrieve_case(["refund_policy_v2.md"]))
        assert result.passed is False
        assert result.judge_details["evidence"] == "retrieved_ids"

    async def test_agent_runner_scores_from_backend_retrieved_ids(self) -> None:
        backend = _StaticBackend(ANSWER, {"retrieved_ids": ["refund_policy_v2.md"]})
        result = await AgentRunner(backend).run(_retrieve_case(["refund_policy_v2.md"]))
        assert result.passed is True
        assert result.judge_details["evidence"] == "retrieved_ids"


class TestSourceIds:
    def test_normalization_keeps_years_and_versions(self) -> None:
        assert normalize_source_id("Refund_Policy-v2.MD") == "refund policy v2 md"
        assert normalize_source_id("Refund Policy 2023") != normalize_source_id(
            "Refund Policy 2024"
        )

    def test_default_mode_is_strict(self) -> None:
        assert resolve_match_mode(None) == "strict"
        assert resolve_match_mode({}) == "strict"
        assert resolve_match_mode({"match": "FUZZY"}) == "fuzzy"
