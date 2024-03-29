import random
from typing import Any
import logging
import aiofiles.os
from ..redis import get_redis_client

logger = logging.getLogger("uvicorn")

"""
Куда работу с редисом перенести обсудить!
"""


async def add_code_to_redis(user_id: int, code: int, context: str, ttl: int = 900):
    async with get_redis_client() as redis:
        await redis.setex(f"{user_id}:{context}", ttl, code)


async def delete_code_from_redis(user_id: int, context: str):
    async with get_redis_client() as redis:
        await redis.delete(f"{user_id}:{context}")


async def get_code_from_redis(user_id: int, context: str):
    async with get_redis_client() as redis:
        code = await redis.get(f"{user_id}:{context}")
        if code:
            code = int(code.decode())
        else:
            return None
        return code


async def generate_secret_number(length: int = 4) -> int:
    min_value = 10 ** (length - 1)
    max_value = (10 ** length) - 1
    return random.randint(min_value, max_value)


async def check_dir_exists(path: str | Any, auto_create: bool = True):
    """
    Проверяет существование директории, по умолчанию, если не нашлась, создаёт её
    """

    path_exist = await aiofiles.os.path.exists(path)

    if path_exist:
        return True
    elif auto_create:
        await aiofiles.os.makedirs(path)
        logger.info(f"Directory {path} created.")
        return True

    return False
