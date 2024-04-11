import asyncio
from gevent import monkey; monkey.patch_all()
from gevent import Greenlet
from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import create_new_token_set

from app.users.models import User
from app.users.schemas import UserSignUp
from app.users.services import create_user
from main import app

pytest.mark.anyio

# Просто пример выполнения теста
# В коде таски предполагается использование более продвинутых механизмов
# К примеру подмена depends, также возможно придётся переработать код в некоторых местах
# К примеру перенести класс почты в depends через вызов __call__ и return self
# Всё это нужно будет примерно обсуждать, но я надеюсь от тебя услышать продуманные решения :)

async def insert_test_user(session: AsyncSession, cookies: bool = True):
    user: User = await create_user(
        db_session=session,
        obj_in=UserSignUp(
            password="14881488",
            email="jugerror1@gmail.com",
            username="djangofree"
        )
    )
    email = await user.email
    user_id = await user.id
    access, refresh = create_new_token_set(email=email, user_id=user_id)

    if not cookies:
        return user
    return user, access, refresh

async def test_user(async_client: AsyncClient):
    response = await async_client.get("/users/me")
    assert response.status_code == 401


async def test_auth_user_get(async_client: AsyncClient, session: AsyncSession):    
    user_data, access, refresh = await insert_test_user(session=session)
    async_client.cookies = {"access": access, "refresh": refresh}
    response = await async_client.get("/users/me")
    assert response.status_code == 200
    assert response.json()["email"] == user_data.email
    assert response.json()["username"] == user_data.username


async def test_sign_up(async_client: AsyncClient):
    response = await async_client.post("/users/me", json =
                                       {
                                           "password": "14881488",
                                           "email": "jugerror@gmail.com",
                                           "username": "testuser",
                                       })
    print(response.text)
    assert response.status_code == 200


async def test_remove_user_without_auth(async_client: AsyncClient, headers):
    body = {
        "password": "14881488",
    }
    response = await async_client.request(method="DELETE", url="/users/me", json={
        "password": "14881488",
    }, headers=headers)
    print(response.text)
    assert response.status_code == 200


async def test_remove_user_with_auth(async_client: AsyncClient, session: AsyncSession):
    print(async_client.cookies)
    response = await async_client.delete("/users/me")
    assert response.status_code == 200

