"""Dependency-free contracts for the versioned evaluation migration assets."""

from __future__ import annotations

import json
from pathlib import Path

from evalforge.retrieval_evaluation import (
    compare_strategies,
    load_corpus,
    load_golden_questions,
)

ASSET_ROOT = (
    Path(__file__).parents[1]
    / "data"
    / "migrations"
    / "2026-08-12-rag-evaluation-lab-and-ai-support-simulator"
)


def test_versioned_retrieval_assets_exercise_both_strategy_outcomes() -> None:
    """Removing the migrated goldens/corpus should break the executable A/B demo."""
    questions = load_golden_questions(
        ASSET_ROOT / "retrieval" / "golden_questions.jsonl"
    )
    corpus = load_corpus(ASSET_ROOT / "retrieval" / "corpus.jsonl")

    comparison = compare_strategies(
        questions,
        corpus,
        "term-frequency",
        "phrase-aware",
        top_k=1,
        threshold=0.1,
    )

    assert comparison["baseline"]["metrics"] == {
        "questions": 2,
        "hit_rate": 0.0,
        "mrr": 0.0,
    }
    assert comparison["candidate"]["metrics"] == {
        "questions": 2,
        "hit_rate": 1.0,
        "mrr": 1.0,
    }
    assert comparison["winner"] == "phrase-aware"
    assert comparison["regression"]["is_regression"] is False


def test_manifest_resolves_every_versioned_asset_with_source_provenance() -> None:
    """The asset manifest must resolve and retain the two reviewed source SHAs."""
    manifest = json.loads((ASSET_ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["schema_version"] == 1
    assert manifest["sources"] == [
        {
            "repository": "rag-evaluation-lab",
            "sha": "0fd1cc1facb6f67bb866b6825e5c4e391c8ab2c5",
            "license": "MIT",
        },
        {
            "repository": "ai-support-simulator",
            "sha": "3ff2d0c47251ee43f8026c14a5d805b1550a3110",
            "license": "MIT",
        },
    ]
    assert len(manifest["assets"]) == 7
    assert all(
        (ASSET_ROOT / relative_path).is_file() for relative_path in manifest["assets"]
    )


def test_conversation_baseline_pair_encodes_a_safety_regression() -> None:
    """The migrated baseline pair must contain a real pass-to-safety-fail diff."""
    baseline = json.loads(
        (
            ASSET_ROOT / "conversation" / "baselines" / "prompt_injection_safe.json"
        ).read_text(encoding="utf-8")
    )
    regressed = json.loads(
        (
            ASSET_ROOT
            / "conversation"
            / "baselines"
            / "prompt_injection_regressed.json"
        ).read_text(encoding="utf-8")
    )
    expected_diff = json.loads(
        (
            ASSET_ROOT
            / "conversation"
            / "baselines"
            / "prompt_injection_expected_diff.json"
        ).read_text(encoding="utf-8")
    )

    assert baseline["scenario"] == regressed["scenario"]
    assert baseline["passed"] is True
    assert regressed["passed"] is False
    assert baseline["dimensions"]["safety"]["score"] == 1.0
    assert regressed["dimensions"]["safety"]["score"] == 0.0
    assert (
        regressed["overall_score"] - baseline["overall_score"]
        == expected_diff["overall_delta"]
        == -0.6
    )
    assert expected_diff["regressed_dimensions"] == ["safety"]
    assert expected_diff["is_regression"] is True
