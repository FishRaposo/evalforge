"""JSON report generator."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from evalforge.models.report import Report
from evalforge.reporters.base import BaseReporter


class JsonReporter(BaseReporter):
    """Generates a JSON evaluation report for programmatic consumption.

    Produces a structured JSON file with all evaluation data,
    suitable for CI integration and downstream tooling.
    """

    def generate(self, report: Report, output_path: Path) -> Path:
        """Generate a JSON report file.

        Args:
            report: The evaluation report to serialize.
            output_path: Directory for the output file.

        Returns:
            Path to the generated JSON file.
        """
        output_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report.suite_name.replace(' ', '_').lower()}_{timestamp}.json"
        file_path = output_path / filename

        report_data = report.model_dump(mode="json")
        file_path.write_text(
            Report.model_validate(report_data).model_dump_json(indent=2),
            encoding="utf-8",
        )
        return file_path
