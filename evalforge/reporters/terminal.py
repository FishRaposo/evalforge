"""Terminal reporter with Rich tables and progress bars."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from evalforge.models.report import Report


class TerminalReporter:
    """Render an EvalForge report as rich terminal output."""

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or Console()

    def generate(self, report: Report) -> str:
        """Generate a rich text representation of the report.

        Args:
            report: The evaluation report.

        Returns:
            Plain-text representation.
        """
        total = report.summary.total
        passed = report.summary.passed
        failed = report.summary.failed
        pass_rate = report.summary.pass_rate
        avg_score = report.summary.avg_score
        lines: list[str] = [
            f"Suite: {report.suite_name}",
            f"Total: {total} | Passed: {passed} | Failed: {failed}",
            f"Pass Rate: {pass_rate:.1%} | Avg Score: {avg_score:.2f}",
            "",
        ]
        for r in report.results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"  [{status}] {r.test_case_id}: {r.test_case_name} (score={r.score:.2f})")
        return "\n".join(lines)

    def print(self, report: Report) -> None:
        """Print a rich table directly to the console.

        Args:
            report: The evaluation report.
        """
        self._console.print(f"\n[bold blue]{report.suite_name}[/bold blue]")
        self._console.print(
            f"Total: {report.summary.total} | "
            f"Passed: [green]{report.summary.passed}[/green] | "
            f"Failed: [red]{report.summary.failed}[/red]"
        )
        self._console.print(
            f"Pass Rate: {report.summary.pass_rate:.1%} | "
            f"Avg Score: {report.summary.avg_score:.2f}"
        )

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name")
        table.add_column("Status", justify="center")
        table.add_column("Score", justify="right")
        table.add_column("Time (ms)", justify="right")

        for r in report.results:
            status = "[green]PASS[/green]" if r.passed else "[red]FAIL[/red]"
            table.add_row(
                r.test_case_id,
                r.test_case_name,
                status,
                f"{r.score:.2f}",
                f"{r.execution_time_ms:.0f}",
            )

        self._console.print(table)
