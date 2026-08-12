"""Golden-question retrieval A/B and CI regression tests."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from evalforge.cli import app


runner = CliRunner()


def _write_retrieval_fixtures(tmp_path: Path) -> tuple[Path, Path]:
    goldens = tmp_path / "goldens.jsonl"
    goldens.write_text(
        json.dumps(
            {
                "id": "q1",
                "query": "alpha beta",
                "gold_contexts": ["alpha beta is the supported answer"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "gold",
                        "content": "alpha beta is the supported answer",
                    }
                ),
                json.dumps(
                    {
                        "id": "distractor",
                        "content": "beta notes mention alpha alpha alpha",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return goldens, corpus


def test_retrieval_compare_writes_strategy_diff_for_same_goldens(
    tmp_path: Path,
) -> None:
    """A phrase-aware candidate should beat term frequency on the same golden."""
    goldens, corpus = _write_retrieval_fixtures(tmp_path)
    output = tmp_path / "comparison.json"

    result = runner.invoke(
        app,
        [
            "retrieval",
            "compare",
            str(goldens),
            str(corpus),
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
    goldens, corpus = _write_retrieval_fixtures(tmp_path)
    output = tmp_path / "regression.json"

    result = runner.invoke(
        app,
        [
            "retrieval",
            "compare",
            str(goldens),
            str(corpus),
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
