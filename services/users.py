import time

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists, delete, and_

import models, schemas
from core.security import get_password_hash, verify_password


async def get_by_email(db_session: AsyncSession, *, email: str):
    user_stmt = select(models.User).where(models.User.email == email)
    user: models.User | None = (await db_session.execute(user_stmt)).scalar()
    return user


async def get_by_username(db_session: AsyncSession, *, username: str):
    user_stmt = select(models.User).where(models.User.username == username)
    user: models.User | None = (await db_session.execute(user_stmt)).scalar()
    return user


async def create_(db_session: AsyncSession, *, obj_in: schemas.UserSignUp):
    db_obj = models.User(
        username=obj_in.username,
        email=obj_in.email,
        hashed_password=get_password_hash(obj_in.password),
        created_at=int(time.time()),
    )

    db_session.add(db_obj)
    await db_session.commit()

    return db_obj


async def update_(
    db_session: AsyncSession, *, db_obj: models.User, obj_in: schemas.UserInDB
):
    """UserInDB - Максимальное кол-во полей, доступное тут, настоящий тип может быть и другим"""
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


async def delete_(db_session: AsyncSession, *, email: str):
    current_user_stmt = select(models.User).where(models.User.email == email)
    current_user = (await db_session.execute(current_user_stmt)).scalar()
    if not current_user:
        return None

    await db_session.delete(current_user)
    await db_session.commit()

    return current_user


async def authenticate(
    db_session: AsyncSession, *, email: str, password: str, username: str
):
    if username:
        user = await get_by_username(db_session, username=username)
    else:
        user = await get_by_email(db_session, email=email)

    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None

    return user


def is_active(user: models.User):
    return user.is_verified


async def get_role_id(user: models.User):
    return user.role_id
