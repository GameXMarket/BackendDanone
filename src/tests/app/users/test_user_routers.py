import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


# Просто пример выполнения теста
# В коде таски предполагается использование более продвинутых механизмов
# К примеру подмена depends, также возможно придётся переработать код в некоторых местах
# К примеру перенести класс почты в depends через вызов __call__ и return self
# Всё это нужно будет примерно обсуждать, но я надеюсь от тебя услышать продуманные решения :)
async def test_user(async_client: AsyncClient):
    response = await async_client.get("/users/me")
    assert response.status_code == 401
