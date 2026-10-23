"""Deterministic trusted-source contracts, deliberately not general entailment."""

from __future__ import annotations

from typing import Any

from evalforge.judges.base import BaseJudge, JudgeResult
from evalforge.models.test_case import TestCase

METHOD = "trusted_source_whole_answer_contract"
VERSION = "1"


def _result(outcome: str, message: str) -> JudgeResult:
    return JudgeResult(
        passed=outcome == "passed",
        score=1.0 if outcome == "passed" else 0.0,
        details={
            "outcome": outcome,
            "message": message,
            "method": METHOD,
            "version": VERSION,
            "quality_validated": False,
        },
    )


class EvidenceSupportJudge(BaseJudge):
    """Check full answers and exact approved claim/source/version/quote links.

    The suite is the trusted authority. Source text supplied by an evaluated
    application is compared byte-for-byte with it, never trusted on its own.
    Only explicitly enumerated whole answers are assessable; a quotation's
    presence alone is never treated as proof that an arbitrary claim follows.
    """

    def judge(self, test_case: TestCase, response: str) -> JudgeResult:
        """Text-only callers cannot establish retrieved-source provenance."""
        return _result("indeterminate", "Structured saved evidence is required")

    def judge_record(self, test_case: TestCase, record: dict[str, Any]) -> JudgeResult:  # noqa: C901
        """Evaluate one validated saved record against its trusted suite contract."""
        provenance = record.get("provenance", {})
        if provenance.get("origin", "unknown") == "unknown":
            return _result("indeterminate", "Saved response origin is unknown")
        if any(
            not isinstance(provenance.get(field), str)
            or provenance[field] in {"", "unknown"}
            for field in ("dataset_revision", "label_origin")
        ):
            return _result(
                "indeterminate",
                "Required dataset_revision or label_origin provenance is unknown",
            )
        if (
            provenance.get("evaluation_mode") == "sim"
            or provenance.get("quality_scoring") == "simulated"
        ):
            return _result(
                "indeterminate",
                "Simulated quality scoring is ineligible for a strict gate",
            )
        expected = test_case.expected if isinstance(test_case.expected, dict) else {}
        contract = expected.get("answer_contract")
        if not isinstance(contract, dict):
            return _result(
                "indeterminate",
                "No whole-answer contract; freeform entailment is unassessed",
            )
        canonical = {
            (s["id"], s["version"]): s["content"] for s in expected.get("sources", [])
        }
        retrieved = {
            (s["id"], s["version"]): s["content"] for s in record["retrieved_sources"]
        }
        for identity, content in retrieved.items():
            if identity not in canonical or canonical[identity] != content:
                return _result(
                    "failed",
                    "Retrieved source identity, version, or content differs "
                    "from trusted source",
                )
        claims = contract.get("claims", [])
        approved_links = {
            (c["text"], c["source_id"], c["source_version"], c["quote"]) for c in claims
        }
        observed_links = set()
        for citation in record["citations"]:
            identity = (citation["source_id"], citation["source_version"])
            link = (citation["claim"], *identity, citation["quote"])
            if (
                identity not in retrieved
                or citation["quote"] not in retrieved[identity]
            ):
                return _result(
                    "failed",
                    "Citation has no matching retrieved source/version/passage",
                )
            if link not in approved_links:
                return _result(
                    "failed", "Citation is not an approved claim-to-source support link"
                )
            observed_links.add(link)
        if observed_links != approved_links:
            return _result("failed", "Required trusted claim support is missing")
        answer = record["answer"]
        if answer not in contract["accepted_answers"]:
            if contract.get("exhaustive", False):
                return _result(
                    "failed",
                    "Whole answer violates the exhaustive answer/refusal contract",
                )
            return _result(
                "indeterminate",
                "Answer requires entailment review outside the enumerated contract",
            )
        return _result(
            "passed", "Whole answer and all trusted evidence links satisfy the contract"
        )
