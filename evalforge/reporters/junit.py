"""JUnit XML reporter for CI integration."""

from __future__ import annotations

from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring

from evalforge.models.report import Report


class JUnitReporter:
    """Generate JUnit XML from an EvalForge report.

    Compatible with Jenkins, GitLab CI, and other JUnit-consuming tools.
    """

    def generate(self, report: Report) -> str:
        """Generate JUnit XML string.

        Args:
            report: The evaluation report.

        Returns:
            JUnit XML string.
        """
        testsuites = Element("testsuites")
        testsuite = SubElement(
            testsuites,
            "testsuite",
            {
                "name": report.suite_name,
                "tests": str(report.summary.total),
                "failures": str(report.summary.failed),
                "errors": "0",
                "timestamp": datetime.now().isoformat(),
            },
        )

        for result in report.results:
            testcase = SubElement(
                testsuite,
                "testcase",
                {
                    "name": result.test_case_name or result.test_case_id,
                    "time": f"{result.execution_time_ms / 1000:.3f}",
                },
            )
            if not result.passed:
                failure = SubElement(testcase, "failure")
                failure.text = result.error or f"Score {result.score:.2f} below threshold"

        return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(testsuites, encoding="unicode")

    def save(self, report: Report, path: str) -> str:
        """Save JUnit XML to file.

        Args:
            report: The evaluation report.
            path: Output file path.

        Returns:
            The output file path.
        """
        xml = self.generate(report)
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml)
        return path
