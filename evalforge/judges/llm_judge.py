"""LLM-as-Judge implementation for evaluation.

Uses LLM to evaluate response quality with structured criteria.
Supports self-consistency scoring and ensemble judging.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import statistics
from typing import Any

from evalforge.core.clients import LLMClientFactory
from evalforge.execution import SimulatedEvaluator, resolve_mode
from evalforge.judges.base import BaseJudge, JudgeResult
from evalforge.models.calibration import CalibrationSummary, JudgeSample
from evalforge.models.test_case import TestCase


class LLMJudge(BaseJudge):
    """Judge that uses LLM to evaluate responses.

    Supports:
    - Single evaluation with structured criteria
    - Self-consistency (multiple samples)
    - Various LLM providers (OpenAI, Anthropic)
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        criteria: str | None = None,
        temperature: float = 0.3,
        num_samples: int = 1,
        api_key: str | None = None,
        client_factory: LLMClientFactory | None = None,
    ) -> None:
        """Initialize LLM judge.

        Args:
            model: LLM model to use.
            criteria: Evaluation criteria description.
            temperature: Sampling temperature.
            num_samples: Number of samples for self-consistency.
            api_key: API key for LLM provider.
        """
        if num_samples < 1:
            raise ValueError("num_samples must be >= 1")
        self.model = model
        self.criteria = criteria or self._default_criteria()
        self.temperature = temperature
        self.num_samples = num_samples
        self.api_key = api_key
        self._client_factory = client_factory or LLMClientFactory()
        self._client: Any = None

    def judge(self, test_case: TestCase, response: str) -> JudgeResult:
        """Evaluate response using LLM (implements BaseJudge interface).

        Offline-first: returns simulated scores when no API key is set.

        Args:
            test_case: Test case defining expected behavior.
            response: Response to evaluate.

        Returns:
            JudgeResult with evaluation.
        """
        query = test_case.input
        context = test_case.expected

        mode = resolve_mode()
        samples: list[JudgeSample] = []
        for sample_index in range(self.num_samples):
            if mode == "sim":
                seed = self._stable_seed(test_case.id, sample_index)
                sim = SimulatedEvaluator(seed=seed)
                raw_result = sim.evaluate(f"{query}\n{response}\n{sample_index}")
            else:
                raw_result = self._evaluate_sync(query, response, context)
            samples.append(self._normalize_sample(raw_result))

        summary = self._summarize_samples(samples)
        score = summary.mean_score
        passed = score >= 0.7 and summary.valid_sample_count > 0
        # Preserve the first sample's legacy fields, then add calibration data.
        result = samples[0].model_dump(mode="json") if samples else {}
        result["score"] = score
        result["criteria_scores"] = result.pop("criterion_scores", {})
        result.update(summary.as_details())
        return JudgeResult(
            passed=passed,
            score=score,
            details=result,
        )

    @staticmethod
    def _stable_seed(test_case_id: str, sample_index: int) -> int:
        """Derive a process-independent seed for an offline sample."""

        digest = hashlib.sha256(f"{test_case_id}:{sample_index}".encode()).digest()
        return int.from_bytes(digest[:8], "big") % (2**31)

    @staticmethod
    def _normalize_value(value: Any) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        if numeric > 1.0:
            numeric /= 10.0
        return max(0.0, min(numeric, 1.0))

    def _normalize_sample(self, raw: dict[str, Any]) -> JudgeSample:
        error = raw.get("error")
        criteria = raw.get("criteria_scores", raw.get("criterion_scores", {}))
        if not isinstance(criteria, dict):
            criteria = {}
        return JudgeSample(
            score=self._normalize_value(raw.get("score", 0.0)),
            criterion_scores={
                str(key): self._normalize_value(value)
                for key, value in criteria.items()
                if isinstance(value, (int, float, str))
            },
            reasoning=str(raw.get("reasoning", "")),
            method=str(raw.get("method", "unknown")),
            error=str(error) if error else None,
            provider=str(raw["provider"]) if raw.get("provider") else None,
            model=str(raw["model"]) if raw.get("model") else None,
            usage={
                str(key): int(value)
                for key, value in (raw.get("usage") or {}).items()
                if isinstance(value, (int, float))
            },
            cache_hit=raw.get("cache_hit")
            if isinstance(raw.get("cache_hit"), bool)
            else None,
            fallback_path=str(raw["fallback_path"])
            if raw.get("fallback_path")
            else None,
        )

    def _summarize_samples(self, samples: list[JudgeSample]) -> CalibrationSummary:
        valid = [sample for sample in samples if sample.valid]
        scores = [sample.score for sample in valid]
        mean_score = statistics.fmean(scores) if scores else 0.0
        stddev = statistics.pstdev(scores) if len(scores) > 1 else 0.0
        spread = max(scores) - min(scores) if len(scores) > 1 else 0.0
        agreement = "high" if spread < 0.2 else "medium" if spread < 0.4 else "low"
        criteria: dict[str, list[float]] = {}
        for sample in valid:
            for key, value in sample.criterion_scores.items():
                criteria.setdefault(key, []).append(value)
        criterion_aggregates = {
            key: round(statistics.fmean(values), 6)
            for key, values in sorted(criteria.items())
        }
        return CalibrationSummary(
            sample_count=len(samples),
            valid_sample_count=len(valid),
            mean_score=round(mean_score, 6),
            standard_deviation=round(stddev, 6),
            agreement=agreement,
            uncertainty=round(stddev, 6),
            samples=samples,
            criterion_aggregates=criterion_aggregates,
            errors=[sample.error for sample in samples if sample.error],
        )

    def _default_criteria(self) -> str:
        """Default evaluation criteria."""
        return """Evaluate the response based on:
1. Accuracy: Is the information correct?
2. Completeness: Does it answer all parts of the question?
3. Clarity: Is it well-structured and easy to understand?
4. Relevance: Does it stay on topic?

Provide a score from 1-10 and brief justification."""

    def _get_client(self) -> Any:
        """Get or create LLM client."""
        if self._client is None:
            if "claude" in self.model.lower():
                import anthropic

                self._client = anthropic.Anthropic(api_key=self.api_key)
            else:
                from openai import OpenAI

                self._client = OpenAI(api_key=self.api_key)
        return self._client

    def _build_prompt(
        self, query: str, response: str, context: Any | None = None
    ) -> str:
        """Build evaluation prompt for the LLM judge.

        Args:
            query: Original query.
            response: Response to evaluate.
            context: Optional reference context.

        Returns:
            Formatted prompt string.
        """
        ctx = f"\nReference context: {context}" if context else ""
        return f"""{self.criteria}

Query: {query}{ctx}

Response: {response}

Provide a score from 1-10 and brief justification."""

    def _evaluate_sync(
        self,
        query: str,
        response: str,
        context: Any | None = None,
    ) -> dict[str, Any]:
        """Evaluate a response using LLM (synchronous, real mode only).

        Args:
            query: Original query.
            response: Response to evaluate.
            context: Optional reference context.

        Returns:
            Evaluation result with score and reasoning.
        """
        prompt = self._build_prompt(query, response, context)

        try:
            result = asyncio.run(self._evaluate_with_factory(prompt))

            return {
                "score": result["score"],
                "reasoning": result["reasoning"],
                "criteria_scores": result.get("criteria_scores", {}),
                "method": "llm_single",
                **{
                    key: result[key]
                    for key in (
                        "provider",
                        "model",
                        "usage",
                        "fallback_path",
                        "cache_hit",
                    )
                    if key in result
                },
            }

        except Exception as e:
            return {
                "score": 0.0,
                "error": str(e),
                "method": "llm_single",
            }

    async def _evaluate_with_openai(self, prompt: str) -> dict[str, Any]:
        """Evaluate using OpenAI API.

        Args:
            prompt: Evaluation prompt.

        Returns:
            Parsed evaluation result.
        """
        client = self._get_client()

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=500,
        )

        content = response.choices[0].message.content or ""
        return self._parse_evaluation(content)

    async def _evaluate_with_anthropic(self, prompt: str) -> dict[str, Any]:
        """Evaluate using Anthropic API.

        Args:
            prompt: Evaluation prompt.

        Returns:
            Parsed evaluation result.
        """
        client = self._get_client()

        response = await asyncio.to_thread(
            client.messages.create,
            model=self.model,
            max_tokens=500,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text if response.content else ""
        return self._parse_evaluation(content)

    def _parse_evaluation(self, content: str) -> dict[str, Any]:  # noqa: C901
        """Parse LLM evaluation response.

        Args:
            content: LLM response text.

        Returns:
            Parsed result with score and reasoning.
        """
        stripped = content.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines and lines[0].lstrip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            stripped = "\n".join(lines).strip()
        try:
            structured = json.loads(stripped)
        except (json.JSONDecodeError, TypeError):
            structured = None
        if isinstance(structured, dict) and "score" in structured:
            raw_score = structured.get("score")
            try:
                if isinstance(raw_score, bool) or not isinstance(
                    raw_score, (int, float, str)
                ):
                    raise ValueError
                float(raw_score)
            except (TypeError, ValueError):
                return {
                    "score": 0.0,
                    "reasoning": str(structured.get("reasoning", "")),
                    "criteria_scores": {},
                    "method": structured.get("method", "json"),
                    "error": "Malformed evaluation output",
                }
            criteria = structured.get(
                "criteria_scores", structured.get("criterion_scores", {})
            )
            return {
                "score": structured.get("score", 0.0),
                "reasoning": structured.get(
                    "reasoning", structured.get("justification", "")
                ),
                "criteria_scores": criteria if isinstance(criteria, dict) else {},
                "method": structured.get("method", "json"),
                **({"error": structured["error"]} if structured.get("error") else {}),
            }

        lines = stripped.split("\n")

        result: dict[str, Any] = {
            "score": 5.0,
            "reasoning": "",
            "criteria_scores": {},
            "method": "line",
        }
        parsed_field = False

        # Extract overall score
        for line in lines:
            if line.lower().startswith("score:"):
                try:
                    score_str = line.split(":")[1].strip()
                    result["score"] = float(score_str.split()[0])
                    parsed_field = True
                except (ValueError, IndexError):
                    pass

            # Extract justification
            elif line.lower().startswith("justification:"):
                result["reasoning"] = line.split(":", 1)[1].strip()
                parsed_field = True

            # Extract criteria scores
            elif "accuracy:" in line.lower():
                try:
                    result["criteria_scores"]["accuracy"] = float(
                        line.split(":")[1].strip()
                    )
                    parsed_field = True
                except (ValueError, IndexError):
                    pass
            elif "completeness:" in line.lower():
                try:
                    result["criteria_scores"]["completeness"] = float(
                        line.split(":")[1].strip()
                    )
                    parsed_field = True
                except (ValueError, IndexError):
                    pass
            elif "clarity:" in line.lower():
                try:
                    result["criteria_scores"]["clarity"] = float(
                        line.split(":")[1].strip()
                    )
                    parsed_field = True
                except (ValueError, IndexError):
                    pass
            elif "relevance:" in line.lower():
                try:
                    result["criteria_scores"]["relevance"] = float(
                        line.split(":")[1].strip()
                    )
                    parsed_field = True
                except (ValueError, IndexError):
                    pass

        if not parsed_field:
            return {
                "score": 0.0,
                "reasoning": "",
                "criteria_scores": {},
                "method": "line",
                "error": "Malformed evaluation output",
            }
        return result

    async def _evaluate_with_factory(self, prompt: str) -> dict[str, Any]:
        """Complete through the local provider-neutral client factory."""

        provider = "anthropic" if "claude" in self.model.lower() else "openai"
        client = self._client_factory.create(
            provider=provider,
            model=self.model,
            api_key=self.api_key,
        )
        completion = await client.complete(
            prompt,
            temperature=self.temperature,
            max_tokens=500,
        )
        parsed = self._parse_evaluation(completion.content)
        parsed["provider"] = completion.provider
        parsed["model"] = completion.model
        parsed["usage"] = completion.usage
        parsed["fallback_path"] = completion.fallback_path
        parsed["cache_hit"] = completion.cache_hit
        return parsed


class EnsembleJudge(BaseJudge):
    """Ensemble of multiple judges with weighted averaging.

    Combines multiple judges for more robust evaluation.
    """

    def __init__(
        self, judges: list[BaseJudge], weights: list[float] | None = None
    ) -> None:
        """Initialize ensemble judge.

        Args:
            judges: List of judges to ensemble.
            weights: Optional weights for each judge.
        """
        self.judges = judges
        self.weights = weights or [1.0] * len(judges)

    def judge(self, test_case: TestCase, response: str) -> JudgeResult:
        """Evaluate response using ensemble of judges.

        Args:
            test_case: The test case defining expected behavior.
            response: Response to evaluate.

        Returns:
            JudgeResult with weighted ensemble score.
        """
        results: list[JudgeResult] = []
        for judge in self.judges:
            try:
                result = judge.judge(test_case, response)
                results.append(result)
            except Exception as exc:
                results.append(
                    JudgeResult(passed=False, score=0.0, details={"error": str(exc)})
                )

        # Weighted average of scores
        valid = [
            (r, w)
            for r, w in zip(results, self.weights, strict=False)
            if "error" not in r.details
        ]
        if not valid:
            return JudgeResult(
                passed=False,
                score=0.0,
                details={
                    "error": "All judges failed",
                    "individual_results": [r.details for r in results],
                },
            )

        total_weight = sum(w for _, w in valid)
        weighted_score = sum(r.score * w for r, w in valid) / total_weight

        scores = [r.score for r, _ in valid]
        variance = max(scores) - min(scores) if len(scores) > 1 else 0.0
        passed = weighted_score >= 0.7

        return JudgeResult(
            passed=passed,
            score=round(weighted_score, 3),
            details={
                "variance": round(variance, 3),
                "agreement": "high"
                if variance < 0.2
                else "medium"
                if variance < 0.4
                else "low",
                "individual_results": [r.details for r in results],
                "method": "ensemble",
            },
        )
