"""Dataset ingestion compatibility imports."""

from evalforge.core.contracts import DatasetRecord, DatasetSource
from evalforge.core.ingestion import (
    HuggingFaceDatasetSource,
    SyntheticDatasetSource,
    normalize_record,
)

__all__ = [
    "DatasetRecord",
    "DatasetSource",
    "HuggingFaceDatasetSource",
    "SyntheticDatasetSource",
    "normalize_record",
]
