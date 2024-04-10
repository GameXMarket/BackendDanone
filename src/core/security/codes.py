from ..redis import get_redis_client
from typing import Literal
import random


async def verify_code(
    user_id: int, context: Literal["verify_email", "verify_password"], code: int, need_delete: bool = True
) -> bool:
    right_code = await get_code_from_redis(user_id=user_id, context=context)
    if code == right_code:
        if need_delete:
            await delete_code_from_redis(user_id, context)
        return True
    return False


async def delete_mail_from_redis(user_id: int, context: str = "mail_update"):
    async with get_redis_client() as redis:
        await redis.delete(f"{context}:{user_id}")


async def get_mail_from_redis(user_id: int, context: str = "mail_update", need_delete: bool = True):
    async with get_redis_client() as redis:
        mail = await redis.get(f"{context}:{user_id}")
        if mail:
            if need_delete:
                await delete_code_from_redis(user_id, context)
            
            return str(mail)
        
        return None


async def add_mail_to_redis(
    user_id: int, mail: str, context: str = "mail_update", ttl: int = 900
):
    async with get_redis_client() as redis:
        await redis.setex(f"{context}:{user_id}", ttl, mail)


async def generate_and_add_code_to_redis(
    user_id: int, context: Literal["verify_email", "verify_password"], ttl: int = 900
):
    async with get_redis_client() as redis:
        code = await generate_secret_number()
        await redis.setex(f"{user_id}:{context}", ttl, code)
        return code


async def delete_code_from_redis(
    user_id: int, context: Literal["verify_email", "verify_password"]
):
    async with get_redis_client() as redis:
        await redis.delete(f"{user_id}:{context}")


async def get_code_from_redis(
    user_id: int, context: Literal["verify_email", "verify_password"]
):
    async with get_redis_client() as redis:
        code = await redis.get(f"{user_id}:{context}")
        if code:
            return int(code)
        
        return None


async def generate_secret_number(length: int = 4) -> int:
    min_value = 10 ** (length - 1)
    max_value = (10**length) - 1
    return random.randint(min_value, max_value)
