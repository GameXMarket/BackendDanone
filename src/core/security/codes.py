from typing import Literal, cast
import random

from ..redis import get_redis_client


async def generate_secret_number(length: int = 4) -> int:
    min_value = 10 ** (length - 1)
    max_value = (10**length) - 1
    return random.randint(min_value, max_value)


async def verify_code(
    user_id: int,
    code: int,
    context: Literal[
        "verify_email", "verify_password", "verify_old_email", "verify_new_email"
    ],
    need_delete: bool = True,
) -> tuple[bool, str]:
    right_code, data = await get_code_data_from_redis(user_id=user_id, context=context)
    if code == right_code:
        await delete_code_data_from_redis(user_id, context)
        return True, cast(bytes, data).decode() if data else None
    
    return False, None


async def generate_and_add_code_data_to_redis(
    user_id: int,
    context: Literal[
        "verify_email", "verify_password", "verify_old_email", "verify_new_email"
    ],
    data: str = "NaN",
    ttl: int = 900,
):
    async with get_redis_client() as redis:
        code = await generate_secret_number()
        await redis.setex(f"{user_id}:{context}", ttl, f"{code}:{data}")

    return code


async def delete_code_data_from_redis(
    user_id: int,
    context: Literal[
        "verify_email", "verify_password", "verify_old_email", "verify_new_email"
    ],
):
    async with get_redis_client() as redis:
        await redis.delete(f"{user_id}:{context}")


async def get_code_data_from_redis(
    user_id: int,
    context: Literal[
        "verify_email", "verify_password", "verify_old_email", "verify_new_email"
    ],
):
    async with get_redis_client() as redis:
        result: str = await redis.get(f"{user_id}:{context}")
        if result:
            code, data = result.split(b":")
            return int(code), data if data != b"NaN" else None

        return None, None
