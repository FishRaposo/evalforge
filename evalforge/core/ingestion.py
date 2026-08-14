"""Dataset adapters owned by EvalForge."""

from __future__ import annotations

from typing import Any

from evalforge.core.contracts import DatasetRecord
from evalforge.datasets.huggingface_loader import HuggingFaceDatasetLoader


class HuggingFaceDatasetSource:
    """Normalize the legacy HuggingFace loader behind ``DatasetSource``."""

    def __init__(self, loader: HuggingFaceDatasetLoader | None = None) -> None:
        self.loader = loader or HuggingFaceDatasetLoader()

    async def load_records(
        self,
        name: str,
        *,
        split: str = "validation",
        max_samples: int | None = None,
    ) -> list[DatasetRecord]:
        rows = await self.loader.load_dataset(
            name, split=split, max_samples=max_samples
        )
        return [
            DatasetRecord.from_mapping(row, index=index)
            for index, row in enumerate(rows)
        ]


class SyntheticDatasetSource:
    """Small deterministic source useful for offline fixtures and CI."""

    async def load_records(
        self,
        name: str,
        *,
        split: str = "validation",
        max_samples: int | None = None,
    ) -> list[DatasetRecord]:
        limit = max_samples or 5
        return [
            DatasetRecord(
                id=f"{name}-{index}",
                query=f"Synthetic question {index} for {name}",
                expected_answer=f"Synthetic answer {index}",
                context=f"Synthetic context {index}",
                metadata={"split": split, "source": "synthetic"},
            )
            for index in range(limit)
        ]


def normalize_record(item: Any, index: int = 0) -> DatasetRecord:
    """Normalize a mapping or already-canonical record."""

    if isinstance(item, DatasetRecord):
        return item
    if isinstance(item, dict):
        return DatasetRecord.from_mapping(item, index=index)
    raise TypeError("dataset records must be mappings or DatasetRecord instances")
