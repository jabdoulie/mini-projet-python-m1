"""Unit tests for main module business logic."""

import pytest
from fastapi import HTTPException

from api.main import create_server, delete_server, get_server, list_servers, store
from api.models import ServerIn


def test_create_server_registers_in_store() -> None:
    """create_server adds the server to the in-memory store."""
    payload = ServerIn(name="web", host="localhost", port=8080)
    server = create_server(payload)
    assert server.name == "web"
    assert server.host == "localhost"
    assert server.port == 8080
    assert server.status == "unknown"
    assert store[server.id] is server


def test_list_servers_returns_all() -> None:
    """list_servers returns every registered server."""
    create_server(ServerIn(name="a", host="h1", port=8001))
    create_server(ServerIn(name="b", host="h2", port=8002))
    assert len(list_servers()) == 2


def test_list_servers_filters_by_status() -> None:
    """list_servers filters by status when requested."""
    server = create_server(ServerIn(name="a", host="h", port=8000))
    server.status = "UP"
    create_server(ServerIn(name="b", host="h", port=8001))
    filtered = list_servers(status="UP")
    assert len(filtered) == 1
    assert filtered[0].name == "a"


def test_get_server_found() -> None:
    """get_server returns an existing server."""
    created = create_server(ServerIn(name="found", host="h", port=8000))
    result = get_server(created.id)
    assert result.id == created.id


def test_get_server_not_found_raises() -> None:
    """get_server raises 404 for unknown ids."""
    with pytest.raises(HTTPException) as exc_info:
        get_server("missing-id")
    assert exc_info.value.status_code == 404


def test_delete_server_removes_from_store() -> None:
    """delete_server removes the entry from the store."""
    created = create_server(ServerIn(name="tmp", host="h", port=8000))
    delete_server(created.id)
    assert created.id not in store


def test_delete_server_not_found_raises() -> None:
    """delete_server raises 404 for unknown ids."""
    with pytest.raises(HTTPException) as exc_info:
        delete_server("missing-id")
    assert exc_info.value.status_code == 404
