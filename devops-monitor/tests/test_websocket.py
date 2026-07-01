"""Tests for WebSocket metrics streaming."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from api.main import ws_metrics


def test_ws_metrics_streams_json(client: TestClient) -> None:
    """WebSocket /ws/metrics sends metrics JSON frames."""
    with client.websocket_connect("/ws/metrics") as websocket:
        data = websocket.receive_json()
        assert "cpu_percent" in data
        assert "memory_percent" in data
        assert "disk_percent" in data
        assert "memory_gb" in data


def test_ws_metrics_disconnect_is_handled(client: TestClient) -> None:
    """Closing the WebSocket connection does not crash the server."""
    with client.websocket_connect("/ws/metrics") as websocket:
        websocket.receive_json()
    # Reconnect to confirm the endpoint still works after disconnect.
    with client.websocket_connect("/ws/metrics") as websocket:
        data = websocket.receive_json()
        assert "cpu_percent" in data


@pytest.mark.asyncio
async def test_ws_metrics_handles_disconnect() -> None:
    """WebSocketDisconnect is caught without propagating."""
    mock_ws = AsyncMock()
    mock_ws.send_json = AsyncMock(side_effect=WebSocketDisconnect())

    await ws_metrics(mock_ws)

    mock_ws.accept.assert_awaited_once()

