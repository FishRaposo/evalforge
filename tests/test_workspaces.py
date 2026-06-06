"""Tests for WorkspaceManager."""

from __future__ import annotations

from pathlib import Path

import pytest

from evalforge.workspaces.manager import WorkspaceManager


class TestWorkspaceManager:
    """Tests for WorkspaceManager."""

    @pytest.fixture
    def workspace_root(self, tmp_path: Path) -> Path:
        return tmp_path / "workspaces"

    def test_init_and_list_workspaces(self, workspace_root: Path) -> None:
        manager = WorkspaceManager(root=str(workspace_root))
        assert manager.list_workspaces() == []

        db1 = manager.init("project-a")
        assert db1.exists()
        assert manager.list_workspaces() == ["project-a"]

        db2 = manager.init("project-b")
        assert db2.exists()
        assert sorted(manager.list_workspaces()) == ["project-a", "project-b"]

    def test_active_workspace(self, workspace_root: Path) -> None:
        manager = WorkspaceManager(root=str(workspace_root))
        assert manager.get_active() is None

        manager.init("my-project")
        manager.set_active("my-project")
        assert manager.get_active() == "my-project"

        with pytest.raises(ValueError, match="does not exist"):
            manager.set_active("nonexistent-workspace")
