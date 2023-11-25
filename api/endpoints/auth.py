from datetime import timedelta

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import schemas, models
from services import users as UserService
from api import deps
from core import security
from core import configuration
from core.database import get_session
from core.security import get_password_hash


router = APIRouter()
    # TODO Прописать модели response


@router.post(
    "/access-token",
)
async def set_token(
    form_data: schemas.UserLogin, db_session: Session = Depends(get_session), 
):
    # TODO Защита от xss, csrf (проверить аргументы по умолчанию)
    user: models.User = await UserService.authenticate(
        db_session=db_session,
        email=form_data.email,
        password=form_data.password,
        username=form_data.username,
    )

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email/username or password")
    elif not UserService.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=configuration.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(
        user.email, expires_delta=access_token_expires
    )
    
    response = JSONResponse(content=True)
    response.set_cookie(key="token", value=token)
    
    return response


@router.delete(
    "/access-token",
)
async def delete_token():
    # TODO Автоматически инвалидировать токен, путём созданя чёрного списка.
    response = JSONResponse(content=True)
    response.delete_cookie("token")
    
    return response


@router.post("/test-token")
def test_token(user = Depends(deps.get_current_user)):
    return user


@router.post("/verify-user/{username}")
async def verify_user(username: str, db_session: Session = Depends(get_session)):
    # TODO нормальная валидация запросов
    user = await UserService.get_by_username(db_session, username=username)
    await UserService.update_(db_session, db_obj=user, obj_in={"is_verified": True})
