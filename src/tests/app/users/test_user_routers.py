import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


# Просто пример выполнения теста
async def test_user(async_client: AsyncClient):
    response = await async_client.get("/users/me")
    assert response.status_code == 401
