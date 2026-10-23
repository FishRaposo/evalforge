"""Locate bundled synthetic inputs independently of the caller's working directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def get_portfolio_root() -> Path:
    """Return installed resources, or the same assets in an editable source tree."""
    installed = Path(__file__).resolve().parent / "data" / "portfolio"
    if installed.is_dir():
        return installed
    source = Path(__file__).resolve().parent.parent / "data" / "portfolio"
    if source.is_dir():
        return source
    raise FileNotFoundError("Packaged EvalForge portfolio assets are unavailable")


def get_portfolio_profiles() -> list[dict[str, Any]]:
    """Internal paths and honest provenance; HTTP adapters omit host paths."""
    root = get_portfolio_root()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    descriptions = {
        "baseline": "100 synthetic whole-answer/source contracts satisfied.",
        "candidate": "Six declared evidence, fact, stale or injection regressions.",
        "repaired": "Six declared regressions repaired against frozen contracts.",
        "indeterminate": "One response has unknown origin; a strict gate cannot pass.",
    }
    return [
        {
            "id": key,
            "name": key.title(),
            "description": description,
            "suite_path": root / "suite.yaml",
            "response_path": root / f"{key}.jsonl",
            "provenance": {
                "origin": "synthetic",
                "assessed_response_origin": "unknown"
                if key == "indeterminate"
                else "synthetic",
                "dataset_revision": manifest["dataset_revision"],
                "label_origin": "agent-authored",
                "human_reviewed": False,
                "quality_validated": False,
            },
        }
        for key, description in descriptions.items()
    ]
