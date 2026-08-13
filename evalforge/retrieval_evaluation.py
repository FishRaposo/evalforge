"""Offline golden-question retrieval evaluation and strategy comparison."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Sequence

RetrievalStrategy = Literal["term-frequency", "phrase-aware"]
SUPPORTED_STRATEGIES: tuple[RetrievalStrategy, ...] = (
    "term-frequency",
    "phrase-aware",
)
_TRACKED_METRICS = ("hit_rate", "mrr")
_TOKEN_PATTERN = re.compile(r"[\w]+", re.UNICODE)


@dataclass(frozen=True)
class GoldenQuestion:
    """A query and the contexts that a successful retrieval must return."""

    id: str
    query: str
    gold_contexts: tuple[str, ...]


@dataclass(frozen=True)
class CorpusDocument:
    """A retrieval corpus entry."""

    id: str
    content: str


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSON objects while tolerating fenced JSONL wrappers."""
    records: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("```"):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            message = f"Invalid JSONL at {path}:{line_number}: {exc.msg}"
            raise ValueError(message) from exc
        if not isinstance(value, dict):
            raise ValueError(f"Expected an object at {path}:{line_number}")
        records.append(value)
    return records


def load_golden_questions(path: str | Path) -> list[GoldenQuestion]:
    """Load the golden-question JSONL shape used by RAG evaluation suites."""
    questions: list[GoldenQuestion] = []
    for index, item in enumerate(_load_jsonl(Path(path)), start=1):
        query = item.get("query")
        contexts = item.get("gold_contexts")
        if not isinstance(query, str) or not query.strip():
            raise ValueError(f"Golden question {index} requires a non-empty query")
        if (
            not isinstance(contexts, list)
            or not contexts
            or not all(
                isinstance(context, str) and context.strip() for context in contexts
            )
        ):
            raise ValueError(
                f"Golden question {index} requires non-empty gold_contexts"
            )
        questions.append(
            GoldenQuestion(
                id=str(item.get("id", index)),
                query=query,
                gold_contexts=tuple(contexts),
            )
        )
    if not questions:
        raise ValueError(f"No golden questions found in {path}")
    return questions


def load_corpus(path: str | Path) -> list[CorpusDocument]:
    """Load a JSONL retrieval corpus containing ``id`` and ``content`` fields."""
    documents: list[CorpusDocument] = []
    for index, item in enumerate(_load_jsonl(Path(path)), start=1):
        content = item.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"Corpus document {index} requires non-empty content")
        documents.append(CorpusDocument(id=str(item.get("id", index)), content=content))
    if not documents:
        raise ValueError(f"No corpus documents found in {path}")
    return documents


def _tokens(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.casefold())


def _score(query: str, content: str, strategy: RetrievalStrategy) -> float:
    query_tokens = _tokens(query)
    content_tokens = _tokens(content)
    if not query_tokens:
        return 0.0
    if strategy == "term-frequency":
        return float(sum(content_tokens.count(token) for token in query_tokens))
    overlap = len(set(query_tokens) & set(content_tokens)) / len(set(query_tokens))
    query_phrase = " ".join(query_tokens)
    content_phrase = " ".join(content_tokens)
    phrase_bonus = 1.0 if query_phrase in content_phrase else 0.0
    return overlap + phrase_bonus


def _is_relevant(document: CorpusDocument, question: GoldenQuestion) -> bool:
    normalized_document = " ".join(_tokens(document.content))
    return any(
        " ".join(_tokens(context)) in normalized_document
        for context in question.gold_contexts
    )


def evaluate_strategy(
    questions: Sequence[GoldenQuestion],
    documents: Sequence[CorpusDocument],
    strategy: RetrievalStrategy,
    *,
    top_k: int = 3,
) -> dict[str, Any]:
    """Evaluate one deterministic lexical retrieval strategy over all goldens."""
    if strategy not in SUPPORTED_STRATEGIES:
        raise ValueError(f"Unsupported retrieval strategy: {strategy}")
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    results: list[dict[str, Any]] = []
    for question in questions:
        ranked = sorted(
            documents,
            key=lambda document: _score(question.query, document.content, strategy),
            reverse=True,
        )[:top_k]
        relevant_rank = next(
            (
                rank
                for rank, document in enumerate(ranked, start=1)
                if _is_relevant(document, question)
            ),
            None,
        )
        results.append(
            {
                "id": question.id,
                "query": question.query,
                "retrieved_ids": [document.id for document in ranked],
                "hit": relevant_rank is not None,
                "reciprocal_rank": (
                    round(1.0 / relevant_rank, 6) if relevant_rank is not None else 0.0
                ),
            }
        )

    count = len(results)
    metrics = {
        "questions": count,
        "hit_rate": round(sum(result["hit"] for result in results) / count, 6),
        "mrr": round(sum(result["reciprocal_rank"] for result in results) / count, 6),
    }
    return {
        "strategy": strategy,
        "top_k": top_k,
        "metrics": metrics,
        "results": results,
    }


def compare_strategies(
    questions: Sequence[GoldenQuestion],
    documents: Sequence[CorpusDocument],
    strategy_a: RetrievalStrategy,
    strategy_b: RetrievalStrategy,
    *,
    top_k: int = 3,
    threshold: float = 0.0,
) -> dict[str, Any]:
    """A/B two strategies and return a CI-ready aggregate regression result."""
    if threshold < 0.0:
        raise ValueError("threshold must not be negative")
    baseline = evaluate_strategy(questions, documents, strategy_a, top_k=top_k)
    candidate = evaluate_strategy(questions, documents, strategy_b, top_k=top_k)
    deltas = {
        metric: round(candidate["metrics"][metric] - baseline["metrics"][metric], 6)
        for metric in _TRACKED_METRICS
    }
    baseline_total = sum(baseline["metrics"][metric] for metric in _TRACKED_METRICS)
    candidate_total = sum(candidate["metrics"][metric] for metric in _TRACKED_METRICS)
    winner = (
        strategy_b
        if candidate_total > baseline_total
        else strategy_a
        if baseline_total > candidate_total
        else "tie"
    )
    regressed_metrics = [
        metric for metric in _TRACKED_METRICS if deltas[metric] < -threshold
    ]
    return {
        "baseline": baseline,
        "candidate": candidate,
        "deltas": deltas,
        "winner": winner,
        "regression": {
            "threshold": threshold,
            "is_regression": bool(regressed_metrics),
            "regressed_metrics": regressed_metrics,
        },
    }
