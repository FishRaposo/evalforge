"""Semantic similarity judge using embedding-based comparison."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

from evalforge.config import get_settings
from evalforge.judges.base import BaseJudge, JudgeResult
from evalforge.models.test_case import TestCase


class SemanticMatchJudge(BaseJudge):
    """Judge that evaluates semantic similarity between response and expected answer.

    Uses OpenAI embeddings API when available, falls back to TF-IDF cosine
    similarity, and ultimately to Jaccard overlap if neither works.

    Args:
        threshold: Minimum similarity score to consider a match (0.0-1.0).
    """

    def __init__(self, threshold: float | None = None) -> None:
        settings = get_settings()
        self._threshold = threshold if threshold is not None else settings.SIMILARITY_THRESHOLD
        self._cache: dict[str, list[float]] = {}
        self._client: Any = None

    def judge(self, test_case: TestCase, response: str) -> JudgeResult:
        expected = str(test_case.expected) if test_case.expected is not None else ""
        threshold = test_case.metadata.get("threshold", self._threshold)

        similarity = self._compute_similarity(response, expected)
        passed = similarity >= threshold

        return JudgeResult(
            passed=passed,
            score=similarity,
            details={
                "expected": expected,
                "actual": response,
                "similarity": similarity,
                "threshold": threshold,
                "match_type": "semantic",
            },
        )

    def _compute_similarity(self, text_a: str, text_b: str) -> float:
        if not text_a and not text_b:
            return 1.0
        if not text_a or not text_b:
            return 0.0

        embedding_sim = self._embedding_similarity(text_a, text_b)
        if embedding_sim is not None:
            return round(embedding_sim, 4)

        tfidf_sim = self._tfidf_cosine_similarity(text_a, text_b)
        if tfidf_sim is not None:
            return round(tfidf_sim, 4)

        return round(self._jaccard_similarity(text_a, text_b), 4)

    def _embedding_similarity(self, text_a: str, text_b: str) -> float | None:
        api_key = get_settings().OPENAI_API_KEY
        if not api_key:
            return None

        try:
            embedding_a = self._get_embedding(text_a, api_key)
            embedding_b = self._get_embedding(text_b, api_key)
            if embedding_a is None or embedding_b is None:
                return None
            return self._cosine_similarity(embedding_a, embedding_b)
        except Exception:
            return None

    def _get_embedding(self, text: str, api_key: str) -> list[float] | None:
        if text in self._cache:
            return self._cache[text]

        import httpx

        if self._client is None:
            self._client = httpx.Client(timeout=30.0)

        response = self._client.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": "text-embedding-3-small", "input": text},
        )
        response.raise_for_status()
        data = response.json()
        embedding: list[float] = data["data"][0]["embedding"]
        self._cache[text] = embedding
        return embedding

    @staticmethod
    def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        mag_a = math.sqrt(sum(a * a for a in vec_a))
        mag_b = math.sqrt(sum(b * b for b in vec_b))
        if mag_a == 0.0 or mag_b == 0.0:
            return 0.0
        return dot / (mag_a * mag_b)

    @staticmethod
    def _tfidf_cosine_similarity(text_a: str, text_b: str) -> float | None:
        tokens_a = text_a.lower().split()
        tokens_b = text_b.lower().split()
        if not tokens_a or not tokens_b:
            return None

        counter_a = Counter(tokens_a)
        counter_b = Counter(tokens_b)

        all_terms = set(counter_a.keys()) | set(counter_b.keys())
        doc_count = 2

        tfidf_a: dict[str, float] = {}
        tfidf_b: dict[str, float] = {}
        for term in all_terms:
            df = (1 if term in counter_a else 0) + (1 if term in counter_b else 0)
            idf = math.log(1 + doc_count / df) if df > 0 else 0.0

            tf_a = counter_a.get(term, 0) / len(tokens_a)
            tfidf_a[term] = tf_a * idf

            tf_b = counter_b.get(term, 0) / len(tokens_b)
            tfidf_b[term] = tf_b * idf

        dot = sum(tfidf_a.get(t, 0.0) * tfidf_b.get(t, 0.0) for t in all_terms)
        mag_a = math.sqrt(sum(v * v for v in tfidf_a.values()))
        mag_b = math.sqrt(sum(v * v for v in tfidf_b.values()))
        if mag_a == 0.0 or mag_b == 0.0:
            return 0.0
        return dot / (mag_a * mag_b)

    @staticmethod
    def _jaccard_similarity(text_a: str, text_b: str) -> float:
        tokens_a = set(text_a.lower().split())
        tokens_b = set(text_b.lower().split())
        if not tokens_a and not tokens_b:
            return 1.0
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b
        return len(intersection) / len(union)
