import logging

import fastapi
from fastapi import (
    Depends,
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    status,
)
from fastapi.responses import JSONResponse
from sqlalchemy.orm import noload
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import *
from ..models import *
from ..services import users_base as UserService
from core import settings as conf
from core.database import get_session
from core.security import codes
from core.security import verify_password
from core.security import create_jwt_token
from core.mail_sender import *
from core.depends import depends as deps
from app.tokens import schemas as schemas_t
from app.attachment.services.user_attachment import user_attachment_manager
import core.utils as utils

logger = logging.getLogger("uvicorn")
router = APIRouter(responses={200: {"model": UserPreDB}})
default_session = deps.UserSession()


@router.post(
    path="/me", responses={409: {"model": UserError}, 500: {"model": UserInfo}}
)
async def sign_up(data: UserSignUp, db_session: AsyncSession = Depends(get_session)):
    """
    Используется для регистрации новых пользователей
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
    await UserService.send_verify_mail(receiver_mail=data.email, logger=logger)
    user = await UserService.create_user(db_session, obj_in=data)

    return UserPreDB(**user.to_dict())


@router.get(
    path="/me",
    responses={**deps.build_response(deps.UserSession.get_current_active_user)},
)
async def get_user(
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user: User = await user_context.get_current_active_user(db_session, token_data)
    user_files = await user_attachment_manager.get_only_files(db_session, user.id)
    user_dict = user.to_dict()
    user_dict["files"] = user_files

    return user_dict


@router.post(
    path="/send-verify-mail",
)
async def send_verify_mail_again(
    email: EmailField,
    db_session: AsyncSession = Depends(get_session),
):
    await UserService.send_verify_mail(receiver_mail=email.email, logger=logger)
    return {"status": "ok"}

    
@router.patch(path="/me/update/username")
async def update_user_username(
    data_form: UserUpdateUsername,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user: User = await user_context.get_current_active_user(db_session, token_data)

    if await UserService.get_by_username(db_session, username=data_form.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
        )

    updated_user = await UserService.update_user(
        db_session, user, {"username": data_form.username}
    )
    return updated_user


@router.post(path="/me/password")
async def send_code_for_change_password(
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user: User = await user_context.get_current_active_user(db_session, token_data)

    code = await codes.generate_and_add_code_data_to_redis(
        user_id=user.id, context="verify_password"
    )
    try:
        await user_auth_sender.send_email(
            sender_name="Danone Market",
            receiver_email=user.email,
            subject="Password change",
            body=await render_auth_template(
                template_file="code_send.html", data={"code": code}
            ),
        )
    except BaseException as ex:
        logger.error(type(ex))
        logger.exception(ex)
        await codes.delete_code_data_from_redis(user_id=user.id, context="verify_password")
        raise HTTPException(
            detail="email not sended", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return JSONResponse(content={"detail": "email_sended"})


@router.post(
    path="/me/oldmail",
)
async def send_code_to_old_user_email(
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):

    """
    Отправляет на почту пользователя код, необходимый для смены почты. <br>
    Код в дальнейшем используйется в /me/newmail
    """

    token_data, user_context = current_session
    user: User = await user_context.get_current_active_user(db_session, token_data)

    code = await codes.generate_and_add_code_data_to_redis(
        user_id=user.id, context="verify_old_email"
    )
    try:
        await user_auth_sender.send_email(
            sender_name="Danone Market",
            receiver_email=user.email,
            subject="Email change",
            body=await render_auth_template(
                template_file="code_send.html", data={"code": code}
            ),
        )
    except BaseException as ex:
        logger.error(type(ex))
        logger.exception(ex)
        await codes.delete_code_data_from_redis(user_id=user.id, context="verify_old_email")
        raise HTTPException(
            detail="email not sended", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return JSONResponse(content={"detail": "email_sended"})


@router.post(path="/me/newmail")
async def send_code_to_new_user_mail(
    form_data: UserUpdateEmail,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):

    """
    Отправляет на новый емейл код подтверждения, сохраняя информацию о новой почте\n
     * code_old - код со старой почты\n
     * email - новая почта
    """

    token_data, user_context = current_session
    user: User = await user_context.get_current_active_user(db_session, token_data)

    is_valid, _ = await codes.verify_code(user_id=user.id, context="verify_old_email", code=form_data.code_old)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wrong code")

    code = await codes.generate_and_add_code_data_to_redis(user_id=user.id, context="verify_new_email", data=form_data.email)
    try:
        await user_auth_sender.send_email(
            sender_name="Danone Market",
            receiver_email=form_data.email,
            subject="Email change",
            body=await render_auth_template(
                template_file="code_send.html", data={"code": code}
            ),
        )
    except BaseException as ex:
        logger.error(type(ex))
        logger.exception(ex)
        await codes.delete_code_data_from_redis(user_id=user.id, context="verify_new_email")
        raise HTTPException(
            detail="email not sended", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return JSONResponse(content={"detail": "email_sended"})


@router.delete(
    path="/me",
)
async def remove_user(
    old_password: PasswordField,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Метод для дебага
    """
    token_data, user_context = current_session
    user: User = await user_context.get_current_active_user(db_session, token_data)

    if not await UserService.authenticate(
        db_session, email=user.email, password=old_password.password
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    deleted_user = await UserService.delete_user(db_session, email=user.email)

    return UserPreDB(**deleted_user.to_dict())


@router.post(
    path="/reset-password",
    responses={
        200: {"model": UserInfo},
        404: {"model": UserError},
        500: {"model": UserInfo},
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
        type_=schemas_t.TokenType.email_verify,
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
