"""Tests for data models."""

import pytest
from pydantic import ValidationError

from api.models import Server, ServerIn, ServerOut


def test_server_default_status() -> None:
    """New servers default to unknown status."""
    server = Server(name="api", host="localhost", port=8000)
    assert server.status == "unknown"
    assert server.id


def test_server_base_url_strips_trailing_slash_not_needed() -> None:
    """base_url builds a standard HTTP URL."""
    server = Server(name="api", host="10.0.0.1", port=3000)
    assert server.base_url() == "http://10.0.0.1:3000"


def test_server_in_valid_port_range() -> None:
    """ServerIn accepts ports between 1 and 65535."""
    low = ServerIn(name="a", host="h", port=1)
    high = ServerIn(name="b", host="h", port=65535)
    assert low.port == 1
    assert high.port == 65535


def test_server_in_rejects_port_zero() -> None:
    """ServerIn rejects port 0."""
    with pytest.raises(ValidationError):
        ServerIn(name="a", host="h", port=0)


def test_server_in_rejects_port_too_high() -> None:
    """ServerIn rejects ports above 65535."""
    with pytest.raises(ValidationError):
        ServerIn(name="a", host="h", port=65536)


def test_server_out_fields() -> None:
    """ServerOut exposes all expected fields."""
    server = Server(name="web", host="localhost", port=8080, status="UP")
    out = ServerOut.from_server(server)
    assert out.name == "web"
    assert out.host == "localhost"
    assert out.port == 8080
    assert out.status == "UP"
    assert out.id == server.id
