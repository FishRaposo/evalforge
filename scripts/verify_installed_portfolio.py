"""Run with a fresh installed wheel, isolated mode and an outside-checkout cwd."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

import evalforge
from evalforge.evaluation import evaluate_saved
from evalforge.evidence import verify_evidence_bundle
from evalforge.portfolio import get_portfolio_profiles, get_portfolio_root
from evalforge.server.app import create_app


def main() -> None:
    installed = Path(evalforge.__file__).resolve()
    if "site-packages" not in str(installed):
        raise AssertionError(f"Expected installed wheel, imported {installed}")
    root = get_portfolio_root()
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["human_reviewed"] is False
    expected = {"baseline": 0, "candidate": 1, "repaired": 0, "indeterminate": 2}
    profiles = get_portfolio_profiles()
    assert len(profiles) == 4
    for profile in profiles:
        result = evaluate_saved(profile["suite_path"], profile["response_path"])
        assert result.exit_code == expected[profile["id"]]
        assert result.report.summary.total == 100
        assert result.report.metadata["gate"]["quality_validated"] is False
    with tempfile.TemporaryDirectory(prefix="evalforge-installed-") as temporary:
        directory = Path(temporary)
        candidate = next(p for p in profiles if p["id"] == "candidate")
        command = [
            sys.executable,
            "-I",
            "-m",
            "evalforge.cli",
            "eval",
            str(candidate["suite_path"]),
            "--backend",
            "saved",
            "--response-file",
            str(candidate["response_path"]),
            "--strict-evidence",
            "--no-save",
            "--format",
            "json",
            "--output",
            str(directory / "reports"),
            "--evidence-dir",
            str(directory / "evidence"),
        ]
        completed = subprocess.run(
            command,
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert completed.returncode == 1, completed.stdout + completed.stderr
        assert verify_evidence_bundle(directory / "evidence").schema_version == 3
        with TestClient(create_app(str(directory / "history.db"))) as client:
            assert client.get("/api/health").status_code == 200
            assert len(client.get("/api/evaluation-profiles").json()["profiles"]) == 4
            assert client.get("/api/runs").json() == []
    print("Installed wheel: packaged profiles0/1/0/2, actual CLI/v3, API pass")


if __name__ == "__main__":
    main()
