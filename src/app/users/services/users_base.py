from typing import Tuple, Any
import time

from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists, delete, and_

from app.tokens import schemas as schemas_t
from .. import models, schemas
from core import settings as conf
from core.mail_sender import *
from core.security import get_password_hash, verify_password, create_jwt_token


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
    db_obj = models.User(
        username=obj_in.username,
        email=obj_in.email,
        hashed_password=get_password_hash(obj_in.password),
        created_at=int(time.time()),
        updated_at=int(time.time()),
        **additional_fields,
    )

    db_session.add(db_obj)
    await db_session.commit()

    return db_obj


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
    await db_session.refresh(db_obj)

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


async def send_verify_mail(receiver_mail: str, logger):
    verify_token = create_jwt_token(
        type_=schemas_t.TokenType.email_verify,
        email=receiver_mail,
        secret=conf.EMAIL_SECRET_KEY,
        expires_delta=conf.EMAIL_ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    try:
        # need fix this
        await user_auth_sender.send_email(
            sender_name="Danone Market",
            receiver_email=receiver_mail,
            subject="User Verify",
            body=await render_auth_template(
                template_file="verify_user.html", data={"token": verify_token}
            ),
        )
    except BaseException as ex:
        logger.error(type(ex))
        logger.exception(ex)
        raise HTTPException(
            detail="email not sended", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )  
      

def is_active(user: models.User):
    return user.is_verified


def get_role_id(user: models.User):
    return user.role_id
