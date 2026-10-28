"""Abstract base class for report generators."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from itertools import count
from pathlib import Path, PureWindowsPath

from evalforge.models.report import Report


class BaseReporter(ABC):
    """Abstract base class for all report generators.

    Reporters transform evaluation results into formatted output
    files in various formats.
    """

    @staticmethod
    def _write_text(
        output_path: Path, suite_name: str, timestamp: str, suffix: str, content: str
    ) -> Path:
        """Treat the display name as one portable filename and never replace a run."""
        output_path.mkdir(parents=True, exist_ok=True)
        name = re.sub(
            r'[<>:"/\\|?*\x00-\x1f]', "_", suite_name.replace(" ", "_").lower()
        )
        name = name.strip(". ") or "evaluation"
        stem = f"{name}_{timestamp}"
        if PureWindowsPath(f"{stem}{suffix}").is_reserved():
            stem = f"_{stem}"
        for index in count():
            collision = f"_{index}" if index else ""
            path = output_path / f"{stem}{collision}{suffix}"
            try:
                with path.open("x", encoding="utf-8") as handle:
                    handle.write(content)
                return path
            except FileExistsError:
                continue
        raise AssertionError("Unreachable")

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
