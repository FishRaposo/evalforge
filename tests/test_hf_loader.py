"""Tests for the HuggingFace dataset loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from evalforge.datasets.huggingface_loader import HuggingFaceDatasetLoader
from evalforge.loader.suite_loader import SuiteLoader


class TestHuggingFaceDatasetLoader:
    """Tests for HuggingFaceDatasetLoader."""

    @pytest.fixture
    def loader(self) -> HuggingFaceDatasetLoader:
        return HuggingFaceDatasetLoader()

    def test_list_available_datasets(self, loader: HuggingFaceDatasetLoader) -> None:
        datasets = loader.list_available_datasets()
        assert isinstance(datasets, list)
        assert "natural_questions" in datasets

    def test_create_test_suite(self, loader: HuggingFaceDatasetLoader, tmp_path: Path) -> None:
        # Use mock mode to avoid real HF download
        import os
        os.environ["EVALFORGE_LLM_MODE"] = "sim"
        output = tmp_path / "hf_suite.yaml"
        import asyncio
        asyncio.run(loader.create_test_suite("natural_questions", str(output), max_samples=2))
        assert output.exists()
        suite = SuiteLoader().load_suite(output)
        assert suite.name == "natural_questions_benchmark"
        assert len(suite.test_cases) == 2
        assert suite.test_cases[0].input is not None
        assert suite.test_cases[0].expected is not None
        assert suite.test_cases[0].type.value == "semantic_answer"
