"""SARIF reporter for static analysis tool integration."""

from __future__ import annotations

from typing import Any

from evalforge.models.report import Report


class SARIFReporter:
    """Generate SARIF output from an EvalForge report.

    Useful for integrating with GitHub Advanced Security and other
    SARIF-consuming platforms.
    """

    def generate(self, report: Report) -> dict[str, Any]:
        """Generate SARIF JSON dictionary.

        Args:
            report: The evaluation report.

        Returns:
            SARIF-compliant dictionary.
        """
        results: list[dict[str, Any]] = []
        for r in report.results:
            if not r.passed:
                results.append({
                    "ruleId": "evalforge/failed-test",
                    "message": {
                        "text": r.error or f"Test {r.test_case_id} failed with score {r.score:.2f}",
                    },
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": "suite.yaml"},
                                "region": {"startLine": 1},
                            }
                        }
                    ],
                })

        return {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "EvalForge",
                            "informationUri": "https://github.com/evalforge/evalforge",
                        }
                    },
                    "results": results,
                }
            ],
        }

    def save(self, report: Report, path: str) -> str:
        """Save SARIF JSON to file.

        Args:
            report: The evaluation report.
            path: Output file path.

        Returns:
            The output file path.
        """
        import json
        data = self.generate(report)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return path
