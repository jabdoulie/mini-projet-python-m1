"""Background health-check polling."""

import asyncio

import httpx

from api.models import Server


async def poll_server(server_id: str, url: str, store: dict[str, Server]) -> None:
    """Check server health and update its status in the store."""
    server = store.get(server_id)
    if server is None:
        return

    health_url = f"{url.rstrip('/')}/health"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(health_url)
        server.status = "UP" if response.status_code == 200 else "DEGRADED"
    except (httpx.RequestError, httpx.TimeoutException):
        server.status = "DOWN"


async def run_poll_loop(store: dict[str, Server], interval: int = 10) -> None:
    """Periodically poll all registered servers."""
    while True:
        if store:
            tasks = [
                poll_server(server_id, server.base_url(), store)
                for server_id, server in list(store.items())
            ]
            await asyncio.gather(*tasks)
        await asyncio.sleep(interval)
