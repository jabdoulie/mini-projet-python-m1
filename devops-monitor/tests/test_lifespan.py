"""Tests for application lifespan and startup/shutdown."""

from fastapi.testclient import TestClient

from api import main as api_main


def test_lifespan_starts_background_poll_task() -> None:
    """App startup launches the background poll loop task."""
    with TestClient(api_main.app):
        assert api_main.poll_task is not None
        assert not api_main.poll_task.done()


def test_lifespan_cancels_poll_task_on_shutdown() -> None:
    """App shutdown cancels the background poll loop cleanly."""
    with TestClient(api_main.app):
        task = api_main.poll_task
        assert task is not None

    assert task.cancelled() or task.done()
