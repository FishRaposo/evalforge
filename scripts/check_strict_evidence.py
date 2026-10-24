"""Run saved synthetic profiles through the public CLI and verify strict evidence."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evalforge.evidence import verify_evidence_bundle  # noqa: E402
from evalforge.portfolio import get_portfolio_profiles  # noqa: E402


def authored_agreement(profile_id: str, profile: dict, report: dict) -> list[dict]:
    """Measure the frozen authored labels, without population-validity claims."""
    corpus = json.loads(
        (profile["suite_path"].parent / "manifest.json").read_text(encoding="utf-8")
    )
    cases = yaml.safe_load(profile["suite_path"].read_text(encoding="utf-8"))[
        "test_cases"
    ]
    records = {
        row["case_id"]: row
        for row in (
            json.loads(line)
            for line in profile["response_path"]
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        )
    }
    authored = {}
    for case in cases:
        case_id = case["id"]
        authored[case_id] = (
            "failed"
            if profile_id == "candidate" and case_id in corpus["synthetic_fault_labels"]
            else "indeterminate"
            if records[case_id]["provenance"].get("origin") == "unknown"
            else "passed"
        )
    measured = {row["test_case_id"]: row["outcome"] for row in report["results"]}
    agreement = []
    for split in ("development", "held_out"):
        for category in (
            "answerable",
            "unanswerable",
            "conflicting",
            "adversarial",
        ):
            ids = [
                case["id"]
                for case in cases
                if case["metadata"]["split"] == split
                and case["metadata"]["category"] == category
            ]
            agreement.append(
                {
                    "split": split,
                    "category": category,
                    "total": len(ids),
                    "agreement": sum(measured[i] == authored[i] for i in ids),
                    "false_passes": sum(
                        measured[i] == "passed" and authored[i] != "passed" for i in ids
                    ),
                    "false_failures": sum(
                        measured[i] == "failed" and authored[i] == "passed" for i in ids
                    ),
                    "indeterminate": sum(measured[i] == "indeterminate" for i in ids),
                    "errors": sum(measured[i] == "error" for i in ids),
                }
            )
    return agreement


def check(output_dir: Path) -> dict:
    """Check observable CLI decisions; preserve original bundles independently."""
    profiles = {profile["id"]: profile for profile in get_portfolio_profiles()}
    expected = {"baseline": 0, "candidate": 1, "repaired": 0, "indeterminate": 2}
    results = {}
    environment = {
        **os.environ,
        "PYTHONUTF8": "1",
        "EVALFORGE_LLM_MODE": "sim",
        "EVALFORGE_OPENAI_API_KEY": "",
        "OPENAI_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for profile_id, expected_exit in expected.items():
        profile = profiles[profile_id]
        directory = output_dir / profile_id
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "evalforge.cli",
                "eval",
                str(profile["suite_path"]),
                "--backend",
                "saved",
                "--response-file",
                str(profile["response_path"]),
                "--strict-evidence",
                "--no-save",
                "--format",
                "json",
                "--output",
                str(directory / "reports"),
                "--evidence-dir",
                str(directory / "evidence"),
            ],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "cli.log").write_text(
            completed.stdout + completed.stderr, encoding="utf-8"
        )
        if completed.returncode != expected_exit:
            raise ValueError(
                f"{profile_id}: expected exit{expected_exit}, "
                f"got{completed.returncode}; "
                f"inspect {directory / 'cli.log'}"
            )
        manifest = verify_evidence_bundle(directory / "evidence")
        if manifest.schema_version != 3:
            raise ValueError(f"{profile_id}: strict evidence must use schema3")
        report = json.loads(
            (directory / "evidence/report.json").read_text(encoding="utf-8")
        )
        gate = report["metadata"]["gate"]
        if gate["exit_code"] != expected_exit:
            raise ValueError(f"{profile_id}: CLI and report gate disagree")
        if sum(gate["counts"].values()) != report["summary"]["total"]:
            raise ValueError(f"{profile_id}: outcome counts do not reconcile")
        if report["summary"]["total"] != 100 or gate["quality_validated"] is not False:
            raise ValueError(f"{profile_id}: corpus/provenance acceptance failed")
        results[profile_id] = {
            "exit_code": completed.returncode,
            "gate": gate,
            "result_hash": manifest.reproducibility_hash,
        }
        agreement = authored_agreement(profile_id, profile, report)
        results[profile_id]["authored_expectation_agreement"] = agreement
        if any(row["agreement"] != row["total"] for row in agreement):
            raise ValueError(
                f"{profile_id}: outcome disagrees with frozen authored expectation"
            )
    summary = {
        "provenance": "Actual CLI; synthetic authored inputs; no model calls.",
        "limitations": (
            "Agreement with agent-authored fixture expectations only. "
            "All candidate faults are development cases; held-out cases test "
            "unchanged valid contracts. No human calibration, model-quality "
            "estimate or population confidence interval."
        ),
        "profiles": results,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "artifacts/strict-evidence"
    )
    args = parser.parse_args()
    check(args.output_dir.resolve())
    print("Verified strict CLI exits0/1/0/2, four schema3 bundles and100-case counts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
