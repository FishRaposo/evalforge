"""EvalForge demo — run a sample suite against the deterministic mock backend.

Offline: no API keys required. Invokes the EvalForge CLI on a bundled example suite
and prints the evaluation report (judges, per-case scores, pass/fail summary).
"""

from __future__ import annotations

import sys
from pathlib import Path

from typer.testing import CliRunner

from evalforge.cli import app

SUITE = Path(__file__).resolve().parent.parent / "example_suites" / "rag_basic.yaml"


def main() -> None:
    # Rich-formatted CLI output contains Unicode; force UTF-8 on Windows consoles.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== EvalForge demo (mock backend, offline) ===")
    result = CliRunner().invoke(app, ["eval", str(SUITE), "--backend", "mock"])
    print(result.output)
    print(f"=== EvalForge demo complete (exit code {result.exit_code}) ===")


if __name__ == "__main__":
    main()
