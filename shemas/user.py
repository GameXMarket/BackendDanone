import re

from pydantic import BaseModel, EmailStr, field_validator

try:
    import core.configuration as conf
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    import core.configuration as conf


class BaseUser(BaseModel):
    """Базовая модель пользователя

    Arguments:
        BaseModel - Базовая модель данных pydantic
    """

    username: str
    email: EmailStr

    @field_validator("username")
    @classmethod  # Дописать валидацию никнейма если требуется
    def validate_username(cls, value: str):
        if len(value) < conf.MIN_LENGTH_USERNAME:
            raise ValueError(
                f"username must be > {conf.MIN_LENGTH_USERNAME} characters long"
            )

        elif len(value) > conf.MAX_LENGTH_USERNAME:
            raise ValueError(
                f"username must be < {conf.MAX_LENGTH_USERNAME} characters long"
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


class UserSignup(BaseUser):
    """Почти полноценная модель User'а, используется дли регистрации

    Arguments:
        BaseUser - Базовая модель пользователя
    """
    
    password: str
    
    @field_validator("password")
    @classmethod  # ! Дописать валидацию пароля 
    def validate_email(cls, value: EmailStr):
        ...
        return value


class UserLogin(BaseUser):
    """Почти полноценная модель User'а, используется для ответа в авторизации

    Arguments:
        BaseUser - Базовая модель пользователя
    """
    
    token: str


class UserNoSecret(BaseUser):
    """Почти полноценная модель User'а, без некоторых приватных полей из БД

    Arguments:
        BaseUser - Базовая модель пользователя
    """

    is_verified: bool = False
    created_at: int  # Unix - time


class UserInDBase(UserNoSecret):
    """Полноценная модель, лежащая в базе данных.

    Arguments:
        UserNoSecret - Почти полноценная модель User'а, без некоторых приватных полей из БД
    """

    id: int
    hashed_password: str


class UserError(BaseModel):
    """Модель, отражающая информацию о возможных, обработанных ошибках эдпоинтов /users

    Arguments:
        BaseModel -- _description_
    """

    detail: str


if __name__ == "__main__":
    pass
