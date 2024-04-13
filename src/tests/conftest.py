import pytest
import asyncio

from httpx import ASGITransport, AsyncClient
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import NullPool

from core.database import Base, get_session
from core.settings.config import DATABASE_TEST_URL
from main import app

engine = create_async_engine(DATABASE_TEST_URL, echo=False, poolclass=NullPool)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base.metadata.bind = engine


async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


app.dependency_overrides[get_session] = override_get_async_session


@pytest.fixture(autouse=True, scope="session")
async def test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="session")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client
