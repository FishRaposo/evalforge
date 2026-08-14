"""Report repository facade over the compatible SQLite history schema."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from evalforge.models.report import Report
from evalforge.storage.history import HistoryStore


class SQLiteReportRepository:
    """Repository interface that preserves ``HistoryStore`` round trips."""

    def __init__(self, db_path: str = "evalforge_history.db") -> None:
        self.store = HistoryStore(db_path)

    @staticmethod
    def _payload(report: Report | Mapping[str, Any]) -> dict[str, Any]:
        if isinstance(report, Report):
            return report.model_dump(mode="json")
        return dict(report)

    def save(self, report: Report | Mapping[str, Any]) -> int:
        return self.store.save_run(self._payload(report))

    save_report = save

    def get(self, run_id: int) -> dict[str, Any] | None:
        return self.store.get_run(run_id)

    get_run = get

    def list(
        self, suite_name: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        return self.store.get_runs(suite_name=suite_name, limit=limit)

    get_runs = list

    def set_baseline(self, suite_name: str, report: Report | Mapping[str, Any]) -> None:
        self.store.set_baseline(suite_name, self._payload(report))

    def get_baseline(self, suite_name: str) -> dict[str, Any] | None:
        return self.store.get_baseline(suite_name)
