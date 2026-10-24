"""One side-effect-free saved evaluation service shared by CLI and local API."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from evalforge.backends.saved import SavedResponseBackend
from evalforge.evidence import canonical_json_bytes, sha256_bytes, sha256_file
from evalforge.judges.evidence_support import METHOD, VERSION
from evalforge.loader.suite_loader import SuiteLoader
from evalforge.models.report import Report, ReportSummary, immutable_report
from evalforge.models.test_case import TestCaseType, TestSuite
from evalforge.runners.saved_runner import SavedRunner

MAX_SUITE_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class EvaluationOutcome:
    """Completed assessment; callers explicitly choose persistence/report output."""

    report: Report
    exit_code: int


def _check_web_tree(value: Any, seen: set[int] | None = None) -> None:
    """Reject active/file-reference configuration before loading a web suite."""
    seen = seen if seen is not None else set()
    if isinstance(value, (dict, list)):
        if id(value) in seen:
            raise ValueError("Recursive or aliased YAML structures are not supported")
        seen.add(id(value))
    if isinstance(value, dict):
        forbidden = {
            "includes",
            "include",
            "$ref",
            "plugin",
            "plugins",
            "judge_plugin",
            "file",
            "file_path",
            "source_path",
            "path",
            "external_file",
        }
        for key, item in value.items():
            if str(key).lower() in forbidden:
                raise ValueError(
                    "Web suite forbids includes, external file references "
                    f"and plugins: {key}"
                )
            _check_web_tree(item, seen)
    elif isinstance(value, list):
        for item in value:
            _check_web_tree(item, seen)


def _validate_contract(suite: TestSuite) -> None:  # noqa: C901
    for case in suite.test_cases:
        if case.type != TestCaseType.EVIDENCE_SUPPORT:
            continue
        expected = case.expected
        if not isinstance(expected, dict) or not isinstance(
            expected.get("sources"), list
        ):
            raise ValueError(f"Trusted sources must be a list for {case.id}")
        sources: dict[tuple[str, str], str] = {}
        for source in expected["sources"]:
            if not isinstance(source, dict) or any(
                not isinstance(source.get(k), str) or not source[k]
                for k in ("id", "version", "content")
            ):
                raise ValueError(f"Invalid trusted source for {case.id}")
            identity = (source["id"], source["version"])
            if identity in sources:
                raise ValueError(f"Duplicate trusted source for {case.id}")
            sources[identity] = source["content"]
        contract = expected.get("answer_contract")
        if contract is None:
            continue  # Supported input, explicitly unassessable freeform entailment.
        if (
            not isinstance(contract, dict)
            or not isinstance(contract.get("kind"), str)
            or contract.get("kind")
            not in {
                "answer",
                "refusal",
            }
        ):
            raise ValueError(f"Invalid answer contract for {case.id}")
        answers = contract.get("accepted_answers")
        if (
            not isinstance(answers, list)
            or not answers
            or any(not isinstance(a, str) or not a for a in answers)
        ):
            raise ValueError(f"Whole accepted answers required for {case.id}")
        if "exhaustive" in contract and not isinstance(contract["exhaustive"], bool):
            raise ValueError(f"Contract exhaustive must be boolean for {case.id}")
        claims = contract.get("claims", [])
        if not isinstance(claims, list) or (
            contract["kind"] == "answer" and not claims
        ):
            raise ValueError(f"Trusted claims required for answer contract {case.id}")
        for claim in claims:
            if not isinstance(claim, dict) or any(
                not isinstance(claim.get(k), str) or not claim[k]
                for k in ("text", "source_id", "source_version", "quote")
            ):
                raise ValueError(f"Invalid trusted claim for {case.id}")
            content = sources.get((claim["source_id"], claim["source_version"]))
            if content is None or claim["quote"] not in content:
                raise ValueError(
                    f"Trusted claim has no canonical source passage for {case.id}"
                )
            if any(claim["text"] not in answer for answer in answers):
                raise ValueError(f"Accepted answer omits a trusted claim for {case.id}")


def _load_inputs(
    suite_path: Path, response_path: Path, *, web: bool = False
) -> tuple[TestSuite, SavedResponseBackend, dict[str, Any]]:
    if suite_path.stat().st_size > MAX_SUITE_BYTES:
        raise ValueError("Suite exceeds the 2 MiB limit")
    try:
        raw = yaml.safe_load(suite_path.read_text(encoding="utf-8"))
    except (UnicodeError, yaml.YAMLError, RecursionError) as exc:
        raise ValueError(f"Invalid UTF-8 YAML suite: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("Suite must be a YAML mapping")
    # Saved evaluations are self-contained in CLI as well as web imports.
    _check_web_tree(raw)
    suite = TestSuite.model_validate(raw)
    errors = SuiteLoader().validate_suite(suite)
    if errors:
        raise ValueError("; ".join(errors))
    if web and len(suite.test_cases) > 500:
        raise ValueError("Web suite exceeds 500 cases")
    _validate_contract(suite)
    backend = SavedResponseBackend(response_path)
    case_ids = {case.id for case in suite.test_cases}
    if case_ids != set(backend.records):
        raise ValueError(
            "Saved response mapping must match suite case IDs exactly; "
            f"missing={sorted(case_ids - set(backend.records))}, "
            f"extra={sorted(set(backend.records) - case_ids)}"
        )
    revisions = {
        record.provenance.get("dataset_revision", "unknown")
        for record in backend.records.values()
    }
    if len(revisions) != 1 or any(not isinstance(r, str) for r in revisions):
        raise ValueError("Saved response dataset revisions must match")
    revision = next(iter(revisions))
    if revision != "unknown" and "version" in raw and revision != suite.version:
        raise ValueError(
            "Saved response dataset revision differs from pinned suite version"
        )
    origins = {
        record.provenance.get("origin", "unknown")
        for record in backend.records.values()
    }
    origin = next(iter(origins)) if len(origins) == 1 else "unknown"
    label_origins = {
        str(record.provenance.get("label_origin", "unknown"))
        for record in backend.records.values()
    }
    provenance = {
        "origin": origin,
        "dataset_revision": revision,
        "label_origin": next(iter(label_origins))
        if len(label_origins) == 1
        else "mixed",
        "human_reviewed": False,
        "quality_validated": False,
    }
    return (
        suite,
        backend,
        {
            "case_count": len(suite.test_cases),
            "dataset_revision": revision,
            "provenance": provenance,
        },
    )


def validate_saved_inputs(
    suite_path: Path, response_path: Path, *, web: bool = False
) -> dict[str, Any]:
    """Validate complete input/schema/ID mapping before upload registration or run."""
    return _load_inputs(Path(suite_path), Path(response_path), web=web)[2]


def evaluate_saved(
    suite_path: Path,
    response_path: Path,
    *,
    strict: bool = True,
    progress: Callable[[int, int], None] | None = None,
) -> EvaluationOutcome:
    """Execute validated saved responses without history, file or network writes."""
    suite, backend, info = _load_inputs(Path(suite_path), Path(response_path))
    runner = SavedRunner(backend, strict=strict)

    async def execute():
        results = []
        for index, case in enumerate(suite.test_cases, 1):
            results.append(await runner.run(case))
            if progress is not None:
                progress(index, len(suite.test_cases))
        return results

    results = asyncio.run(execute())
    counts = {
        key: sum(r.outcome == key for r in results)
        for key in ("passed", "failed", "indeterminate", "error")
    }
    exit_code = (
        2
        if counts["indeterminate"] or counts["error"]
        else 1
        if counts["failed"]
        else 0
    )
    origin = info["provenance"]["origin"]
    scope = (
        "synthetic_contract"
        if origin == "synthetic"
        else "recorded_response_contract"
        if origin in {"real", "recorded"}
        else "unknown"
    )
    if not strict:
        scope = "unknown"
    if scope == "unknown":
        exit_code = 2
    gate = {
        "status": "cannot_evaluate"
        if exit_code == 2
        else "failed"
        if exit_code == 1
        else "passed",
        "exit_code": exit_code,
        "counts": counts,
        "scope": scope,
        "quality_validated": False,
    }
    total = len(results)
    passed = counts["passed"]
    report = Report(
        suite_name=suite.name,
        summary=ReportSummary(
            total=total,
            passed=passed,
            failed=total - passed,
            pass_rate=passed / total,
            avg_score=sum(r.score for r in results) / total,
        ),
        results=results,
        metadata={
            "backend": "saved",
            "mode": "saved",
            "strict_evidence": strict,
            "origin": origin,
            "dataset_revision": info["dataset_revision"],
            "provenance": info["provenance"],
            "judge_method": METHOD
            if all(
                case.type == TestCaseType.EVIDENCE_SUPPORT for case in suite.test_cases
            )
            else "legacy_saved_checks"
            if all(
                case.type != TestCaseType.EVIDENCE_SUPPORT for case in suite.test_cases
            )
            else "mixed_saved_checks",
            "judge_version": VERSION,
            "gate": gate,
            "suite_contract": sha256_bytes(
                canonical_json_bytes(suite.model_dump(mode="json"))
            ),
            "input_hashes": {
                "suite": sha256_file(suite_path),
                "responses": sha256_file(response_path),
            },
        },
    )
    return EvaluationOutcome(
        report=immutable_report(report), exit_code=exit_code if strict else 0
    )
