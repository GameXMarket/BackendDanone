from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import async_sessionmaker

from core.database import engine


async_session = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_session():
    async with async_session() as session:
        yield session


@asynccontextmanager
async def context_get_session():
    async with async_session() as session:
        yield session
