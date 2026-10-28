"""Markdown report generator."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from evalforge.models.report import Report
from evalforge.reporters.base import BaseReporter


class MarkdownReporter(BaseReporter):
    """Generates a formatted Markdown evaluation report.

    Produces a human-readable report with summary statistics,
    a results table, and detailed information for failed tests.
    """

    def generate(self, report: Report, output_path: Path) -> Path:
        """Generate a Markdown report file.

        Args:
            report: The evaluation report to render.
            output_path: Directory for the output file.

        Returns:
            Path to the generated Markdown file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        lines: list[str] = []
        lines.append(f"# Evaluation Report: {report.suite_name}")
        lines.append("")
        lines.append(f"**Generated**: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        lines.append("## Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total | {report.summary.total} |")
        lines.append(f"| Passed | {report.summary.passed} |")
        lines.append(f"| Failed | {report.summary.failed} |")
        lines.append(f"| Skipped | {report.summary.skipped} |")
        lines.append(f"| Pass Rate | {report.summary.pass_rate:.1%} |")
        lines.append(f"| Avg Score | {report.summary.avg_score:.2f} |")
        lines.append("")

        lines.append("## Results")
        lines.append("")
        lines.append("| ID | Name | Status | Score | Time (ms) |")
        lines.append("|----|------|--------|-------|-----------|")

        for result in report.results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(
                f"| {result.test_case_id} "
                f"| {result.test_case_name} "
                f"| {status} "
                f"| {result.score:.2f} "
                f"| {result.execution_time_ms:.0f} |"
            )

        lines.append("")

        failed_results = [r for r in report.results if not r.passed]
        if failed_results:
            lines.append("## Failed Tests Detail")
            lines.append("")
            for result in failed_results:
                lines.append(f"### {result.test_case_id}: {result.test_case_name}")
                lines.append("")
                lines.append(f"- **Score**: {result.score:.2f}")
                if result.error:
                    lines.append(f"- **Error**: {result.error}")
                if result.actual_response:
                    lines.append(f"- **Response**: {result.actual_response[:500]}")
                if result.judge_details:
                    lines.append(f"- **Judge Details**: {result.judge_details}")
                lines.append("")

        if report.metadata:
            lines.append("## Metadata")
            lines.append("")
            for key, value in report.metadata.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        return self._write_text(
            output_path, report.suite_name, timestamp, ".md", "\n".join(lines)
        )
