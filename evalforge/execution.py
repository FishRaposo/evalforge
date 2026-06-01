"""Hybrid execution core — deterministic simulation or real provider calls.

Set ``EVALFORGE_LLM_MODE=real`` to use real provider clients.
Set ``EVALFORGE_LLM_MODE=sim`` (default) for deterministic mock responses.
"""

from __future__ import annotations

import os
import random
from typing import Any


def resolve_mode(mode: str | None = None) -> str:
    """Return execution mode: ``"sim"`` or ``"real"``."""
    return (mode or os.getenv("EVALFORGE_LLM_MODE") or "sim").lower()


class SimulatedEvaluator:
    """Deterministic evaluator that returns fake scores and reasoning.

    Offline-first: requires no API keys and produces repeatable
    results for tests and demos.
    """

    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)

    def evaluate(self, prompt: str) -> dict[str, Any]:
        """Return a deterministic evaluation result.

        Uses a hash of *prompt* to keep results stable across repeated
        calls for the same input while varying across different inputs.
        """
        # Deterministic sub-sequence based on prompt content
        prompt_hash = sum(ord(c) for c in prompt)
        self._rng.seed(prompt_hash)

        score = round(self._rng.uniform(0.5, 1.0), 2)
        consistency = self._rng.choice(["high", "medium", "high"])

        return {
            "score": score,
            "reasoning": f"Simulated evaluation with seed-derived score {score}.",
            "criteria_scores": {
                "accuracy": round(self._rng.uniform(score - 0.1, score), 2),
                "completeness": round(self._rng.uniform(score - 0.1, score), 2),
                "clarity": round(self._rng.uniform(score - 0.1, score), 2),
                "relevance": round(self._rng.uniform(score - 0.1, score), 2),
            },
            "method": "simulated",
            "consistency": consistency,
        }

    def batch_evaluate(self, prompts: list[str]) -> list[dict[str, Any]]:
        """Evaluate multiple prompts deterministically."""
        return [self.evaluate(p) for p in prompts]
