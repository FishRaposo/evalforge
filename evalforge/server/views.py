"""Additive API views over full reports; absent historical evidence stays unknown."""

from __future__ import annotations

import json
from typing import Any


def validate_history_report(report: Any) -> None:
    """Validate containers the read surface consumes, retaining legacy/extra keys."""
    if not isinstance(report, dict):
        raise ValueError("Report must be an object")
    for field in ("summary", "metadata"):
        if not isinstance(report.get(field, {}), dict):
            raise ValueError(f"Report {field} must be an object")
    _validate_storage_scalars(report)
    for field in ("pass_rate", "avg_score"):
        value = report.get("summary", {}).get(field, 0.0)
        if (
            isinstance(value, bool)
            or not isinstance(value, (float, int))
            or not 0 <= value <= 1
        ):
            raise ValueError(f"Summary {field} must be finite numeric data")
    metadata = report.get("metadata", {})
    for field in ("provenance", "gate"):
        if (
            field in metadata
            and metadata[field] is not None
            and not isinstance(metadata[field], dict)
        ):
            raise ValueError(f"Metadata {field} must be an object")
    results = report.get("results", [])
    if not isinstance(results, list):
        raise ValueError("Report results must be a list")
    for result in results:
        _validate_history_case(result)


def _validate_storage_scalars(report: dict[str, Any]) -> None:
    if "suite_name" in report and not isinstance(report["suite_name"], str):
        raise ValueError("Suite name must be text")
    for container in (report, report.get("metadata", {})):
        backend = container.get("backend")
        if backend is not None and not isinstance(backend, str):
            raise ValueError("Backend must be text or null")
    summary = report.get("summary", {})
    for field in ("total", "total_tests", "passed", "failed"):
        value = summary.get(field, 0)
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 2**63 - 1
        ):
            raise ValueError(f"Summary {field} must be a nonnegative SQLite integer")


def _validate_history_case(result: Any) -> None:
    if not isinstance(result, dict):
        raise ValueError("Each result must be an object")
    if not isinstance(result.get("test_case_id", ""), (str, int)):
        raise ValueError("Case identity must be scalar text or a legacy integer")
    for field in ("backend_metadata", "judge_details"):
        if not isinstance(result.get(field, {}), dict):
            raise ValueError(f"Result {field} must be an object")
    evidence = result.get("backend_metadata", {})
    if not isinstance(evidence.get("provenance", {}), dict):
        raise ValueError("Evidence provenance must be an object")
    for field in ("retrieved_sources", "citations", "authoritative_sources"):
        items = evidence.get(field, [])
        if not isinstance(items, list) or any(
            not isinstance(item, dict) for item in items
        ):
            raise ValueError(f"Evidence {field} must be a list of objects")


def _read_report(row: dict[str, Any]) -> dict[str, Any]:
    try:
        report = json.loads(row["report_json"])
        validate_history_report(report)
        return report
    except (ValueError, TypeError):
        # Preserve the original stored bytes; an unreadable legacy row is not a pass.
        return {
            "results": [
                {
                    "test_case_id": "unavailable-legacy-report",
                    "test_case_name": "Stored report cannot be inspected",
                    "passed": False,
                    "score": 0,
                    "outcome": "error",
                    "error": "Malformed legacy report; "
                    "original stored JSON is retained",
                }
            ]
        }


def run_view(row: dict[str, Any]) -> dict[str, Any]:
    """Preserve every legacy storage key and expose canonical case inspection."""
    report = _read_report(row)
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
    a_summary = _read_report(a).get("summary", {})
    b_summary = _read_report(b).get("summary", {})
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
