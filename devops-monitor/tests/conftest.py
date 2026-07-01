"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient

from api import main as api_main


@pytest.fixture(autouse=True)
def clear_store() -> None:
    """Reset the in-memory server store between tests."""
    api_main.store.clear()


@pytest.fixture
def client() -> TestClient:
    """Return a FastAPI test client."""
    return TestClient(api_main.app)
