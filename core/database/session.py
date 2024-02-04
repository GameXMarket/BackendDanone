from contextlib import asynccontextmanager
from typing import AsyncIterator, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from core.database import engine


async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        yield session


@asynccontextmanager
async def context_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
