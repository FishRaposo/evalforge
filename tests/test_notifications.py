"""Tests for Slack and Discord notifications."""

from __future__ import annotations

import httpx
import pytest

from evalforge.notifications.discord import DiscordNotifier
from evalforge.notifications.slack import SlackNotifier


class TestDiscordNotifier:
    """Tests for DiscordNotifier."""

    @pytest.mark.asyncio
    async def test_discord_skip_when_no_webhook(self) -> None:
        notifier = DiscordNotifier(webhook_url=None)
        # Should return True without raising exception or requesting HTTP
        res = await notifier.send({"suite_name": "Test"})
        assert res is True

    @pytest.mark.asyncio
    async def test_discord_send_success(self) -> None:
        notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/mock")
        report = {
            "suite_name": "basic_suite",
            "summary": {
                "total": 5,
                "passed": 4,
                "failed": 1,
                "pass_rate": 0.8,
                "avg_score": 0.75,
            },
        }

        # Mock transport
        async def _handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(204)  # Discord returns 204 No Content on success

        transport = httpx.MockTransport(_handler)
        original_client = httpx.AsyncClient
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("httpx.AsyncClient", lambda **kwargs: original_client(transport=transport, **kwargs))
            res = await notifier.send(report)
            assert res is True


class TestSlackNotifier:
    """Tests for SlackNotifier."""

    @pytest.mark.asyncio
    async def test_slack_skip_when_no_webhook(self) -> None:
        notifier = SlackNotifier(webhook_url=None)
        res = await notifier.send({"suite_name": "Test"})
        assert res is True

    @pytest.mark.asyncio
    async def test_slack_send_success(self) -> None:
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/services/mock")
        report = {
            "suite_name": "basic_suite",
            "summary": {
                "total": 5,
                "passed": 4,
                "failed": 1,
                "pass_rate": 0.8,
                "avg_score": 0.75,
            },
        }

        async def _handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200)

        transport = httpx.MockTransport(_handler)
        original_client = httpx.AsyncClient
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("httpx.AsyncClient", lambda **kwargs: original_client(transport=transport, **kwargs))
            res = await notifier.send(report)
            assert res is True
