import logging

from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from core.security import tokens as TokenSecurity
from core.security import codes
from core.database import get_session
import core.depends as deps
import core.settings as conf
import app.users.schemas as schemas_u
import app.users.models as models_u
import app.users.services as UserService
import app.tokens.schemas as schemas_t
import app.tokens.models as models_t
import app.tokens.services as BannedTokensService


logger = logging.getLogger("uvicorn")
router = APIRouter(responses={200: {"model": schemas_t.TokenSet}})
default_session = deps.UserSession()

# ! Need refactoring


@router.post(path="/login")
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect email/username or password",
        )
    elif not UserService.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )

    access, refresh = TokenSecurity.create_new_token_set(form_data.email, user.id)

    response = JSONResponse({"access": access, "refresh": refresh})
    response.set_cookie(key="refresh", value=refresh)

    if conf.DEBUG:
        response.set_cookie(key="access", value=access)

    return response


@router.post(
    path="/refresh",
    responses=deps.build_response(deps.get_refresh),
)
async def token_update(
    token_data: schemas_t.JwtPayload = Depends(deps.get_refresh),
    db_session=Depends(get_session),
):
    """
    Данный метод принимает refresh токен, возвращает новую пару ключей
    """
    user = await UserService.get_by_email(db_session, email=token_data.sub)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    access, refresh = TokenSecurity.create_new_token_set(token_data.sub, user.id)

    response = JSONResponse({"access": access, "refresh": refresh})
    response.set_cookie(key="refresh", value=refresh)

    if conf.DEBUG:
        response.set_cookie(key="access", value=access)

    return response


@router.post(
    path="/logout",
    responses={
        **{200: {"model": schemas_t.TokenInfo}},
        **deps.build_response(deps.auto_token_ban),
    },
)
async def token_delete(banned: None = Depends(deps.auto_token_ban)):
    """
    Данный метод используются когда человек выходит из аккаунта, автоматически банит токены
    """

    response = JSONResponse(content={"detail": "deleted"})

    if conf.DEBUG:
        response.delete_cookie("access")
        response.delete_cookie("refresh")

    return response


@router.get(
    path="/verify-user",
    responses={
        404: {"model": schemas_u.UserError},
        409: {"model": schemas_u.UserError},
    },
)
async def verify_user_email(token: str, db_session: Session = Depends(get_session)):
    """
    Метод используется для верификации пользователей, через почту
    """
    token_data = await TokenSecurity.verify_jwt_token(
        token=token, secret=conf.EMAIL_SECRET_KEY, db_session=db_session
    )

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Token not found"
        )

    banned_token = await BannedTokensService.ban_token(
        db_session, token=token, payload=token_data
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

    access, refresh = TokenSecurity.create_new_token_set(user.email, user.id)

    response = JSONResponse({"access": access, "refresh": refresh})
    response.set_cookie(key="refresh", value=refresh)

    if conf.DEBUG:
        response.set_cookie(key="access", value=access)

    return response


@router.post(
    path="/password-reset",
    responses={
        404: {"model": schemas_u.UserError},
        409: {"model": schemas_u.UserError},
        200: {"model": schemas_u.UserPreDB},
    },
)
async def verify_password_reset(
    token: str,
    password_f: schemas_u.PasswordField,
    db_session: Session = Depends(get_session),
):
    """
    Метод используется для верификации пользователей, через почту
    """

    token_data = await TokenSecurity.verify_jwt_token(
        token=token, secret=conf.PASSWORD_RESET_SECRET_KEY, db_session=db_session
    )

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Token not found"
        )

    banned_token = await BannedTokensService.ban_token(
        db_session, token=token, payload=token_data
    )

    user = await UserService.get_by_email(db_session, email=token_data.sub)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not UserService.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User not active"
        )

    user = await UserService.update_user(
        db_session, db_obj=user, obj_in={"password": password_f.password}
    )

    return schemas_u.UserPreDB(**user.to_dict())


@router.post(
    path="/password-change",
    responses={
        404: {"model": schemas_u.UserError},
        409: {"model": schemas_u.UserError},
        200: {"model": schemas_u.UserUpdatePassword},
    },
)
async def verify_password_change(
    form_data: schemas_u.UserUpdatePassword,
    db_session: Session = Depends(get_session),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
            default_session
    ),
):
    token_data, user_context = current_session
    user: models_u.User = await user_context.get_current_active_user(db_session, token_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not UserService.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User not active"
        )

    is_valid, _ = await codes.verify_code(user_id=user.id, context="verify_password", code=form_data.code)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wrong code")

    user = await UserService.update_user(
        db_session, db_obj=user, obj_in={"password": form_data.password}
    )
    return 


@router.post(
    path="/email-change",
    responses={
        404: {"model": schemas_u.UserError},
        409: {"model": schemas_u.UserError},
        200: {"model": schemas_u.UserPreDB},
    },
)
async def verify_email_change(
    code: int,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
            default_session
    ),
    db_session: Session = Depends(get_session),
):
    token_data, user_context = current_session
    user: models_u.User = await user_context.get_current_active_user(db_session, token_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not UserService.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User not active"
        )

    valid = await verify_code(user_id=user.id, context="verify_email", code=code, need_delete=False)

    if not valid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wrong code")

    new_mail = await get_mail_from_redis(user.id)
    
    if not new_mail:
        raise HTTPException(403)
    
    user = await UserService.update_user(
        db_session, db_obj=user, obj_in={"email": new_mail}
    )
    await delete_mail_from_redis(user.id)
    return schemas_u.UserPreDB(**user.to_dict())
