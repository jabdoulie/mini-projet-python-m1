"""Unit tests for system metrics."""

from api.metrics import get_system_metrics


def test_get_system_metrics_keys() -> None:
    """Metrics dict must contain the expected keys."""
    metrics = get_system_metrics()
    assert "cpu_percent" in metrics
    assert "memory_percent" in metrics
    assert "disk_percent" in metrics
    assert "memory_gb" in metrics


def test_get_system_metrics_ranges() -> None:
    """Percent values must be between 0 and 100."""
    metrics = get_system_metrics()
    for key in ("cpu_percent", "memory_percent", "disk_percent"):
        assert 0 <= metrics[key] <= 100


def test_get_system_metrics_memory_gb_non_negative() -> None:
    """Memory usage in GB must be non-negative."""
    metrics = get_system_metrics()
    assert metrics["memory_gb"] >= 0
