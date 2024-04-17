from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import async_session

from app.offers.services.offers_my import *
from app.offers.schemas.offers import *
from app.offers.services.offers_public import *
from app.offers.models import Offer

from core.database.preload_data import preload_db_main


test_offer_name = "TEST"
test_offer_description = "TESTTEST"
test_offer_price = 100
test_offer_count = 10
test_category_value_ids = [1, 2, 3]
test_offer_id = None
test_offer_user_id = 1

test_offer_name_second = "TEST2"


async def test_init_test_db():
    async with async_session() as session:
        await preload_db_main(session)
    assert 1 == 1


async def test_offer_create():
    global test_offer_id
    async with async_session() as session:
        offer: Offer = await create_offer(
            db_session=session,
            user_id=test_offer_user_id,
            obj_in=CreateOffer(
                name=test_offer_name,
                description=test_offer_description,
                price=test_offer_price,
                count=test_offer_count,
                category_value_ids=test_category_value_ids
            )
        )
        test_offer_id = offer.id
        assert offer.name == test_offer_name
        assert offer.description == test_offer_description
        assert offer.user_id == test_offer_user_id


async def test_get_raw_offer_by_user_id():
    async with async_session() as session:
        offer: Offer = await get_raw_offer_by_user_id(
            db_session=session,
            user_id=test_offer_user_id,
            offer_id=test_offer_id
        )
        assert offer.name == test_offer_name
        assert offer.description == test_offer_description
        assert offer.user_id == test_offer_user_id


async def test_get_by_user_id_offer_id():
    async with async_session() as session:
        offer: Offer = await get_by_user_id_offer_id(
            db_session=session,
            user_id=test_offer_user_id,
            id=test_offer_id
        )
        assert offer["name"] == test_offer_name
        assert offer["description"] == test_offer_description


async def test_get_mini_by_user_id_offset_limit():
    async with async_session() as session:
        offer: list[Offer] = await get_mini_by_user_id_offset_limit(
            db_session=session,
            offset=test_offer_id-1,
            limit=1,
            user_id=test_offer_user_id,

        )
        
        assert offer[0]["name"] == test_offer_name
        assert offer[0]["description"] == test_offer_description


async def test_get_offer_by_carcass_id():
    async with async_session() as session:
        offers: list  = await get_offers_by_carcass_id(db_session=session, user_id=test_offer_user_id, carcass_id=1, offset=0, limit=10)
        assert test_offer_id in [offer["id"] for offer in offers]

        
async def test_get_offer_by_value_id():
    async with async_session() as session:
        offers: list  = await get_offers_by_value_id(db_session=session, user_id=test_offer_user_id, value_id=1, offset=0, limit=10)
        assert test_offer_id in [offer["id"] for offer in offers]

#НАДО ДУМАТЬ! 2 НИЖНИХ НЕ РАБОТАЮТ
async def test_update_offer():
    async with async_session() as session:
        offer_: Offer = await get_by_offer_id(db_session=session, id=test_offer_id)
        offer: Offer = await update_offer(db_session=session, db_obj=offer_, obj_in=OfferBase(
            name=test_offer_name_second,
            description=test_offer_description,
            price=test_offer_price,
            count=test_offer_count,
            category_value_ids=test_category_value_ids
        ))
        assert offer["name"] == test_offer_name_second


async def test_delete_offer():
    async with async_session() as session:
        offer: Offer = await delete_offer(db_session=session, user_id=test_offer_user_id, offer_id=test_offer_id)

        assert offer.name == test_offer_name_second