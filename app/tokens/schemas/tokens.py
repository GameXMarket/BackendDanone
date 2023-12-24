from enum import Enum

from pydantic import BaseModel, EmailStr


class TokenType(str, Enum):
    access: str = "access"
    refresh: str = "refresh"
    email_verify: str = "email-verify"
    password_reset: str = "password_reset"


class JwtPayload(BaseModel):
    token_type: TokenType
    session: str
    exp: int
    sub: EmailStr


class TokenSet(BaseModel):
    access: str
    refresh: str


class BannedTokenInDB(BaseModel):
    id: int
    session_id: str
    expired_at: int


class TokenInfo(BaseModel):
    detail: str


class TokenError(TokenInfo):
    pass
