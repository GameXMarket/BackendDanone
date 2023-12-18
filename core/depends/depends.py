from fastapi.security import APIKeyCookie
from fastapi import Request, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.tokens import models as models_t, schemas as schemas_t
from app.tokens import services as TokensService
from app.users import models as models_u, schemas as schemas_u
from app.users import services as UserService
from core.security import tokens as TokenSecurity
from core.database import get_session

from core import settings as conf

# TODO BASE

# ! В случае надобности, просто меняем схему получения токенов
access_cookie_scheme = APIKeyCookie(
    name="session",
    scheme_name="Cookie session token",
    description="Поле и кнопка ниже ни на что не влияют, они сделаны для отображения запросов, требующих авторизации",
)

refresh__cookie_scheme = APIKeyCookie(
    name="refresh",
    scheme_name="Cookie refresh token",
    description="Поле и кнопка ниже ни на что не влияют, они сделаны для отображения запросов, требующих авторизации",
)


async def get_refresh(
    refresh_t=Depends(refresh__cookie_scheme),
    db_session: AsyncSession = Depends(get_session),
) -> schemas_t.JwtPayload:
    token_data: schemas_t.JwtPayload = await TokenSecurity.verify_jwt_token(
        token=refresh_t, secret=conf.ACCESS_SECRET_KEY, db_session=db_session
    )

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    banned_token = await TokensService.ban_token(
        db_session=db_session, token=refresh_t, payload=token_data
    )

    return token_data


async def get_access(
    access_t=Depends(access_cookie_scheme),
    db_session: AsyncSession = Depends(get_session),
) -> schemas_t.JwtPayload:
    token_data = await TokenSecurity.verify_jwt_token(
        token=access_t, secret=conf.ACCESS_SECRET_KEY, db_session=db_session
    )

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    return token_data

# TODO Others

async def auto_token_ban(
    refresh_t=Depends(refresh__cookie_scheme),
    access_t=Depends(access_cookie_scheme),
    db_session: AsyncSession = Depends(get_session),
) -> None:
    refresh_data = await TokenSecurity.verify_jwt_token(
        refresh_t, secret=conf.REFRESH_SECRET_KEY, db_session=db_session
    )
    if refresh_data:
        await TokensService.ban_token(
            db_session=db_session,
            token=refresh_t,
            payload=schemas_t.JwtPayload(**refresh_data),
        )
    access_data = await TokenSecurity.verify_jwt_token(
        access_t, secret=conf.ACCESS_SECRET_KEY, db_session=db_session
    )
    if access_data:
        await TokensService.ban_token(
            db_session=db_session,
            token=access_data,
            payload=schemas_t.JwtPayload(**access_data),
        )


async def get_current_user(
    token_data: schemas_t.JwtPayload = Depends(get_access),
    db_session: AsyncSession = Depends(get_session),
):
    user = await UserService.get_by_email(db_session, email=token_data.sub)

    if not user:
        # Можно кидать 404 с юзер нот фоунд, но т.к. токен валиден,
        #  но я думаю лучше использовать одинаковый ответ
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    return user


async def get_current_active_user(
    current_user: models_u.User = Depends(get_current_user),
):
    is_active = UserService.is_active(current_user)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User is not active"
        )

    return current_user


def __check_user_role(check_role_id: int, active_user: models_u.User):
    user_role_id = UserService.get_role_id(active_user)

    if check_role_id != user_role_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    return active_user


# Будет не особо актуально в скором времени
def get_current_user_user(
    current_active_user: models_u.User = Depends(get_current_active_user),
):
    return __check_user_role(0, current_active_user)


def get_current_mod_user(
    current_active_user: models_u.User = Depends(get_current_active_user),
):
    return __check_user_role(1, current_active_user)


def get_current_arbit_user(
    current_active_user: models_u.User = Depends(get_current_active_user),
):
    return __check_user_role(2, current_active_user)


def get_current_admin_user(
    current_active_user: models_u.User = Depends(get_current_active_user),
):
    return __check_user_role(3, current_active_user)
