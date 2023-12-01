import uuid
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any

from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

import schemas
import core.configuration as conf
from services import banned_tokens as BannedTokensService


def create_jwt_token(
    type_: schemas.TokenType,
    email: str,
    secret: str,
    expires_delta: timedelta,
) -> str:
    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "exp": expire,
        "sub": email,
        "session": str(uuid.uuid4()),
        "token_type": type_,
    }
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=conf.ALGORITHM)

    return encoded_jwt


def create_new_token_set(email: str) -> Tuple[str, str]:
    access = create_jwt_token(
        type_=schemas.TokenType.access,
        email=email,
        secret=conf.ACCESS_SECRET_KEY,
        expires_delta=timedelta(minutes=conf.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh = create_jwt_token(
        type_=schemas.TokenType.refresh,
        email=email,
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

    if await BannedTokensService.get_by_payload(
        db_session, payload=schemas.JwtPayload(**payload)
    ):
        return None

    return schemas.JwtPayload(**payload)
