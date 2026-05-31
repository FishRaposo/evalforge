"""HTML report generator with styled tables."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from evalforge.models.report import Report
from evalforge.reporters.base import BaseReporter


class HtmlReporter(BaseReporter):
    """Generates a styled HTML evaluation report.

    Produces a self-contained HTML file with CSS styling,
    tables, and color-coded results for easy visualization.
    """

    def generate(self, report: Report, output_path: Path) -> Path:
        """Generate an HTML report file.

        Args:
            report: The evaluation report to render.
            output_path: Directory for the output file.

        Returns:
            Path to the generated HTML file.
        """
        output_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report.suite_name.replace(' ', '_').lower()}_{timestamp}.html"
        file_path = output_path / filename

        html = self._build_html(report)
        file_path.write_text(html, encoding="utf-8")
        return file_path

    def _build_html(self, report: Report) -> str:
        """Build the complete HTML report string.

        Args:
            report: The evaluation report data.

        Returns:
            A complete HTML document string.
        """
        summary = report.summary
        pass_color = "#4caf50" if summary.pass_rate >= 0.8 else "#ff9800" if summary.pass_rate >= 0.6 else "#f44336"

        rows_html = ""
        for result in report.results:
            status_class = "pass" if result.passed else "fail"
            status_text = "PASS" if result.passed else "FAIL"
            rows_html += f"""
            <tr>
                <td>{result.test_case_id}</td>
                <td>{result.test_case_name}</td>
                <td class="{status_class}">{status_text}</td>
                <td>{result.score:.2f}</td>
                <td>{result.execution_time_ms:.0f}</td>
            </tr>"""

        failed_rows = ""
        for result in report.results:
            if not result.passed:
                error_text = result.error or "N/A"
                response_text = (result.actual_response[:300] + "...") if len(result.actual_response) > 300 else result.actual_response
                failed_rows += f"""
            <div class="failed-test">
                <h3>{result.test_case_id}: {result.test_case_name}</h3>
                <p><strong>Score:</strong> {result.score:.2f}</p>
                <p><strong>Error:</strong> {error_text}</p>
                <p><strong>Response:</strong> {response_text}</p>
            </div>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EvalForge Report: {report.suite_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }}
        h1 {{ color: #1a1a2e; }}
        h2 {{ color: #16213e; border-bottom: 2px solid #0f3460; padding-bottom: 8px; }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .card h3 {{ margin: 0; color: #666; font-size: 0.85em; }}
        .card .value {{ font-size: 2em; font-weight: bold; margin: 8px 0 0; }}
        .card.pass-rate .value {{ color: {pass_color}; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background: #1a1a2e;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f8f9fa; }}
        .pass {{ color: #4caf50; font-weight: bold; }}
        .fail {{ color: #f44336; font-weight: bold; }}
        .failed-test {{
            background: white;
            border-left: 4px solid #f44336;
            padding: 16px;
            margin: 12px 0;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .failed-test h3 {{ margin-top: 0; color: #f44336; }}
        .metadata {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>EvalForge Report: {report.suite_name}</h1>
    <p class="metadata">Generated: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="summary-cards">
        <div class="card">
            <h3>Total</h3>
            <div class="value">{summary.total}</div>
        </div>
        <div class="card">
            <h3>Passed</h3>
            <div class="value" style="color: #4caf50;">{summary.passed}</div>
        </div>
        <div class="card">
            <h3>Failed</h3>
            <div class="value" style="color: #f44336;">{summary.failed}</div>
        </div>
        <div class="card pass-rate">
            <h3>Pass Rate</h3>
            <div class="value">{summary.pass_rate:.1%}</div>
        </div>
        <div class="card">
            <h3>Avg Score</h3>
            <div class="value">{summary.avg_score:.2f}</div>
        </div>
    </div>

    <h2>Results</h2>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Status</th>
                <th>Score</th>
                <th>Time (ms)</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    {"<h2>Failed Tests</h2>" + failed_rows if failed_rows else ""}

    <h2>Metadata</h2>
    <ul>
        {" ".join(f'<li><strong>{k}</strong>: {v}</li>' for k, v in report.metadata.items())}
    </ul>
</body>
</html>"""
