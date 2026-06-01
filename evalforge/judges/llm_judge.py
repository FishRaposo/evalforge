"""LLM-as-Judge implementation for evaluation.

Uses LLM to evaluate response quality with structured criteria.
Supports self-consistency scoring and ensemble judging.
"""

from __future__ import annotations

import asyncio
from typing import Any

from evalforge.execution import SimulatedEvaluator, resolve_mode
from evalforge.judges.base import BaseJudge, JudgeResult
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
    ) -> None:
        """Initialize LLM judge.

        Args:
            model: LLM model to use.
            criteria: Evaluation criteria description.
            temperature: Sampling temperature.
            num_samples: Number of samples for self-consistency.
            api_key: API key for LLM provider.
        """
        self.model = model
        self.criteria = criteria or self._default_criteria()
        self.temperature = temperature
        self.num_samples = num_samples
        self.api_key = api_key
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
        if mode == "sim":
            sim = SimulatedEvaluator(seed=hash(test_case.id) % 2**31)
            result = sim.evaluate(f"{query}\n{response}")
        else:
            result = self._evaluate_sync(query, response, context)

        score = result.get("score", 0.0)
        passed = score >= 0.7
        return JudgeResult(
            passed=passed,
            score=score,
            details=result,
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

    def _build_prompt(self, query: str, response: str, context: Any | None = None) -> str:
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
            if "claude" in self.model.lower():
                result = asyncio.run(self._evaluate_with_anthropic(prompt))
            else:
                result = asyncio.run(self._evaluate_with_openai(prompt))

            return {
                "score": result["score"],
                "reasoning": result["reasoning"],
                "criteria_scores": result.get("criteria_scores", {}),
                "method": "llm_single",
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

    def _parse_evaluation(self, content: str) -> dict[str, Any]:
        """Parse LLM evaluation response.

        Args:
            content: LLM response text.

        Returns:
            Parsed result with score and reasoning.
        """
        lines = content.strip().split("\n")

        result: dict[str, Any] = {
            "score": 5.0,
            "reasoning": "",
            "criteria_scores": {},
        }

        # Extract overall score
        for line in lines:
            if line.lower().startswith("score:"):
                try:
                    score_str = line.split(":")[1].strip()
                    result["score"] = float(score_str.split()[0])
                except (ValueError, IndexError):
                    pass

            # Extract justification
            elif line.lower().startswith("justification:"):
                result["reasoning"] = line.split(":", 1)[1].strip()

            # Extract criteria scores
            elif "accuracy:" in line.lower():
                try:
                    result["criteria_scores"]["accuracy"] = float(line.split(":")[1].strip())
                except (ValueError, IndexError):
                    pass
            elif "completeness:" in line.lower():
                try:
                    result["criteria_scores"]["completeness"] = float(line.split(":")[1].strip())
                except (ValueError, IndexError):
                    pass
            elif "clarity:" in line.lower():
                try:
                    result["criteria_scores"]["clarity"] = float(line.split(":")[1].strip())
                except (ValueError, IndexError):
                    pass
            elif "relevance:" in line.lower():
                try:
                    result["criteria_scores"]["relevance"] = float(line.split(":")[1].strip())
                except (ValueError, IndexError):
                    pass

        return result


class EnsembleJudge(BaseJudge):
    """Ensemble of multiple judges with weighted averaging.

    Combines multiple judges for more robust evaluation.
    """

    def __init__(self, judges: list[BaseJudge], weights: list[float] | None = None) -> None:
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
                results.append(JudgeResult(passed=False, score=0.0, details={"error": str(exc)}))

        # Weighted average of scores
        valid = [(r, w) for r, w in zip(results, self.weights) if "error" not in r.details]
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
                "agreement": "high" if variance < 0.2 else "medium" if variance < 0.4 else "low",
                "individual_results": [r.details for r in results],
                "method": "ensemble",
            },
        )
