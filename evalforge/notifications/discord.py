"""Discord webhook notification sender.

Offline-first: no-op when no webhook URL is configured.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("evalforge.notifications")


class DiscordNotifier:
    """Send evaluation summaries to Discord via webhook."""

    def __init__(self, webhook_url: str | None = None) -> None:
        self._url = webhook_url or os.getenv("EVALFORGE_DISCORD_WEBHOOK")

    async def send(self, report: dict[str, Any]) -> bool:
        """Send a report summary to Discord.

        Args:
            report: Evaluation report dict.

        Returns:
            True if sent (or skipped in offline mode).
        """
        if not self._url:
            logger.info("Discord webhook not configured; skipping notification")
            return True

        summary = report.get("summary", {})
        payload = {
            "content": (
                f"**EvalForge Report: {report.get('suite_name', 'Unknown')}**\n"
                f"Passed: {summary.get('passed', 0)} / {summary.get('total', summary.get('total_tests', 0))}\n"
                f"Pass Rate: {summary.get('pass_rate', 0.0):.1%}\n"
                f"Avg Score: {summary.get('avg_score', 0.0):.2f}"
            ),
        }

        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(self._url, json=payload, timeout=30.0)
            return response.status_code == 204
