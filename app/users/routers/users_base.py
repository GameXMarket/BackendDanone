from fastapi import Depends, APIRouter, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import *
from ..models import *
from ..services import users as UserService
from core.database import get_session
from core.security import verify_password
from core.depends import depends as deps # Переделать

router = APIRouter()
# TODO Прописать модели response и другое


@router.post(path="/me", responses={200: {"model": BaseUser}, 409: {"model": UserError}})
async def sign_up(
    request: Request, data: UserSignUp, db_session: AsyncSession = Depends(get_session)
):
    """
    Используется для регистрации новых пользователей, возвращает
    """
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

    user = await UserService.create_user(db_session, obj_in=data)
    # TODO send email verif here...

    return UserPreDB(**user.to_dict())


@router.get(path="/me")
async def get_user(user: User = Depends(deps.get_current_user_user)):

    return UserPreDB(**user.to_dict())


@router.patch(path="/me")
async def update_user(
    form_data: UserUpdate,
    user: User = Depends(deps.get_current_user_user),
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
    del update_data["auth"]

    if update_data.get("username") == user.username:
        del update_data["username"]

    if update_data.get("password") == form_data.auth.password:
        del update_data["password"]

    if update_data.get("is_verified") == form_data.is_verified:
        del update_data["is_verified"]

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT,
            detail="User not modified",
        )

    if update_data.get("usename"):
        if await UserService.get_by_username(db_session, username=form_data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The user with this username already exists in the system.",
            )

    new_user = await UserService.update_user(db_session, db_obj=user, obj_in=form_data)

    return UserPreDB(**new_user.to_dict())


@router.delete(path="/me")
async def remove_user(
    old_password: PasswordField,
    user: User = Depends(deps.get_current_user_user),
    db_session: AsyncSession = Depends(get_session),
):
    if not await UserService.authenticate(
        db_session, email=user.email, password=old_password.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    deleted_user = await UserService.delete_user(db_session, email=user.email)

    return UserPreDB(**deleted_user.to_dict())
