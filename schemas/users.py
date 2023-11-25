import re
from typing import Optional

from pydantic import (
    BaseModel,
    EmailStr,
    field_validator,
    model_validator,
)

import core.configuration as conf


class BaseUser(BaseModel):
    """Базовая модель пользователя"""

    username: str
    email: EmailStr

    @field_validator("username")
    @classmethod  # Дописать валидацию никнейма если требуется
    def validate_username(cls, value: str):
        if len(value) < conf.MIN_LENGTH_USERNAME:
            raise ValueError(
                f"username must be >= {conf.MIN_LENGTH_USERNAME} characters long"
            )

        elif len(value) > conf.MAX_LENGTH_USERNAME:
            raise ValueError(
                f"username must be <= {conf.MAX_LENGTH_USERNAME} characters long"
            )

        # Проверка на специальные символы
        elif not re.match(conf.USERNAME_REGEX, value):
            raise ValueError(
                "username must contain only letters, numbers, and underscores"
            )

        # Проверка на начало с цифры
        elif value[0].isdigit():
            raise ValueError("username cannot start with a digit")

        # Проверка на наличие пробелов
        elif " " in value:
            raise ValueError("username cannot contain spaces")

        return value

    @field_validator("email")
    @classmethod  # Дописать валидацию почты если требуется
    def validate_email(cls, value: EmailStr):
        ...
        return value


class UserSignUp(BaseUser):
    """Модель User'а, используется там, где требуется пароль и никнейм И почта"""

    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):
        # Дополнительные проверки пароля, если нужны
        return value


class UserLogin(UserSignUp):
    """Модель User'а, используется там, где требуется пароль и никнейм ИЛИ почта"""

    username: Optional[str] = None
    email: Optional[EmailStr] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str):
        if value:
            return super().validate_username(value)

    @model_validator(mode="after")
    def check_fields_2(self):
        if not self.username and not self.email:
            raise ValueError("username or email must be provided")

        return self


class UserUpdate(UserLogin):
    @model_validator(mode="after")
    def check_fields_all(self):
        print(self.__dict__)


class UserPreDB(BaseUser):
    """Содержит поля, без секретов, но данные поля заполняются только через бекенд"""

    is_verified: bool = False
    role_id: int = 0
    created_at: int  # Unix - time


class UserInDB(UserPreDB):
    """Полноценная модель, лежащая в базе данных."""

    id: int
    hashed_password: str


class UserInfo(BaseModel):
    """Модель, отражающая информацию"""

    detail: str


class UserError(UserInfo):
    """Модель, отражающая информацию о возможных, обработанных ошибках эдпоинтов"""

    pass
