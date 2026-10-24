"""Additive API views over full reports; absent historical evidence stays unknown."""

from __future__ import annotations

import json
from typing import Any


def run_view(row: dict[str, Any]) -> dict[str, Any]:
    """Preserve every legacy storage key and expose canonical case inspection."""
    report = json.loads(row["report_json"])
    metadata = report.get("metadata", {})
    cases = []
    for result in report.get("results", []):
        evidence = result.get("backend_metadata", {})
        details = result.get("judge_details", {})
        passed = result.get("passed")
        outcome = result.get("outcome") or (
            "error"
            if result.get("error")
            else "passed"
            if passed is True
            else "failed"
            if passed is False
            else "unknown"
        )
        cases.append(
            {
                "id": result.get("test_case_id"),
                "name": result.get("test_case_name"),
                "input": evidence.get("input"),
                "expected": evidence.get("expected"),
                "actual": result.get("actual_response"),
                "outcome": outcome,
                "passed": passed,
                "score": result.get("score"),
                "category": evidence.get("category"),
                "tags": evidence.get("tags", []),
                "judges": [
                    {
                        "judge": details.get("method", "unknown"),
                        "passed": passed,
                        "score": result.get("score"),
                        "message": details.get("message", result.get("error")),
                        "details": details,
                    }
                ],
                "retrieved_sources": evidence.get("retrieved_sources", []),
                "citations": evidence.get("citations", []),
                "authoritative_sources": evidence.get("authoritative_sources", []),
                "provenance": evidence.get("provenance")
                or {"origin": "unknown", "judge_method": "unknown"},
            }
        )
    return {
        **row,
        "cases": cases,
        "gate": metadata.get("gate"),
        "provenance": metadata.get("provenance")
        or {"origin": "unknown", "judge_method": "unknown"},
        "dataset_revision": metadata.get("dataset_revision"),
        "suite_contract": metadata.get("suite_contract"),
    }


def compare_view(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Align by stable IDs only when dataset and suite contracts are known equal."""
    left, right = run_view(a), run_view(b)
    a_summary = json.loads(a["report_json"]).get("summary", {})
    b_summary = json.loads(b["report_json"]).get("summary", {})
    comparable = bool(
        left["dataset_revision"]
        and left["suite_contract"]
        and left["dataset_revision"] == right["dataset_revision"]
        and left["suite_contract"] == right["suite_contract"]
    )
    reason = (
        "Matching dataset revision and suite contract"
        if comparable
        else "Dataset revision or suite contract is missing or differs"
    )
    before = {case["id"]: case for case in left["cases"]}
    after = {case["id"]: case for case in right["cases"]}
    deltas = []
    for case_id in sorted(before.keys() | after.keys(), key=str):
        baseline, candidate = before.get(case_id), after.get(case_id)
        if baseline is None:
            change = "added"
        elif candidate is None:
            change = "removed"
        elif not comparable:
            change = "not_comparable"
        elif (
            baseline["outcome"] == candidate["outcome"]
            and baseline["score"] == candidate["score"]
        ):
            change = "unchanged"
        elif baseline["outcome"] == "passed" and candidate["outcome"] == "failed":
            change = "regressed"
        elif baseline["outcome"] == "failed" and candidate["outcome"] == "passed":
            change = "improved"
        else:
            change = "changed"
        deltas.append(
            {
                "case_id": case_id,
                "change": change,
                "baseline": baseline,
                "candidate": candidate,
            }
        )
    return {
        "run_a_id": a["id"],
        "run_b_id": b["id"],
        "pass_rate_delta": b_summary.get("pass_rate", 0.0)
        - a_summary.get("pass_rate", 0.0),
        "avg_score_delta": b_summary.get("avg_score", 0.0)
        - a_summary.get("avg_score", 0.0),
        "comparable": comparable,
        "reason": reason,
        "case_deltas": deltas,
    }
