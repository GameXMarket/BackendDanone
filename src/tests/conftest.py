import pytest
from httpx import AsyncClient

from main import app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def async_client():
    async with AsyncClient(app=app, base_url="http://testserver") as async_client:
        yield async_client 
