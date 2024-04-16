from contextlib import asynccontextmanager
from typing import AsyncIterator, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from core.database import engine


async_session = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_session():
    async with async_session() as session:
        yield session


@asynccontextmanager
async def context_get_session():
    async with async_session() as session:
        yield session
