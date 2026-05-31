"""LLM-as-Judge implementation for evaluation.

Uses LLM to evaluate response quality with structured criteria.
Supports self-consistency scoring and ensemble judging.
"""

from __future__ import annotations

import asyncio
from typing import Any

from evalforge.judges.base import BaseJudge


class LLMJudge(Judge):
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
        self._client = None
    
    async def judge(self, test_case: Any, response: str) -> Any:
        """Evaluate response (implements BaseJudge interface).
        
        Args:
            test_case: Test case with query.
            response: Response to evaluate.
            
        Returns:
            JudgeResult with evaluation.
        """
        from evalforge.judges.base import JudgeResult
        
        query = getattr(test_case, 'query', '') or test_case.get('query', '')
        context = getattr(test_case, 'expected_citations', None) or test_case.get('expected_citations')
        
        result = await self.evaluate(query, response, context)
        
        return JudgeResult(
            passed=result.get('score', 0) >= 0.7,
            score=result.get('score', 0) / 10,  # Normalize to 0-1
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
    
    async def evaluate(
        self,
        query: str,
        response: str,
        context: str | None = None,
    ) -> dict[str, Any]:
        """Evaluate a response using LLM.
        
        Args:
            query: Original query.
            response: Response to evaluate.
            context: Optional reference context.
            
        Returns:
            Evaluation result with score and reasoning.
        """
        if self.num_samples > 1:
            # Self-consistency: evaluate multiple times
            scores = []
            for _ in range(self.num_samples):
                result = await self._single_evaluation(query, response, context)
                scores.append(result["score"])
            
            # Average scores
            avg_score = sum(scores) / len(scores)
            variance = max(scores) - min(scores)
            
            return {
                "score": round(avg_score, 2),
                "individual_scores": scores,
                "variance": round(variance, 2),
                "consistency": "high" if variance < 2 else "medium" if variance < 4 else "low",
                "method": "llm_self_consistency",
            }
        else:
            return await self._single_evaluation(query, response, context)
    
    async def _single_evaluation(
        self,
        query: str,
        response: str,
        context: str | None,
    ) -> dict[str, Any]:
        """Single LLM evaluation.
        
        Args:
            query: Original query.
            response: Response to evaluate.
            context: Optional reference context.
            
        Returns:
            Evaluation result.
        """
        prompt = self._build_prompt(query, response, context)
        
        try:
            if "claude" in self.model.lower():
                result = await self._evaluate_with_anthropic(prompt)
            else:
                result = await self._evaluate_with_openai(prompt)
            
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
    
    def _build_prompt(
        self,
        query: str,
        response: str,
        context: str | None,
    ) -> str:
        """Build evaluation prompt.
        
        Args:
            query: Original query.
            response: Response to evaluate.
            context: Optional reference context.
            
        Returns:
            Evaluation prompt.
        """
        prompt_parts = [
            "You are an expert evaluator. Evaluate the following response.\n",
            f"Query: {query}\n",
        ]
        
        if context:
            prompt_parts.append(f"Reference Context: {context[:1000]}\n")
        
        prompt_parts.extend([
            f"Response to Evaluate: {response[:2000]}\n",
            f"Evaluation Criteria: {self.criteria}\n",
            """Provide your evaluation in this exact format:
Score: [1-10]
Justification: [Your reasoning]
Criteria Scores:
- Accuracy: [1-10]
- Completeness: [1-10]
- Clarity: [1-10]
- Relevance: [1-10]""",
        ])
        
        return "\n".join(prompt_parts)
    
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
    """Ensemble of multiple judges with majority voting.
    
    Combines multiple judges (LLM, rule-based, etc.) for
    more robust evaluation.
    """
    
    def __init__(self, judges: list[BaseJudge], weights: list[float] | None = None) -> None:
        """Initialize ensemble judge.
        
        Args:
            judges: List of judges to ensemble.
            weights: Optional weights for each judge.
        """
        self.judges = judges
        self.weights = weights or [1.0] * len(judges)
    
    async def judge(self, test_case: Any, response: str) -> Any:
        """Evaluate response (implements BaseJudge interface).
        
        Args:
            test_case: Test case with query.
            response: Response to evaluate.
            
        Returns:
            JudgeResult with evaluation.
        """
        from evalforge.judges.base import JudgeResult
        
        query = getattr(test_case, 'query', '') or test_case.get('query', '')
        context = getattr(test_case, 'expected_citations', None) or test_case.get('expected_citations')
        
        result = await self.evaluate(query, response, context)
        
        return JudgeResult(
            passed=result.get('score', 0) >= 0.7,
            score=result.get('score', 0) / 10,
            details=result,
        )
    
    async def evaluate(
        self,
        query: str,
        response: str,
        context: str | None = None,
    ) -> dict[str, Any]:
        """Evaluate using ensemble of judges.
        
        Args:
            query: Original query.
            response: Response to evaluate.
            context: Optional reference context.
            
        Returns:
            Ensemble evaluation result.
        """
        # Get evaluations from all judges
        evaluations = []
        for judge in self.judges:
            try:
                eval_result = await judge.evaluate(query, response, context)
                evaluations.append(eval_result)
            except Exception as e:
                evaluations.append({"score": 0.0, "error": str(e)})
        
        # Calculate weighted average
        valid_scores = [
            (e["score"], w)
            for e, w in zip(evaluations, self.weights)
            if "score" in e and "error" not in e
        ]
        
        if not valid_scores:
            return {
                "score": 0.0,
                "error": "All judges failed",
                "individual_results": evaluations,
            }
        
        total_weight = sum(w for _, w in valid_scores)
        weighted_score = sum(s * w for s, w in valid_scores) / total_weight
        
        # Calculate variance for consistency check
        scores = [s for s, _ in valid_scores]
        variance = max(scores) - min(scores) if len(scores) > 1 else 0
        
        return {
            "score": round(weighted_score, 2),
            "variance": round(variance, 2),
            "agreement": "high" if variance < 2 else "medium" if variance < 4 else "low",
            "individual_results": evaluations,
            "method": "ensemble",
        }
