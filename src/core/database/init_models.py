import logging

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine

from core.database import Base
from core.database.listener import PostgreListener
import core.settings.config as conf


logger = logging.getLogger("uvicorn")
engine = create_async_engine(
    url=conf.DATABASE_URL,
    pool_size=10,
    max_overflow = 0,
    pool_pre_ping = True,
    connect_args = {
        "timeout": 15,
        "command_timeout": 5,
        "server_settings": {
            "jit": "off",
            "application_name": "backend_danone",
        },
    },
    echo=conf.ECHO_SQL
)
event_listener = PostgreListener()


async def init_models(*, drop_all=False):
    if not conf.DEBUG and drop_all:
        raise ValueError("This action is possible only when the debug is enabled!")

    async with engine.begin() as conn:
        if drop_all:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Init models finished.")