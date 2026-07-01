"""Application data models."""

from dataclasses import dataclass, field
from uuid import uuid4

from pydantic import BaseModel, Field


@dataclass
class Server:
    """A monitored server."""

    name: str
    host: str
    port: int
    id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "unknown"

    def base_url(self) -> str:
        """Return the base HTTP URL for this server."""
        return f"http://{self.host}:{self.port}"


class ServerIn(BaseModel):
    """Incoming server registration payload."""

    name: str
    host: str
    port: int = Field(ge=1, le=65535)


class ServerOut(BaseModel):
    """Server representation returned by the API."""

    id: str
    name: str
    host: str
    port: int
    status: str

    @classmethod
    def from_server(cls, server: Server) -> "ServerOut":
        """Build a response model from a Server dataclass."""
        return cls(
            id=server.id,
            name=server.name,
            host=server.host,
            port=server.port,
            status=server.status,
        )
