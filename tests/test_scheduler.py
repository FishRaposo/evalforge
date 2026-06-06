"""Tests for SimpleScheduler."""

from __future__ import annotations

from unittest.mock import MagicMock

from evalforge.scheduler.cron import SimpleScheduler


class TestSimpleScheduler:
    """Tests for SimpleScheduler."""

    def test_scheduler_fallback_offline(self) -> None:
        # Test immediate execution when apscheduler is imported or mocked
        sched = SimpleScheduler()
        callback = MagicMock()

        # Test add job immediate execution (when fallback is active or real scheduler handles it)
        # We can mock out self._scheduler to simulate offline fallback
        sched._scheduler = None

        sched.add_job(callback, trigger="interval", minutes=60)
        callback.assert_called_once()

    def test_scheduler_shutdown(self) -> None:
        sched = SimpleScheduler()
        mock_scheduler = MagicMock()
        sched._scheduler = mock_scheduler

        sched.shutdown()
        mock_scheduler.shutdown.assert_called_once()
