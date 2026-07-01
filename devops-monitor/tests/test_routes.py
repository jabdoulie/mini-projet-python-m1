"""Route tests for the FastAPI application."""

from fastapi.testclient import TestClient

from api.auth import DEFAULT_API_KEY


def test_health(client: TestClient) -> None:
    """GET /health returns ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics(client: TestClient) -> None:
    """GET /metrics returns cpu_percent."""
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.json()
    assert "cpu_percent" in body
    assert "memory_percent" in body
    assert "disk_percent" in body
    assert "memory_gb" in body


def test_create_server_without_key(client: TestClient) -> None:
    """POST /servers without API key returns 403."""
    response = client.post(
        "/servers",
        json={"name": "test", "host": "localhost", "port": 8000},
    )
    assert response.status_code == 403


def test_create_server_with_invalid_key(client: TestClient) -> None:
    """POST /servers with wrong API key returns 403."""
    response = client.post(
        "/servers",
        json={"name": "test", "host": "localhost", "port": 8000},
        headers={"X-API-Key": "bad-key"},
    )
    assert response.status_code == 403


def test_create_server_with_invalid_port(client: TestClient) -> None:
    """POST /servers with invalid port returns 422."""
    response = client.post(
        "/servers",
        json={"name": "test", "host": "localhost", "port": 0},
        headers={"X-API-Key": DEFAULT_API_KEY},
    )
    assert response.status_code == 422


def test_create_server_with_key(client: TestClient) -> None:
    """POST /servers with valid key returns 201 and appears in GET /servers."""
    payload = {"name": "api", "host": "localhost", "port": 8000}
    response = client.post(
        "/servers",
        json=payload,
        headers={"X-API-Key": DEFAULT_API_KEY},
    )
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == payload["name"]
    assert created["host"] == payload["host"]
    assert created["port"] == payload["port"]
    assert created["status"] == "unknown"
    assert "id" in created

    list_response = client.get("/servers")
    assert list_response.status_code == 200
    ids = [server["id"] for server in list_response.json()]
    assert created["id"] in ids


def test_get_servers_empty(client: TestClient) -> None:
    """GET /servers returns an empty list when no servers exist."""
    response = client.get("/servers")
    assert response.status_code == 200
    assert response.json() == []


def test_get_server_by_id(client: TestClient) -> None:
    """GET /servers/{id} returns a registered server."""
    create = client.post(
        "/servers",
        json={"name": "one", "host": "localhost", "port": 8000},
        headers={"X-API-Key": DEFAULT_API_KEY},
    )
    server_id = create.json()["id"]
    response = client.get(f"/servers/{server_id}")
    assert response.status_code == 200
    assert response.json()["id"] == server_id


def test_get_server_not_found(client: TestClient) -> None:
    """GET /servers/{id} returns 404 for unknown id."""
    response = client.get("/servers/does-not-exist")
    assert response.status_code == 404


def test_filter_servers_by_status(client: TestClient) -> None:
    """GET /servers?status returns only matching servers."""
    create = client.post(
        "/servers",
        json={"name": "one", "host": "localhost", "port": 8000},
        headers={"X-API-Key": DEFAULT_API_KEY},
    )
    server_id = create.json()["id"]
    from api.main import store

    store[server_id].status = "UP"

    response = client.get("/servers", params={"status": "UP"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "UP"


def test_filter_servers_no_match(client: TestClient) -> None:
    """GET /servers?status returns empty when nothing matches."""
    client.post(
        "/servers",
        json={"name": "one", "host": "localhost", "port": 8000},
        headers={"X-API-Key": DEFAULT_API_KEY},
    )
    response = client.get("/servers", params={"status": "UP"})
    assert response.status_code == 200
    assert response.json() == []


def test_delete_server(client: TestClient) -> None:
    """DELETE /servers/{id} removes the server."""
    create = client.post(
        "/servers",
        json={"name": "tmp", "host": "localhost", "port": 8000},
        headers={"X-API-Key": DEFAULT_API_KEY},
    )
    server_id = create.json()["id"]

    delete = client.delete(f"/servers/{server_id}", headers={"X-API-Key": DEFAULT_API_KEY})
    assert delete.status_code == 204
    assert client.get(f"/servers/{server_id}").status_code == 404


def test_delete_server_without_key(client: TestClient) -> None:
    """DELETE /servers/{id} without API key returns 403."""
    create = client.post(
        "/servers",
        json={"name": "tmp", "host": "localhost", "port": 8000},
        headers={"X-API-Key": DEFAULT_API_KEY},
    )
    server_id = create.json()["id"]
    response = client.delete(f"/servers/{server_id}")
    assert response.status_code == 403


def test_delete_server_not_found(client: TestClient) -> None:
    """DELETE /servers/{id} returns 404 for unknown id."""
    response = client.delete(
        "/servers/missing",
        headers={"X-API-Key": DEFAULT_API_KEY},
    )
    assert response.status_code == 404


def test_check_server(client: TestClient) -> None:
    """POST /servers/{id}/check schedules a health check."""
    create = client.post(
        "/servers",
        json={"name": "check-me", "host": "localhost", "port": 8000},
        headers={"X-API-Key": DEFAULT_API_KEY},
    )
    server_id = create.json()["id"]
    response = client.post(f"/servers/{server_id}/check")
    assert response.status_code == 202
    assert response.json() == {"message": "Health check scheduled"}


def test_check_server_not_found(client: TestClient) -> None:
    """POST /servers/{id}/check returns 404 for unknown id."""
    response = client.post("/servers/missing/check")
    assert response.status_code == 404
