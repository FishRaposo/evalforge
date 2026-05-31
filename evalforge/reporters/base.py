"""Abstract base class for report generators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from evalforge.models.report import Report


class BaseReporter(ABC):
    """Abstract base class for all report generators.

    Reporters transform evaluation results into formatted output
    files in various formats.
    """

    @abstractmethod
    def generate(self, report: Report, output_path: Path) -> Path:
        """Generate a report file from evaluation results.

        Args:
            report: The evaluation report with results and summary.
            output_path: Directory where the report file should be written.

        Returns:
            The path to the generated report file.
        """
        ...
