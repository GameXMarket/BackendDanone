import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.security import create_jwt_token
from app.users.models import User
from app.tokens.schemas import TokenType
import datetime
from main import app

# Просто пример выполнения теста
# В коде таски предполагается использование более продвинутых механизмов
# К примеру подмена depends, также возможно придётся переработать код в некоторых местах
# К примеру перенести класс почты в depends через вызов __call__ и return self
# Всё это нужно будет примерно обсуждать, но я надеюсь от тебя услышать продуманные решения :)

@pytest.mark.asyncio
async def test_user(async_client: AsyncClient):
    response = await async_client.get("/users/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_sign_up(async_client: AsyncClient, session: AsyncSession):
    user_data = {"email": "fagtedsfdsdt@gmail.com", "username": "saftdsaesdsdfdfsdst", "hashed_password": "testpassword"}
    user = User(**user_data)
    session.add(user)
    user.is_verified = True
    await session.commit()

    token = create_jwt_token(type_= TokenType.access, user_id=user.id, email=user_data["email"], secret="test", expires_delta=datetime.timedelta(minutes=5))
    async_client.cookies = {"access": token}
    response = await async_client.get("/users/me")
    assert response.status_code == 200
    assert response.json()["email"] == user_data["email"]
    assert response.json()["username"] == user_data["username"]