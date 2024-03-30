from ..redis import get_redis_client
import random


async def verify_code(user_id: int, context: str, code: int) -> bool:
    right_code = await get_code_from_redis(user_id=user_id, context=context)
    return code == right_code


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
