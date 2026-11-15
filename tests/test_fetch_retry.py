"""Tests for transient CAP HTTP fetch retries."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import aiohttp
import pytest

from custom_components.ha_allerta_er.cap import async_fetch_cap, parse_cap

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.mark.asyncio
async def test_async_fetch_cap_succeeds_after_transient_client_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A retryable ClientError on the first attempt should not fail the fetch."""
    payload = (FIXTURES / "live_cap_20261111.xml").read_bytes()
    calls = {"count": 0}

    async def flaky_once(_session: aiohttp.ClientSession) -> object:
        calls["count"] += 1
        if calls["count"] == 1:
            raise aiohttp.ClientError(
                "[Errno 8] EOF occurred in violation of protocol (_ssl.c:2406)"
            )
        return parse_cap(payload)

    async def instant_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(
        "custom_components.ha_allerta_er.cap.asyncio.sleep", instant_sleep
    )

    feed = await async_fetch_cap(MagicMock(), fetch_once=flaky_once)
    assert feed.identifier == "107/2026"
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_async_fetch_cap_raises_after_all_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"count": 0}

    async def always_fail(_session: aiohttp.ClientSession) -> object:
        calls["count"] += 1
        raise aiohttp.ClientError("persistent failure")

    async def instant_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(
        "custom_components.ha_allerta_er.cap.asyncio.sleep", instant_sleep
    )

    with pytest.raises(aiohttp.ClientError, match="persistent failure"):
        await async_fetch_cap(MagicMock(), fetch_once=always_fail)
    assert calls["count"] == 3