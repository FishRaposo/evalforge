"""Versioned offline responses selected exclusively by exact test-case identity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from evalforge.backends.base import BackendResponse, BaseBackend

CASE_ID_CONTEXT_KEY = "_evalforge_case_id"
MAX_RESPONSE_BYTES = 10 * 1024 * 1024


class RetrievedSource(BaseModel):
    """A verbatim source snapshot, not an assertion of source authority."""

    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    content: str = Field(min_length=1)


class SavedCitation(BaseModel):
    """Claim-to-source link supplied by the application being evaluated."""

    model_config = ConfigDict(extra="forbid", strict=True)
    source_id: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    claim: str = Field(min_length=1)
    quote: str = Field(min_length=1)


class SavedResponseRecord(BaseModel):
    """Public-safe saved-response schema v1; unknown provenance stays unknown."""

    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal[1]
    case_id: str = Field(min_length=1)
    answer: str
    retrieved_sources: list[RetrievedSource] = Field(default_factory=list)
    citations: list[SavedCitation] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


def _validate_provenance(record: SavedResponseRecord) -> None:
    origin = record.provenance.get("origin", "unknown")
    if not isinstance(origin, str) or origin not in {
        "synthetic",
        "recorded",
        "real",
        "unknown",
    }:
        raise ValueError(f"Invalid provenance origin for {record.case_id}")
    for field in ("dataset_revision", "label_origin"):
        if field in record.provenance and not isinstance(record.provenance[field], str):
            raise ValueError(f"Invalid provenance {field} for {record.case_id}")


class SavedResponseBackend(BaseBackend):
    """Read and validate every record before any evaluation is dispatched."""

    def __init__(self, path: Path) -> None:
        if path.stat().st_size > MAX_RESPONSE_BYTES:
            raise ValueError("Saved responses exceed the 10 MiB limit")
        self.records: dict[str, SavedResponseRecord] = {}
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeError as exc:
            raise ValueError("Saved responses must be UTF-8") from exc
        for line_number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                record = SavedResponseRecord.model_validate(json.loads(line))
            except (ValueError, ValidationError, RecursionError) as exc:
                raise ValueError(
                    f"Invalid saved record on line {line_number}: {exc}"
                ) from exc
            if record.case_id in self.records:
                raise ValueError(f"Duplicate saved case ID: {record.case_id}")
            _validate_provenance(record)
            identities = [
                (source.id, source.version) for source in record.retrieved_sources
            ]
            if len(identities) != len(set(identities)):
                raise ValueError(f"Duplicate retrieved source for {record.case_id}")
            self.records[record.case_id] = record
        if not self.records:
            raise ValueError("Saved response file contains no records")

    async def query(
        self, prompt: str, context: dict[str, Any] | None = None
    ) -> BackendResponse:
        """Ignore prompt similarity; callers must supply the reserved exact case ID."""
        case_id = (context or {}).get(CASE_ID_CONTEXT_KEY)
        if not isinstance(case_id, str):
            raise ValueError("Saved backend requires reserved case identity in context")
        if case_id not in self.records:
            raise ValueError(f"Saved response missing for case: {case_id}")
        record = self.records[case_id]
        return BackendResponse(
            content=record.answer,
            metadata={"backend": "saved", **record.model_dump(mode="json")},
        )

    async def health_check(self) -> bool:
        """This backend has no network or provider dependency."""
        return bool(self.records)
