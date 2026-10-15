"""Shared source/document identifier matching for the citation and retrieval judges.

Strict matching is the default: an expected source matches only when a cited or
retrieved identifier is the same identifier after normalization (case, whitespace
and separator punctuation are ignored; words, numbers, years and versions are not).
``Refund Policy 2023`` therefore never satisfies ``Refund Policy 2024`` and
``refund_policy_v1.md`` never satisfies ``refund_policy_v2.md``.

Fuzzy matching (substring plus word overlap) is the historical behaviour and is
available only through an explicit per-case opt-in: ``metadata: {match: fuzzy}``.
"""

from __future__ import annotations

import re
from typing import Any, Literal

MatchMode = Literal["strict", "fuzzy"]

MATCH_MODES: tuple[str, ...] = ("strict", "fuzzy")

_SEPARATORS = re.compile(r"[^0-9a-z]+")


def normalize_source_id(value: str) -> str:
    """Normalize a source or document identifier for strict comparison.

    Lowercases and collapses every run of non-alphanumeric characters to a single
    space, so ``Refund_Policy-v2.MD`` and ``refund policy v2 md`` are equal while
    ``refund_policy_v1.md`` and ``refund_policy_v2.md`` stay different.
    """
    return _SEPARATORS.sub(" ", value.lower()).strip()


def resolve_match_mode(metadata: dict[str, Any] | None) -> MatchMode:
    """Read the matching mode from test-case metadata (default ``strict``).

    Raises:
        ValueError: If ``metadata["match"]`` is set to an unknown mode.
    """
    raw = (metadata or {}).get("match", "strict")
    mode = str(raw).strip().lower()
    if mode == "strict":
        return "strict"
    if mode == "fuzzy":
        return "fuzzy"
    raise ValueError(
        f"Unknown match mode {raw!r}; expected one of: {', '.join(MATCH_MODES)}"
    )
