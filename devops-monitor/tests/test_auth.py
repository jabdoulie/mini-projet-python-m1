"""Tests for API key authentication."""

import pytest
from fastapi import HTTPException

from api.auth import DEFAULT_API_KEY, verify_api_key


@pytest.mark.asyncio
async def test_verify_api_key_valid() -> None:
    """A correct API key is accepted."""
    result = await verify_api_key(DEFAULT_API_KEY)
    assert result == DEFAULT_API_KEY


@pytest.mark.asyncio
async def test_verify_api_key_missing() -> None:
    """Missing API key raises 403."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(None)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Invalid or missing API key"


@pytest.mark.asyncio
async def test_verify_api_key_invalid() -> None:
    """Wrong API key raises 403."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key("wrong-key")
    assert exc_info.value.status_code == 403
