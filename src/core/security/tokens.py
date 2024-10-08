import uuid
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any

from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

import core.settings as conf
from app.tokens import schemas, services


def create_jwt_token(
    type_: schemas.TokenType,
    email: str,
    secret: str,
    expires_delta: timedelta | float,
    user_id: int | None = None,
) -> str:
    if isinstance(expires_delta, float):
        expires_delta = timedelta(minutes=expires_delta)
        
    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "exp": expire,
        "sub": email,
        "session": str(uuid.uuid4()),
        "token_type": type_,
    }
    
    if user_id:
        to_encode["user_id"] = user_id
    
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=conf.ALGORITHM)

    return encoded_jwt


def create_new_token_set(email: str, user_id: int) -> Tuple[str, str]:
    access = create_jwt_token(
        type_=schemas.TokenType.access,
        email=email,
        user_id=user_id,
        secret=conf.ACCESS_SECRET_KEY,
        expires_delta=timedelta(minutes=conf.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh = create_jwt_token(
        type_=schemas.TokenType.refresh,
        email=email,
        user_id=user_id,
        secret=conf.REFRESH_SECRET_KEY,
        expires_delta=timedelta(minutes=conf.REFRESH_TOKEN_EXPIRE_MINUTES),
    )
    
    return access, refresh


async def verify_jwt_token(
    token: str, secret: str, db_session: AsyncSession
) -> schemas.JwtPayload | None:
    """
    Верифицирует исключительно логику обычного JWT + забанен ли токен!!
    В случае, если всё окей, возвращает token_data, иначе None
    """
    
    try:
        payload = jwt.decode(token, secret, algorithms=[conf.ALGORITHM])
    except JWTError:
        return None

    if await services.get_by_payload(
        db_session, payload=schemas.JwtPayload(**payload)
    ):
        return None

    return schemas.JwtPayload(**payload)
