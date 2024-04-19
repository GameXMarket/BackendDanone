from pydantic import ValidationError
import pytest

from app.users.schemas import *


async def test_base_user_model():
    data = {
        "username": "test_user",
        "email": "test@example.com",
    }
    user = BaseUser(**data)
    assert user.username == data["username"]
    assert user.email == data["email"]


async def test_user_signup_model():
    data = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "test_password",
    }
    user = UserSignUp(**data)
    assert user.username == data["username"]
    assert user.email == data["email"]
    assert user.password == data["password"]


async def test_user_login_model():
    data = {
        "email": "test@example.com",
        "password": "test_password",
    }
    user = UserLogin(**data)
    assert user.email == data["email"]
    assert user.password == data["password"]


async def test_user_update_username_model():
    data = {
        "username": "new_username",
    }
    user = UserUpdateUsername(**data)
    assert user.username == data["username"]


async def test_user_update_password_model():
    data = {
        "password": "new_password",
        "code": 1234,
        "auth": {"password": "old_password"},
    }
    user = UserUpdatePassword(**data)
    assert user.password == data["password"]


async def test_user_pre_db_model():
    data = {
        "username": "test_user",
        "email": "test@example.com",
        "id": 1,
        "created_at": 1621371729,
        "updated_at": 1621371729,
    }
    user = UserPreDB(**data)
    assert user.username == data["username"]
    assert user.email == data["email"]
    assert user.id == data["id"]
    assert user.created_at == data["created_at"]
    assert user.updated_at == data["updated_at"]


async def test_user_in_db_model():
    data = {
        "username": "test_user",
        "email": "test@example.com",
        "id": 1,
        "created_at": 1621371729,
        "updated_at": 1621371729,
        "hashed_password": "hashed_password",
    }
    user = UserInDB(**data)
    assert user.username == data["username"]
    assert user.email == data["email"]
    assert user.id == data["id"]
    assert user.created_at == data["created_at"]
    assert user.updated_at == data["updated_at"]
    assert user.hashed_password == data["hashed_password"]


async def test_admin_signup_model():
    data = {
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin_password",
    }
    admin = AdminSignUp(**data)
    assert admin.username == data["username"]
    assert admin.email == data["email"]
    assert admin.password == data["password"]
    assert admin.role_id == 3
    assert admin.is_verified == True


async def test_invalid_email_signup():
    with pytest.raises(ValidationError):
        UserSignUp(username="test_user", email="invalid_email", password="password")
