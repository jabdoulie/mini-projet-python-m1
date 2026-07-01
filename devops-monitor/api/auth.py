"""API key authentication."""

import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
DEFAULT_API_KEY = "dev-api-key"
EXPECTED_API_KEY = os.getenv("API_KEY", DEFAULT_API_KEY)


async def verify_api_key(api_key: str | None = Security(API_KEY_HEADER)) -> str:
    """Validate the X-API-Key header."""
    if not api_key or api_key != EXPECTED_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return api_key
