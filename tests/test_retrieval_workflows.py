"""Golden-question retrieval A/B and CI regression tests."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from evalforge.cli import app

runner = CliRunner()
ASSET_ROOT = (
    Path(__file__).parents[1]
    / "data"
    / "migrations"
    / "2026-08-12-rag-evaluation-lab-and-ai-support-simulator"
)
GOLDENS = ASSET_ROOT / "retrieval" / "golden_questions.jsonl"
CORPUS = ASSET_ROOT / "retrieval" / "corpus.jsonl"


def test_retrieval_compare_writes_strategy_diff_for_same_goldens(
    tmp_path: Path,
) -> None:
    """A phrase-aware candidate should beat term frequency on the same golden."""
    output = tmp_path / "comparison.json"

    result = runner.invoke(
        app,
        [
            "retrieval",
            "compare",
            str(GOLDENS),
            str(CORPUS),
            "--strategy-a",
            "term-frequency",
            "--strategy-b",
            "phrase-aware",
            "--top-k",
            "1",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["baseline"]["strategy"] == "term-frequency"
    assert payload["baseline"]["metrics"]["hit_rate"] == 0.0
    assert payload["candidate"]["strategy"] == "phrase-aware"
    assert payload["candidate"]["metrics"]["hit_rate"] == 1.0
    assert payload["deltas"]["hit_rate"] == 1.0
    assert payload["winner"] == "phrase-aware"


def test_retrieval_compare_exits_one_when_candidate_regresses(tmp_path: Path) -> None:
    """CI should fail when candidate hit rate drops beyond the allowed threshold."""
    output = tmp_path / "regression.json"

    result = runner.invoke(
        app,
        [
            "retrieval",
            "compare",
            str(GOLDENS),
            str(CORPUS),
            "--strategy-a",
            "phrase-aware",
            "--strategy-b",
            "term-frequency",
            "--top-k",
            "1",
            "--threshold",
            "0.1",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["regression"]["is_regression"] is True
    assert payload["regression"]["regressed_metrics"] == ["hit_rate", "mrr"]
    assert "Regression detected" in result.output
