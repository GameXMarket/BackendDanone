from httpx import AsyncClient

from tests.app.users.test_user_routers import insert_test_user
from app.offers.services import create_offer
from app.offers.schemas import CreateOffer

from tests.conftest import async_session


base_endpoint = "offers/"

async def test_get_all(async_client: AsyncClient):
    response = await async_client.get(base_endpoint + "getall/"

    )
    assert response.status_code == 200


async def test_get_offer_by_id(async_client: AsyncClient):
    response_not_found = await async_client.get(
        base_endpoint + "1/"
    ) 
    assert response_not_found.status_code == 404
    async with async_session():
    await insert_test_user()