from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from core.security import tokens as TokenSecurity
from core.database import get_session
import core.depends as deps
import core.settings as conf
import app.users.schemas as schemas_u
import app.users.models as models_u
import app.users.services as UserService
import app.tokens.schemas as schemas_t
import app.tokens.models as models_t
import app.tokens.services as BannedTokensService


router = APIRouter()
# TODO Прописать модели response


@router.post(
    "/login",
)
async def token_set(
    form_data: schemas_u.UserLogin,
    db_session: Session = Depends(get_session),
):
    """Возвращает два токена (refresh и access), запрашивает почту и пароль"""

    user: models_u.User = await UserService.authenticate(
        db_session=db_session,
        email=form_data.email,
        password=form_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email/username or password"
        )
    elif not UserService.is_active(user):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

    access, refresh = TokenSecurity.create_new_token_set(form_data.email)
    
    if conf.DEBUG:
        response = JSONResponse(content={"detail": "tokens_added"})
        response.set_cookie(key="session", value=access)
        response.set_cookie(key="refresh", value=refresh)

        return response
    
    return schemas_t.TokenSet(access=access, refresh=refresh)


@router.post("/refresh")
def token_update(token_data: schemas_t.JwtPayload = Depends(deps.get_refresh)):
    """
    Данный метод принимает refresh токен, возвращает новую пару ключей
    """
    
    access, refresh = TokenSecurity.create_new_token_set(token_data.sub)

    if conf.DEBUG:
        response = JSONResponse(content={"detail": "tokens_updated"})
        response.set_cookie(key="session", value=access)
        response.set_cookie(key="refresh", value=refresh)

        return response

    return schemas_t.TokenSet(access=access, refresh=refresh)


@router.post(
    "/logout",
)
async def token_delete(banned: None = Depends(deps.auto_token_ban)):
    """
    Данный метод используются когда человек выходит из аккаунта\n
    Я не до конца уверен в их актуальности, также возможно стоит
     поместить данные методы в один путь /delete-tokens, который
     запрашивает сразу оба токена.
    """
    
    # TODO Доделать нормальное переключение между дебагом и продом
    response = JSONResponse(content={"detail": "deleted"})
    
    if conf.DEBUG:
        response.delete_cookie("token")
        response.delete_cookie("refresh")

        return response
    
    return response


@router.get(
    "/verify-user",
)
async def verify_user_email(token: str, db_session: Session = Depends(get_session)):
    """
    Метод используется для верификации пользователей, через почту\n
    Виден в документации только во время отладки.
    """
    token_data = await TokenSecurity.verify_jwt_token(
        token=token,
        secret=conf.EMAIL_SECRET_KEY,
        db_session=db_session
    )
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not found"
        )

    user = await UserService.get_by_email(db_session, email=token_data.sub)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if UserService.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already active"
        )

    user = await UserService.update_user(
        db_session, db_obj=user, obj_in={"is_verified": True}
    )
    
    banned_token = await BannedTokensService.ban_token(db_session, token=token)

    return schemas_u.UserPreDB(**user.to_dict())


@router.get(
    "/password-reset",
)
async def verify_password_reset(token: str, db_session: Session = Depends(get_session)):
    """
    Метод используется для верификации пользователей, через почту\n
    Виден в документации только во время отладки.
    """

    # TODO нормальная валидация запросов с почты + логика сброса по токену

    return "method in progress.."
