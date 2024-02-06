import logging
from typing import AsyncIterator, AsyncGenerator
from contextlib import asynccontextmanager

import redis.asyncio as aredis
from redis.asyncio.client import Pipeline

from core.settings import config


logger = logging.getLogger("uvicorn")
pool = aredis.ConnectionPool.from_url(config.REDIS_URL)


@asynccontextmanager
async def get_redis_client() -> AsyncGenerator[aredis.Redis, None]:
    _client = aredis.Redis(connection_pool=pool)
    _exception = None
    try:
        yield _client
    except BaseException as e:
        _exception = e
    finally:
        await _client.aclose()
    
    if _exception:
        raise _exception


@asynccontextmanager
async def get_redis_pipeline(need_client: bool = False) -> AsyncGenerator[tuple[Pipeline, aredis.Redis] | Pipeline, None]:
    async with get_redis_client() as client:
        async with client.pipeline(transaction=True) as pipe:
            if need_client:
                yield pipe, client
            else:
                yield pipe

            await pipe.execute()
