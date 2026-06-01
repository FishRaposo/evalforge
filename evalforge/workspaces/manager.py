"""Lightweight workspace manager backed by SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class WorkspaceManager:
    """Manage named workspaces with scoped suites and baselines.

    Each workspace gets its own SQLite database under ~/.evalforge/workspaces/.
    """

    def __init__(self, root: str | None = None) -> None:
        self._root = Path(root or Path.home() / ".evalforge" / "workspaces")
        self._root.mkdir(parents=True, exist_ok=True)

    def _db_path(self, name: str) -> Path:
        return self._root / f"{name}.db"

    def init(self, name: str) -> Path:
        """Create a new workspace.

        Args:
            name: Workspace name.

        Returns:
            Path to the workspace database.
        """
        db = self._db_path(name)
        with sqlite3.connect(str(db)) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS suites"
                " (name TEXT PRIMARY KEY, path TEXT, created_at TEXT)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS baselines"
                " (suite_name TEXT PRIMARY KEY, report_json TEXT, created_at TEXT)"
            )
        return db

    def list_workspaces(self) -> list[str]:
        """Return all workspace names."""
        return [p.stem for p in self._root.glob("*.db")]

    def get_active(self) -> str | None:
        """Return the active workspace name from ~/.evalforge/active_workspace."""
        marker = self._root.parent / "active_workspace"
        if marker.exists():
            return marker.read_text(encoding="utf-8").strip()
        return None

    def set_active(self, name: str) -> None:
        """Set the active workspace."""
        if not self._db_path(name).exists():
            raise ValueError(f"Workspace '{name}' does not exist")
        marker = self._root.parent / "active_workspace"
        marker.write_text(name, encoding="utf-8")
