import pytest
from httpx import AsyncClient


async def test_root(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 307
