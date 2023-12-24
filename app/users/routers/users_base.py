import logging

from fastapi import Depends, APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import *
from ..models import *
from ..services import users as UserService
from core import settings as conf
from core.database import get_session
from core.security import verify_password
from core.security import create_jwt_token
from core.mail_sender import *
from core.depends import depends as deps  # Переделать
from app.tokens.schemas import TokenType


logger = logging.getLogger("uvicorn")
router = APIRouter(responses={200: {"model": UserPreDB}})


@router.post(
    path="/me", responses={409: {"model": UserError}, 500: {"model": UserInfo}}
)
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

    verify_token = create_jwt_token(
        type_=TokenType.email_verify,
        email=data.email,
        secret=conf.EMAIL_SECRET_KEY,
        expires_delta=conf.EMAIL_ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    try:
        await user_auth_sender.send_email(
            sender_name="Danone Market",
            receiver_email=data.email,
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

    user = await UserService.create_user(db_session, obj_in=data)

    return UserPreDB(**user.to_dict())


@router.get(path="/me", responses=deps.build_response(deps.get_current_user_user))
async def get_user(user: User = Depends(deps.get_current_user_user)):
    return UserPreDB(**user.to_dict())


@router.patch(
    path="/me",
    responses={
        401: {"model": UserError},
        418: {"model": UserError},
        409: {"model": UserError},
    }.update(deps.build_response(deps.get_current_user_user)),
)
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


@router.delete(
    path="/me",
    responses={
        401: {"model": UserError},
    }.update(deps.build_response(deps.get_current_user_user)),
)
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


@router.post(
    path="/reset-password",
    responses={
        200: {"model": UserInfo},
        404: {"model": UserError},
        500: {"model": UserInfo}
    },
)
async def reset_user_password(
    email_f: EmailField,
    db_session: AsyncSession = Depends(get_session),
):
    user = await UserService.get_by_email(db_session, email=email_f.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    verify_token = create_jwt_token(
        type_=TokenType.email_verify,
        email=email_f.email,
        secret=conf.PASSWORD_RESET_SECRET_KEY,
        expires_delta=conf.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
    )

    try:
        await user_auth_sender.send_email(
            sender_name="Danone Market",
            receiver_email=email_f.email,
            subject="Password Reset",
            body=await render_auth_template(
                template_file="password-reset.html", data={"token": verify_token}
            ),
        )
    except BaseException as ex:
        logger.error(type(ex))
        logger.exception(ex)
        raise HTTPException(
            detail="email not sended", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return JSONResponse(content={"detail": "email_sended"})
