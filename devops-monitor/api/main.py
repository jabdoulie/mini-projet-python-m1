"""FastAPI application entry point."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, WebSocket
from fastapi.websockets import WebSocketDisconnect

from api.auth import verify_api_key
from api.metrics import get_system_metrics
from api.models import Server, ServerIn, ServerOut
from api.poller import poll_server, run_poll_loop

store: dict[str, Server] = {}
poll_task: asyncio.Task[None] | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start and stop the background health-check loop."""
    global poll_task
    poll_task = asyncio.create_task(run_poll_loop(store))
    yield
    if poll_task is not None:
        poll_task.cancel()
        try:
            await poll_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="DevOps Monitor API", lifespan=lifespan)


def create_server(payload: ServerIn) -> Server:
    """Register a new server in the store."""
    server = Server(name=payload.name, host=payload.host, port=payload.port)
    store[server.id] = server
    return server


def list_servers(status: str | None = None) -> list[Server]:
    """Return all servers, optionally filtered by status."""
    servers = list(store.values())
    if status is not None:
        servers = [server for server in servers if server.status == status]
    return servers


def get_server(server_id: str) -> Server:
    """Return a server or raise 404."""
    server = store.get(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


def delete_server(server_id: str) -> None:
    """Remove a server from the store."""
    if server_id not in store:
        raise HTTPException(status_code=404, detail="Server not found")
    del store[server_id]


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> dict[str, float]:
    """Return current system metrics."""
    return get_system_metrics()


@app.websocket("/ws/metrics")
async def ws_metrics(websocket: WebSocket) -> None:
    """Stream metrics as JSON every second."""
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(get_system_metrics())
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass


@app.post("/servers", status_code=201, response_model=ServerOut)
def register_server(
    payload: ServerIn,
    _: str = Depends(verify_api_key),
) -> ServerOut:
    """Register a new monitored server."""
    server = create_server(payload)
    return ServerOut.from_server(server)


@app.get("/servers", response_model=list[ServerOut])
def get_servers(status: str | None = Query(default=None)) -> list[ServerOut]:
    """List monitored servers."""
    return [ServerOut.from_server(server) for server in list_servers(status)]


@app.get("/servers/{server_id}", response_model=ServerOut)
def get_server_by_id(server_id: str) -> ServerOut:
    """Return one server."""
    return ServerOut.from_server(get_server(server_id))


@app.delete("/servers/{server_id}", status_code=204)
def remove_server(
    server_id: str,
    _: str = Depends(verify_api_key),
) -> None:
    """Remove a monitored server."""
    delete_server(server_id)


@app.post("/servers/{server_id}/check", status_code=202)
async def check_server(
    server_id: str,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Trigger an immediate health check."""
    server = get_server(server_id)
    background_tasks.add_task(poll_server, server_id, server.base_url(), store)
    return {"message": "Health check scheduled"}
