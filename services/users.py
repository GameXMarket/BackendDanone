import time

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists, delete, and_

from dto.users import BaseUser as BaseUserDTO
from dto.users import UserInDBase as UserInDBaseDTO
from models.users import User as UserModelDB


async def create_user(data: BaseUserDTO, db_session: AsyncSession):
    # Проверки по электронной почте
    email_exists_stmt = select(exists().where(UserModelDB.email == data.email))
    email_exists = (await db_session.execute(email_exists_stmt)).scalar()
    if email_exists:
        return {
            "error": HTTPException(
                detail="Email is already registered",
                status_code=status.HTTP_409_CONFLICT,
            )
        }

    # Проверка по имени пользователя
    username_exists_stmt = select(exists().where(UserModelDB.username == data.username))
    username_exists = (await db_session.execute(username_exists_stmt)).scalar()
    if username_exists:
        return {
            "error": HTTPException(
                detail="Username is already registered",
                status_code=status.HTTP_409_CONFLICT,
            )
        }

    new_user = UserModelDB(
        username=data.username,
        email=data.email,
        hashed_password="fakehashed",
        created_at=int(time.time()),
    )

    db_session.add(new_user)
    await db_session.commit()

    return {"ok": UserInDBaseDTO(**new_user.to_dict())}


async def get_user(username: str, db_session: AsyncSession):
    user_stmt = select(UserModelDB).where(UserModelDB.username == username)
    user = (await db_session.execute(user_stmt)).scalar()

    if not user:
        return {
            "error": HTTPException(
                detail="User not found", status_code=status.HTTP_404_NOT_FOUND
            )
        }

    return {"ok": UserInDBaseDTO(**user.to_dict())}


async def update_user(username: str, data: BaseUserDTO, db_session: AsyncSession):
    # Получаем текущего пользователя
    current_user_stmt = select(UserModelDB).where(UserModelDB.username == username)
    current_user = (await db_session.execute(current_user_stmt)).scalar()
    if not current_user:
        return {
            "error": HTTPException(
                detail="User not found", status_code=status.HTTP_404_NOT_FOUND
            )
        }

    if data.email == current_user.email and data.username == current_user.username:
        return {"ok": UserInDBaseDTO(**current_user.to_dict())}

    # Проверка почты
    if data.email != current_user.email:
        email_exists_stmt = select(
            exists().where(
                and_(
                    UserModelDB.email == data.email,
                    UserModelDB.username != username,
                )
            )
        )
        email_exists = (await db_session.execute(email_exists_stmt)).scalar()
        if email_exists:
            return {
                "error": HTTPException(
                    detail="Email is already registered by another user",
                    status_code=status.HTTP_409_CONFLICT,
                )
            }

    # Проверка никнейма
    elif data.username != current_user.username:
        username_exists_stmt = select(
            exists().where(
                and_(
                    UserModelDB.username == data.username,
                    UserModelDB.username != username,
                )
            )
        )
        username_exists = (await db_session.execute(username_exists_stmt)).scalar()
        if username_exists:
            return {
                "error": HTTPException(
                    detail="Username is already registered by another user",
                    status_code=status.HTTP_409_CONFLICT,
                )
            }

    # Обновление пользователя
    update_stmt = (
        update(UserModelDB)
        .where(UserModelDB.username == username)
        .values(username=data.username, email=data.email)
    )
    await db_session.execute(update_stmt)
    await db_session.commit()

    return {"ok": UserInDBaseDTO(**current_user.to_dict())}


async def remove_user(username: str, db_session: AsyncSession):
    current_user_stmt = select(UserModelDB).where(UserModelDB.username == username)
    current_user = (await db_session.execute(current_user_stmt)).scalar()
    if not current_user:
        return {
            "error": HTTPException(
                detail="User not found", status_code=status.HTTP_404_NOT_FOUND
            )
        }

    delete_stmt = delete(UserModelDB).where(UserModelDB.username == username)
    await db_session.execute(delete_stmt)
    await db_session.commit()

    return {"ok": UserInDBaseDTO(**current_user.to_dict())}
