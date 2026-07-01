"""Tests for background health-check polling."""

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from api.models import Server
from api.poller import poll_server, run_poll_loop


@pytest.mark.asyncio
async def test_poll_server_up() -> None:
    """poll_server sets UP on HTTP 200."""
    server = Server(name="api", host="localhost", port=8000)
    local_store = {server.id: server}
    request = httpx.Request("GET", "http://localhost:8000/health")
    mock_response = httpx.Response(200, request=request)

    with patch("api.poller.httpx.AsyncClient") as mock_client:
        instance = mock_client.return_value.__aenter__.return_value
        instance.get = AsyncMock(return_value=mock_response)
        await poll_server(server.id, server.base_url(), local_store)

    assert server.status == "UP"


@pytest.mark.asyncio
async def test_poll_server_degraded() -> None:
    """poll_server sets DEGRADED on non-200 responses."""
    server = Server(name="api", host="localhost", port=8000)
    local_store = {server.id: server}
    request = httpx.Request("GET", "http://localhost:8000/health")
    mock_response = httpx.Response(503, request=request)

    with patch("api.poller.httpx.AsyncClient") as mock_client:
        instance = mock_client.return_value.__aenter__.return_value
        instance.get = AsyncMock(return_value=mock_response)
        await poll_server(server.id, server.base_url(), local_store)

    assert server.status == "DEGRADED"


@pytest.mark.asyncio
async def test_poll_server_down_on_connection_error() -> None:
    """poll_server sets DOWN on connection errors."""
    server = Server(name="api", host="localhost", port=8000)
    local_store = {server.id: server}

    with patch("api.poller.httpx.AsyncClient") as mock_client:
        instance = mock_client.return_value.__aenter__.return_value
        instance.get = AsyncMock(side_effect=httpx.ConnectError("failed"))
        await poll_server(server.id, server.base_url(), local_store)

    assert server.status == "DOWN"


@pytest.mark.asyncio
async def test_poll_server_down_on_timeout() -> None:
    """poll_server sets DOWN on timeout."""
    server = Server(name="api", host="localhost", port=8000)
    local_store = {server.id: server}

    with patch("api.poller.httpx.AsyncClient") as mock_client:
        instance = mock_client.return_value.__aenter__.return_value
        instance.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        await poll_server(server.id, server.base_url(), local_store)

    assert server.status == "DOWN"


@pytest.mark.asyncio
async def test_poll_server_missing_id_is_noop() -> None:
    """poll_server ignores unknown server ids."""
    server = Server(name="api", host="localhost", port=8000)
    local_store: dict[str, Server] = {}

    await poll_server(server.id, server.base_url(), local_store)
    assert server.status == "unknown"


@pytest.mark.asyncio
async def test_poll_server_trailing_slash_url() -> None:
    """poll_server normalises URLs with a trailing slash."""
    server = Server(name="api", host="localhost", port=8000)
    local_store = {server.id: server}
    request = httpx.Request("GET", "http://localhost:8000/health")
    mock_response = httpx.Response(200, request=request)

    with patch("api.poller.httpx.AsyncClient") as mock_client:
        instance = mock_client.return_value.__aenter__.return_value
        instance.get = AsyncMock(return_value=mock_response)
        await poll_server(server.id, "http://localhost:8000/", local_store)

    instance.get.assert_awaited_once_with("http://localhost:8000/health")
    assert server.status == "UP"


@pytest.mark.asyncio
async def test_run_poll_loop_polls_servers() -> None:
    """run_poll_loop calls poll_server for each registered server."""
    server = Server(name="api", host="localhost", port=8000)
    local_store = {server.id: server}

    with patch("api.poller.poll_server", new_callable=AsyncMock) as mock_poll:
        with patch("api.poller.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = [None, asyncio.CancelledError()]
            with pytest.raises(asyncio.CancelledError):
                await run_poll_loop(local_store, interval=1)

    assert mock_poll.await_count >= 1


@pytest.mark.asyncio
async def test_run_poll_loop_empty_store() -> None:
    """run_poll_loop keeps running when the store is empty."""
    local_store: dict[str, Server] = {}

    with patch("api.poller.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_sleep.side_effect = [None, asyncio.CancelledError()]
        with pytest.raises(asyncio.CancelledError):
            await run_poll_loop(local_store, interval=1)

    assert mock_sleep.await_count >= 1
