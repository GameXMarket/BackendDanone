from typing import Tuple, Any
import time

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update, exists, delete, and_

from .. import models, schemas
from core.security import get_password_hash, verify_password


async def get_by_id(db_session: AsyncSession, *, id: int):
    user_stmt = select(models.User).where(models.User.id == id)
    user: models.User | None = (await db_session.execute(user_stmt)).scalar()
    return user


async def get_by_email(
    db_session: AsyncSession, *, email: str, options: Tuple[Any] = None
):
    user_stmt = select(models.User).where(models.User.email == email)
    if options:
        user_stmt = user_stmt.options(options[0](options[1]))
    user: models.User | None = (await db_session.execute(user_stmt)).scalar()
    return user


async def get_by_username(db_session: AsyncSession, *, username: str):
    user_stmt = select(models.User).where(models.User.username == username)
    user: models.User | None = (await db_session.execute(user_stmt)).scalar()
    return user


async def create_user(
    db_session: AsyncSession,
    *,
    obj_in: schemas.UserSignUp,
    additional_fields: dict = {},
):
    stmt = (
        insert(models.User)
        .values(
            username=obj_in.username,
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            **additional_fields,

        )
        .returning(
            models.User
        )
    )
    q = await db_session.execute(stmt)
    await db_session.commit()
    return q.scalar()


async def update_user(
    db_session: AsyncSession, db_obj: models.User, obj_in: schemas.UserInDB | dict
):
    """UserInDB - Максимальное кол-во полей, доступное тут, настоящий тип может быть и другим"""
    db_obj.updated_at = int(time.time())
    obj_data = jsonable_encoder(db_obj)
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)

    if update_data.get("password"):
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password

    for field in obj_data:
        if field in update_data:
            setattr(db_obj, field, update_data[field])

    db_session.add(db_obj)
    await db_session.commit()

    return db_obj


async def update_last_online(db_session: AsyncSession, *, db_obj: models.User):
    new_user = await update_user(
        db_session, db_obj=db_obj, obj_in={"last_online": int(time.time())}
    )

    return new_user


async def delete_user(db_session: AsyncSession, *, email: str):
    current_user = await get_by_email(db_session, email=email)

    if not current_user:
        return None

    await db_session.delete(current_user)
    await db_session.commit()

    return current_user


async def authenticate(db_session: AsyncSession, *, email: str, password: str):
    if not email:
        return None

    user = await get_by_email(db_session, email=email)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def is_active(user: models.User):
    return user.is_verified


def get_role_id(user: models.User):
    return user.role_id
