from httpx import AsyncClient

from core.database.preload_data import preload_db_main
from core.security import create_new_token_set
from core.settings import config

from tests.conftest import async_session


base_endpoint = "offers/"


async def test_init_test_db():
    async with async_session() as session:
        await preload_db_main(session)
    assert 1 == 1


async def test_get_all(async_client: AsyncClient):
    response = await async_client.get(base_endpoint + "getall/")
    assert response.status_code == 200


async def test_get_offer_by_id(async_client: AsyncClient):
    response = await async_client.get(base_endpoint + "1/")
    assert response.status_code == 200


async def test_get_my_offers_without_auth(async_client: AsyncClient):
    response = await async_client.get(base_endpoint + "my/getall/")
    assert response.status_code == 401


async def test_get_auth(async_client: AsyncClient):
    access, refresh = create_new_token_set(
        email=config.BASE_ADMIN_MAIL_LOGIN, user_id=1
    )
    async_client.cookies = {"access": access, "refresh": refresh}
    assert 1 == 1


async def test_get_my_offers(async_client: AsyncClient):
    response = await async_client.get(base_endpoint + "my/getall/")
    assert response.status_code == 200


async def test_create_my_offer(async_client: AsyncClient):
    response = await async_client.post(
        base_endpoint + "my/",
        json={
            "name": "TEST",
            "description": "TESTTEST",
            "price": 100,
            "count": 2,
            "category_value_ids": [1, 2],
        },
    )
    assert response.status_code == 200


async def test_get_my_offers_by_categories(async_client: AsyncClient):
    response = await async_client.get(base_endpoint + "my/bycategories")
    assert response.status_code == 200


async def test_get_my_offers_bycarcassid(async_client: AsyncClient):
    response = await async_client.get(
        base_endpoint + "my/bycarcassid", params={"carcass_id": 1}
    )
    assert response.status_code == 200


async def test_get_my_offers_byvalueid(async_client: AsyncClient):
    response = await async_client.get(
        base_endpoint + "my/byvalueid", params={"value_id": 1}
    )
    assert response.status_code == 200


async def test_get_my_offer_by_id(async_client: AsyncClient):
    response = await async_client.get(
        base_endpoint + "my/3/",
    )
    assert response.status_code == 200


async def test_update_my_offer_by_id(async_client: AsyncClient):
    response = await async_client.put(
        base_endpoint + "my/3/",
        json={
            "name": "Offer name",
            "description": "Offer description",
            "price": 1000,
            "count": 1,
            "category_value_ids": [1],
        },
    )
    assert response.status_code == 200


async def test_get_my_offer_by_id(async_client: AsyncClient):
    response = await async_client.delete(
        base_endpoint + "my/1/",
    )
    assert response.status_code == 200
