"""Report persistence compatibility imports."""

from evalforge.core.contracts import ReportRepository
from evalforge.core.repository import SQLiteReportRepository

__all__ = ["ReportRepository", "SQLiteReportRepository"]
