from fastapi import Depends, APIRouter, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import models
from schemas import *
from services import users as UserService
from core.database import get_session
from core.security import verify_password
from api import deps


router = APIRouter()
# TODO Прописать модели response и другое


@router.post(path="/", responses={200: {"model": BaseUser}, 409: {"model": UserError}})
async def sign_up(
    request: Request, data: UserSignUp, db_session: AsyncSession = Depends(get_session)
):
    """
    Используется для регистрации новых пользователей, возвращает
    """
    # TODO Вероятно не лучшее решение с проверкой
    if await UserService.get_by_email(db_session, email=data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user with this email already exists in the system.",
        )
    if await UserService.get_by_username(db_session, username=data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user with this username already exists in the system.",
        )

    user = await UserService.create_(db_session, obj_in=data)
    # TODO send email verif here...

    return UserPreDB(**user.to_dict())


@router.get(path="/me")
async def get_user(user: models.User = Depends(deps.get_current_user_user)):

    return UserPreDB(**user.to_dict())


@router.put(path="/me")
async def update_user(
    form_data: UserUpdate,
    user: models.User = Depends(deps.get_current_user_user),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Данный метод используется для изменения пароля и username пользователя\n
    Для подтверждения сначала проверятся токен, далее пароль и остальные поля
    """
    if not verify_password(form_data.auth.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect old password",
        )

    update_data = form_data.model_dump(exclude_unset=True)
    if update_data.get("username") == user.username:
        del update_data["username"]

    if update_data.get("password") == form_data.auth.password:
        del update_data["password"]

    print(update_data)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_304_NOT_MODIFIED,
            detail="User and password not modified",
        )

    # TODO Вероятно не лучшее решение с проверкой
    if await UserService.get_by_username(db_session, username=form_data.data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user with this username already exists in the system.",
        )

    new_user = await UserService.update_(db_session, db_obj=user, obj_in=form_data.data)

    return UserPreDB(**new_user.to_dict())


@router.delete(path="/me")
async def remove_user(
    user: models.User = Depends(deps.get_current_user_user),
    db_session: AsyncSession = Depends(get_session),
):
    deleted_user = await UserService.delete_(db_session, email=user.email)

    return UserPreDB(**deleted_user.to_dict())
