"""EvalForge-owned compatibility contracts and adapters."""

from evalforge.core.clients import (
    AnthropicClient,
    LiteLLMClient,
    LLMClientFactory,
    OfflineLLMClient,
    OpenAICompatibleClient,
)
from evalforge.core.contracts import (
    Completion,
    DatasetRecord,
    DatasetSource,
    DriftEngine,
    JudgeEngine,
    LLMClient,
    ReportRepository,
)
from evalforge.core.ingestion import (
    HuggingFaceDatasetSource,
    SyntheticDatasetSource,
    normalize_record,
)
from evalforge.core.judging import RegistryDriftEngine, RegistryJudgeEngine
from evalforge.core.repository import SQLiteReportRepository

__all__ = [
    "AnthropicClient",
    "Completion",
    "DatasetRecord",
    "DatasetSource",
    "DriftEngine",
    "HuggingFaceDatasetSource",
    "JudgeEngine",
    "LLMClient",
    "LLMClientFactory",
    "LiteLLMClient",
    "OfflineLLMClient",
    "OpenAICompatibleClient",
    "RegistryDriftEngine",
    "RegistryJudgeEngine",
    "ReportRepository",
    "SQLiteReportRepository",
    "SyntheticDatasetSource",
    "normalize_record",
]
