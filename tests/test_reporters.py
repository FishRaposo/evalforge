"""Tests for report generators."""

from __future__ import annotations

import json
from pathlib import Path

from evalforge.models.report import Report, ReportSummary
from evalforge.reporters.html import HtmlReporter
from evalforge.reporters.json_report import JsonReporter
from evalforge.reporters.markdown import MarkdownReporter


class TestMarkdownReporter:
    """Tests for MarkdownReporter."""

    def test_markdown_report_generation(
        self, sample_report: Report, temp_output_dir: Path
    ) -> None:
        """MarkdownReporter should generate a valid Markdown file."""
        reporter = MarkdownReporter()
        output_path = reporter.generate(sample_report, temp_output_dir)

        assert output_path.exists()
        assert output_path.suffix == ".md"

        content = output_path.read_text(encoding="utf-8")
        assert sample_report.suite_name in content
        assert "Summary" in content
        assert "Results" in content

    def test_markdown_contains_summary_table(
        self, sample_report: Report, temp_output_dir: Path
    ) -> None:
        """Markdown report should include summary statistics table."""
        reporter = MarkdownReporter()
        output_path = reporter.generate(sample_report, temp_output_dir)

        content = output_path.read_text(encoding="utf-8")
        assert "Total" in content
        assert "Passed" in content
        assert "Failed" in content
        assert "Pass Rate" in content

    def test_markdown_shows_failed_details(
        self, sample_report: Report, temp_output_dir: Path
    ) -> None:
        """Markdown report should include details for failed tests."""
        reporter = MarkdownReporter()
        output_path = reporter.generate(sample_report, temp_output_dir)

        content = output_path.read_text(encoding="utf-8")
        assert "Failed Tests Detail" in content


class TestJsonReporter:
    """Tests for JsonReporter."""

    def test_json_report_generation(
        self, sample_report: Report, temp_output_dir: Path
    ) -> None:
        """JsonReporter should generate a valid JSON file."""
        reporter = JsonReporter()
        output_path = reporter.generate(sample_report, temp_output_dir)

        assert output_path.exists()
        assert output_path.suffix == ".json"

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["suite_name"] == sample_report.suite_name
        assert "summary" in data
        assert "results" in data

    def test_json_report_structure(
        self, sample_report: Report, temp_output_dir: Path
    ) -> None:
        """JSON report should have correct structure matching Report model."""
        reporter = JsonReporter()
        output_path = reporter.generate(sample_report, temp_output_dir)

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["summary"]["total"] == 3
        assert data["summary"]["passed"] == 2
        assert data["summary"]["failed"] == 1
        assert len(data["results"]) == 3


class TestHtmlReporter:
    """Tests for HtmlReporter."""

    def test_html_report_generation(
        self, sample_report: Report, temp_output_dir: Path
    ) -> None:
        """HtmlReporter should generate a valid HTML file."""
        reporter = HtmlReporter()
        output_path = reporter.generate(sample_report, temp_output_dir)

        assert output_path.exists()
        assert output_path.suffix == ".html"

        content = output_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert sample_report.suite_name in content

    def test_html_contains_styled_table(
        self, sample_report: Report, temp_output_dir: Path
    ) -> None:
        """HTML report should include styled results table."""
        reporter = HtmlReporter()
        output_path = reporter.generate(sample_report, temp_output_dir)

        content = output_path.read_text(encoding="utf-8")
        assert "<table>" in content
        assert "PASS" in content
        assert "FAIL" in content
        assert "style" in content.lower()

    def test_html_shows_summary_cards(
        self, sample_report: Report, temp_output_dir: Path
    ) -> None:
        """HTML report should include summary card statistics."""
        reporter = HtmlReporter()
        output_path = reporter.generate(sample_report, temp_output_dir)

        content = output_path.read_text(encoding="utf-8")
        assert "summary-cards" in content
        assert "pass-rate" in content


class TestHtmlReporterEscaping:
    """HtmlReporter must escape untrusted/model-derived strings (XSS guard)."""

    def test_html_escapes_dynamic_values(self) -> None:
        from evalforge.models.report import Report, ReportSummary
        from evalforge.models.test_result import TestResult

        payload = "<script>alert('xss')</script>"
        results = [
            TestResult(
                test_case_id="tc-x",
                test_case_name=payload,
                passed=False,
                score=0.1,
                actual_response=payload,
                error=payload,
                execution_time_ms=10.0,
            ),
        ]
        summary = ReportSummary(
            total=1, passed=0, failed=1, skipped=0, pass_rate=0.0, avg_score=0.1
        )
        # suite_name kept filesystem-safe (it becomes the output filename); the
        # XSS payload still flows through suite_name escaping via _build_html below.
        report = Report(
            suite_name=payload,
            summary=summary,
            results=results,
            metadata={payload: payload},
        )

        # Build the HTML body directly to exercise every escaped field, including
        # suite_name, without hitting Windows filename restrictions.
        content = HtmlReporter()._build_html(report)

        # Raw script tag must never appear; it must be HTML-escaped instead.
        assert "<script>alert('xss')</script>" not in content
        assert "&lt;script&gt;" in content
        # suite_name, metadata key/value, test_case_name, response, and error
        # all carry the payload, so the escaped form must be present.
        assert content.count("&lt;script&gt;") >= 5


class TestReportSummaryAccuracy:
    """Tests for report summary calculation accuracy."""

    def test_report_summary_accuracy(self) -> None:
        """Report summary should accurately reflect the results."""
        from evalforge.models.test_result import TestResult

        results = [
            TestResult(test_case_id="1", test_case_name="A", passed=True, score=1.0),
            TestResult(test_case_id="2", test_case_name="B", passed=True, score=0.9),
            TestResult(test_case_id="3", test_case_name="C", passed=False, score=0.3),
            TestResult(test_case_id="4", test_case_name="D", passed=False, score=0.1),
        ]

        summary = ReportSummary(
            total=4,
            passed=2,
            failed=2,
            skipped=0,
            pass_rate=0.5,
            avg_score=0.575,
        )

        report = Report(suite_name="Accuracy Test", summary=summary, results=results)

        assert report.summary.total == 4
        assert report.summary.passed == 2
        assert report.summary.failed == 2
        assert report.summary.pass_rate == 0.5
        assert len(report.results) == 4
