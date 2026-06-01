"""Simple cron-like scheduler for recurring evaluations.

Uses APScheduler when available, otherwise logs a warning and runs
immediately (useful for testing and offline environments).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("evalforge.scheduler")


class SimpleScheduler:
    """Schedule recurring evaluation jobs.

    If ``apscheduler`` is installed, it will be used for real scheduling.
    Otherwise jobs run immediately (offline/demo mode).
    """

    def __init__(self) -> None:
        self._scheduler: Any | None = None
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            self._scheduler = BackgroundScheduler()
            self._scheduler.start()
        except ImportError:
            logger.warning("apscheduler not installed; scheduled jobs will run immediately")

    def add_job(
        self,
        func: Callable[..., Any],
        trigger: str = "interval",
        **kwargs: Any,
    ) -> None:
        """Add a scheduled job.

        Args:
            func: The function to run.
            trigger: APScheduler trigger type (e.g. ``interval``, ``cron``).
            **kwargs: Trigger-specific arguments (e.g. ``minutes=30``).
        """
        if self._scheduler is not None:
            self._scheduler.add_job(func, trigger=trigger, **kwargs)
        else:
            logger.info("Running job immediately (offline mode)")
            func()

    def shutdown(self) -> None:
        """Stop the scheduler."""
        if self._scheduler is not None:
            self._scheduler.shutdown()
