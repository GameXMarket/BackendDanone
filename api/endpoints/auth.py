from datetime import timedelta

from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import schemas, models
import core.configuration as conf
from core.security import tokens as TokenSecurity
from core.database import get_session
from services import users as UserService
from api import deps

from core import configuration as conf


router = APIRouter()
# TODO Прописать модели response


@router.post(
    "/get-tokens",
)
async def token_set(
    form_data: schemas.UserLogin,
    db_session: Session = Depends(get_session),
):
    """Возвращает два токена (refresh и access), запрашивает почту и пароль"""
    # ! TODO Когда ставим токен, если есть старый и он действителен мы его инвалидируем.

    user: models.User = await UserService.authenticate(
        db_session=db_session,
        email=form_data.email,
        password=form_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=400, detail="Incorrect email/username or password"
        )
    elif not UserService.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")

    access = TokenSecurity.create_jwt_token(
        type_=schemas.TokenType.access,
        email=form_data.email,
        secret=conf.ACCESS_SECRET_KEY,
        expires_delta=timedelta(minutes=conf.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh = TokenSecurity.create_jwt_token(
        type_=schemas.TokenType.refresh,
        email=form_data.email,
        secret=conf.ACCESS_SECRET_KEY,
        expires_delta=timedelta(minutes=conf.REFRESH_TOKEN_EXPIRE_MINUTES),
    )

    response = JSONResponse(content={"detail": "tokens_added"})
    # TODO Защита от xss, csrf (проверить аргументы по умолчанию)
    response.set_cookie(key="session", value=access)
    response.set_cookie(key="refresh", value=refresh)

    return response


@router.post("/update-tokens")
def token_update(token_data: schemas.JwtPayload = Depends(deps.get_refresh)):
    """
    Данный метод принимает refresh токен, возвращает новую пару ключей
    """

    access = TokenSecurity.create_jwt_token(
        type_=schemas.TokenType.access,
        email=token_data.sub,
        secret=conf.ACCESS_SECRET_KEY,
        expires_delta=timedelta(minutes=conf.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh = TokenSecurity.create_jwt_token(
        type_=schemas.TokenType.refresh,
        email=token_data.sub,
        secret=conf.ACCESS_SECRET_KEY,
        expires_delta=timedelta(minutes=conf.REFRESH_TOKEN_EXPIRE_MINUTES),
    )

    response = JSONResponse(content={"detail": "tokens_updated"})
    # TODO Защита от xss, csrf (проверить аргументы по умолчанию)
    response.set_cookie(key="session", value=access)
    response.set_cookie(key="refresh", value=refresh)

    return response


@router.post(
    "/test-test-tokens",
)
async def set_tokens(access: str, refresh: str):

    response = JSONResponse(content={"detail": None})
    # response.set_cookie(key="session", value=access)
    # response.set_cookie(key="refresh", value=refresh)

    return response


@router.post(
    "/delete-tokens",
)
async def token_delete():
    """
    Данный метод используются когда человек выходит из аккаунта\n
    Я не до конца уверен в их актуальности, также возможно стоит
     поместить данные методы в один путь /delete-tokens, который
     запрашивает сразу оба токена.
    """
    # ! TODO Автоматически инвалидировать токен, путём созданя чёрного списка.

    response = JSONResponse(content={"detail": "deleted"})
    response.delete_cookie("token")

    return response


@router.post(
    "/verify-user",
)
async def verify_user_email(token: str, db_session: Session = Depends(get_session)):
    """
    Метод используется для верификации пользователей, через почту\n
    Виден в документации только во время отладки.
    """

    # TODO нормальная валидация запросов с почты

    user = await UserService.get_by_username(db_session, username=token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if UserService.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already active"
        )

    user = await UserService.update_(
        db_session, db_obj=user, obj_in={"is_verified": True}
    )

    return schemas.UserPreDB(**user.to_dict())


@router.post(
    "/reset-password",
)
async def verify_password_reset(token: str, db_session: Session = Depends(get_session)):
    """
    Метод используется для верификации пользователей, через почту\n
    Виден в документации только во время отладки.
    """

    # TODO нормальная валидация запросов с почты + логика сброса по токену

    return "method in progress.."
