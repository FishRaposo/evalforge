"""Compatibility aliases for report persistence contracts."""

from evalforge.core.contracts import ReportRepository
from evalforge.core.repository import SQLiteReportRepository

__all__ = ["ReportRepository", "SQLiteReportRepository"]
