"""Compliance judge for EvalForge evaluation framework.

Integrates the compliance rule engine as an EvalForge judge,
so compliance checks can be run alongside LLM-as-judge and heuristic evaluators.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from evalforge.judges.base import BaseJudge, JudgeResult
from evalforge.models.test_case import TestCase

from .engine import ComplianceEngine


class ComplianceJudge(BaseJudge):
    """Judge that evaluates responses against compliance rule packs.

    Usage:
        judge = ComplianceJudge(rule_pack_path="rule_packs/ai_ethics.yaml")
        result = judge.judge(test_case, response)
    """

    def __init__(self, rule_pack_path: str | Path) -> None:
        """Initialize with a rule pack.

        Args:
            rule_pack_path: Path to YAML rule pack.
        """
        self.engine = ComplianceEngine(rule_pack_path)

    def judge(self, test_case: TestCase, response: str) -> JudgeResult:
        """Evaluate a response against compliance rules.

        Args:
            test_case: Test case with metadata.
            response: AI-generated response text.

        Returns:
            JudgeResult with pass/fail and compliance score.
        """
        # Build content from test case metadata + response
        content: dict[str, Any] = {"text": response}
        if test_case.metadata:
            content.update(test_case.metadata)

        report = self.engine.evaluate(content)

        # Pass if score >= 0.8 and no critical failures
        critical_failures = [
            r for r in report.results if not r.passed and r.severity == "critical"
        ]
        passed = report.score >= 0.8 and len(critical_failures) == 0

        return JudgeResult(
            passed=passed,
            score=report.score,
            details={
                "standard_id": report.standard_id,
                "standard_name": report.standard_name,
                "total_rules": report.total_rules,
                "passed_rules": report.passed_rules,
                "failed_rules": report.failed_rules,
                "summary": report.summary,
                "results": [
                    {
                        "rule_id": r.rule_id,
                        "passed": r.passed,
                        "severity": r.severity,
                        "message": r.message,
                        "field": r.field,
                    }
                    for r in report.results
                ],
                "critical_failures": len(critical_failures),
            },
        )
