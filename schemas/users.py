import re
from typing import Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)

import core.configuration as conf


class UsernameField(BaseModel):
    username: str = Field(
        examples=["username"],
        max_length=conf.MAX_LENGTH_USERNAME,
        min_length=conf.MIN_LENGTH_USERNAME,
        pattern=conf.USERNAME_REGEX,
        strip_whitespace=True,
    )

    @field_validator("username")
    @classmethod  # Дописать валидацию никнейма если требуется
    def validate_username(cls, value: str):

        return value


class EmailField(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod  # Дописать валидацию почты если требуется
    def validate_email(cls, value: EmailStr):
        ...
        return value


class PasswordField(BaseModel):
    password: str = Field(
        examples=["password"],
        max_length=conf.MAX_LENGTH_PASSWORD,
        min_length=conf.MIN_LENGTH_PASSWORD,
        pattern=conf.PASSWORD_REGEX,
        strip_whitespace=True,
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):

        return value


class BaseUser(UsernameField, EmailField):
    """Базовая модель пользователя"""

    pass


class UserSignUp(UsernameField, EmailField, PasswordField):
    """Модель User'а, используется там, где требуется пароль и никнейм и почта"""

    pass


class UserLogin(EmailField, PasswordField):
    """Модель User'а, используется там, где требуется пароль и почта"""

    pass


class UserUpdate(UsernameField, PasswordField):
    """Используется для изменения имени и пароля"""

    unverify_user: bool = False
    auth: PasswordField


class UserPreDB(BaseUser):
    """
    Содержит поля, без секретов, но данные поля заполняются только через бекенд
    Подходит для возврата через api
    """

    id: int
    is_verified: bool = False
    role_id: int = 0
    created_at: int  # Unix - time


class UserInDB(UserPreDB):
    """Полноценная модель, лежащая в базе данных."""

    hashed_password: str


class UserInfo(BaseModel):
    """Модель, отражающая информацию"""

    detail: str


class UserError(UserInfo):
    """Модель, отражающая информацию о возможных, обработанных ошибках эдпоинтов"""

    pass
