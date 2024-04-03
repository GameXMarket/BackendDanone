from typing import Any, AsyncGenerator
import pytest
from httpx import AsyncClient

from main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, Any, None]:
    async with AsyncClient(app=app, base_url="http://testserver") as async_client:
        yield async_client 


