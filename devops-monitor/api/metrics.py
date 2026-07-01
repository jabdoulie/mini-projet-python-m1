"""System metrics collection."""

import psutil


def get_system_metrics() -> dict[str, float]:
    """Return a snapshot of current CPU, memory, and disk usage."""
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory_percent": memory.percent,
        "memory_gb": round(memory.used / (1024**3), 2),
        "disk_percent": disk.percent,
    }
