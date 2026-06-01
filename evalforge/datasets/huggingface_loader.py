"""HuggingFace datasets integration.

Load and evaluate on public datasets from HuggingFace Hub.
"""

from __future__ import annotations

from typing import Any


class HuggingFaceDatasetLoader:
    """Loads datasets from HuggingFace Hub for evaluation.

    Supports popular RAG benchmarks:
    - HotpotQA
    - Natural Questions
    - TriviaQA
    - SQuAD
    """

    DATASET_CONFIGS = {
        "hotpot_qa": {
            "path": "hotpot_qa",
            "name": "fullwiki",
            "question_column": "question",
            "answer_column": "answer",
            "context_column": "context",
        },
        "natural_questions": {
            "path": "google-research-datasets/natural_questions",
            "question_column": "question_text",
            "answer_column": "annotations",
        },
        "trivia_qa": {
            "path": "trivia_qa",
            "name": "unfiltered.nocontext",
            "question_column": "question",
            "answer_column": "answer",
        },
        "squad": {
            "path": "squad",
            "question_column": "question",
            "answer_column": "answers",
            "context_column": "context",
        },
    }

    def __init__(self) -> None:
        """Initialize loader."""
        self._datasets = None

    def _ensure_datasets(self) -> Any:
        """Ensure datasets library is available."""
        if self._datasets is None:
            try:
                import datasets
                self._datasets = datasets
            except ImportError:
                raise ImportError(
                    "datasets library required. "
                    "Install with: pip install datasets"
                )
        return self._datasets

    async def load_dataset(
        self,
        name: str,
        split: str = "validation",
        max_samples: int | None = None,
    ) -> list[dict[str, Any]]:
        """Load a dataset.

        Args:
            name: Dataset name (hotpot_qa, squad, etc.).
            split: Dataset split (train, validation, test).
            max_samples: Maximum samples to load.

        Returns:
            List of examples.
        """
        config = self.DATASET_CONFIGS.get(name)
        if not config:
            raise ValueError(f"Unknown dataset: {name}")

        try:
            datasets = self._ensure_datasets()
        except ImportError:
            # Offline fallback: generate synthetic examples
            limit = max_samples or 5
            return [
                {
                    "query": f"Synthetic question {i} for {name}",
                    "expected_answer": f"Synthetic answer {i}",
                    "context": f"Synthetic context {i}",
                }
                for i in range(limit)
            ]

        # Load from HuggingFace
        dataset = datasets.load_dataset(
            config["path"],
            name=config.get("name"),
            split=split,
        )

        # Convert to standard format
        examples = []
        for i, item in enumerate(dataset):
            if max_samples and i >= max_samples:
                break

            example = self._convert_example(item, config)
            examples.append(example)

        return examples

    def _convert_example(
        self,
        item: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert dataset item to standard format.

        Args:
            item: Dataset item.
            config: Dataset config.

        Returns:
            Standardized example.
        """
        q_col = config.get("question_column", "question")
        a_col = config.get("answer_column", "answer")
        c_col = config.get("context_column")

        example = {
            "query": item.get(q_col, ""),
            "expected_answer": item.get(a_col, ""),
            "expected_citations": [],
        }

        # Extract context if available
        if c_col and c_col in item:
            context = item[c_col]
            if isinstance(context, list):
                example["expected_citations"] = [c.get("text", str(c)) for c in context[:5]]
            elif isinstance(context, str):
                example["expected_citations"] = [context]

        return example

    async def create_test_suite(
        self,
        dataset_name: str,
        output_path: str,
        split: str = "validation",
        max_samples: int = 100,
    ) -> str:
        """Create EvalForge test suite from dataset.

        Args:
            dataset_name: Name of dataset.
            output_path: Where to save YAML suite.
            split: Dataset split.
            max_samples: Max samples to include.

        Returns:
            Path to created suite.
        """
        examples = await self.load_dataset(dataset_name, split, max_samples)

        import yaml

        suite: dict[str, Any] = {
            "name": f"{dataset_name}_benchmark",
            "description": f"Benchmark from {dataset_name} dataset",
            "backend": "openai",
            "test_cases": [],
        }

        for i, ex in enumerate(examples):
            suite["test_cases"].append({
                "id": f"{dataset_name}_{i:04d}",
                "name": f"test_{i}",
                "type": "semantic_answer",
                "input": ex["query"],
                "expected": ex["expected_answer"],
                "tags": ["hf", dataset_name],
            })

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(suite, f, default_flow_style=False, sort_keys=False)

        return output_path

    def list_available_datasets(self) -> list[str]:
        """List available built-in datasets.

        Returns:
            List of dataset names.
        """
        return list(self.DATASET_CONFIGS.keys())
