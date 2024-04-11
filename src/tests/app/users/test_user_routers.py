import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, inspect

from core.security import create_new_token_set

from app.users.models import User
from app.tokens.schemas import TokenType
from main import app


# Просто пример выполнения теста
# В коде таски предполагается использование более продвинутых механизмов
# К примеру подмена depends, также возможно придётся переработать код в некоторых местах
# К примеру перенести класс почты в depends через вызов __call__ и return self
# Всё это нужно будет примерно обсуждать, но я надеюсь от тебя услышать продуманные решения :)


async def test_user(async_client: AsyncClient):
    response = await async_client.get("/users/me")
    assert response.status_code == 401


async def test_sign_up(async_client: AsyncClient, headers):
    body = {
        "password": "password",
        "email": "sokolovskipavel1@gmail.com",
        "username": "testusername",
    }
    response = await async_client.post(url="/users/me", json=body, headers=headers)
    assert response.status_code == 200


async def test_remove_user_without_auth(async_client: AsyncClient, headers):
    body = {
        "password": "password",
    }
    response = await async_client.delete("/users/me", json=body, headers=headers)
    assert response.status_code == 200


async def test_auth_user_get(async_client: AsyncClient, session: AsyncSession):
    user_data = {
        "email": "fagteddft@gmail.com",
        "username": "saftdsfdsdfdfsdst",
        "hashed_password": "testpassword",
    }
    user = User(**user_data)
    user_id = user.id
    session.add(user)
    user.is_verified = True
    await session.commit()
    await session.close()
    access, refresh = create_new_token_set(email=user_data["email"], user_id=user_id)
    async_client.cookies = {"access": access, "refresh": refresh}
    response = await async_client.get("/users/me")
    assert response.status_code == 200
    assert response.json()["email"] == user_data["email"]
    assert response.json()["username"] == user_data["username"]
