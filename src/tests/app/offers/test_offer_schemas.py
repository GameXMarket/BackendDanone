import pytest
from pydantic import ValidationError

from app.offers.schemas.offers import *


async def test_offer_status_enum():
    assert OfferStatusEnum.active == "active"
    assert OfferStatusEnum.hidden == "hidden"
    assert OfferStatusEnum.deleted == "deleted"


async def test_category_value_ids_base():
    obj = CategoryValueIdsBase(category_value_ids=[1, 2, 3])
    assert obj.category_value_ids == [1, 2, 3]

    obj = CategoryValueIdsBase()
    assert obj.category_value_ids is None


async def test_offer_mini():
    obj = OfferMini(id=1, name="Offer name", description="Offer description")
    assert obj.id == 1
    assert obj.name == "Offer name"
    assert obj.description == "Offer description"


async def test_offer_pre_db():
    obj = OfferPreDB(
        id=1,
        name="Offer name",
        description="Offer description",
        price=1000,
        count=1,
        user_id=1,
        created_at=123456789,
        updated_at=123456789,
        upped_at=123456789,
    )
    assert obj.id == 1
    assert obj.name == "Offer name"
    assert obj.description == "Offer description"
    assert obj.price == 1000
    assert obj.count == 1
    assert obj.user_id == 1
    assert obj.status == "hidden"
    assert obj.created_at == 123456789
    assert obj.updated_at == 123456789
    assert obj.upped_at == 123456789

    with pytest.raises(ValidationError):
        OfferPreDB(
            id=1,
            name="Offer name",
            description="Offer description",
            price=1000,
            count=1,
            user_id=1,
            status="invalid_status",
            created_at=123456789,
            updated_at=123456789,
            upped_at=123456789,
        )


async def test_create_offer():
    obj = CreateOffer(
        name="Offer name",
        description="Offer description",
        price=1000,
        count=1,
        category_value_ids=[1, 2, 3],
    )
    assert obj.name == "Offer name"
    assert obj.description == "Offer description"
    assert obj.price == 1000
    assert obj.count == 1
    assert obj.category_value_ids == [1, 2, 3]


async def test_update_offer():
    obj = UpdateOffer(name="Updated offer name", description="Updated offer description", price=100, count=2)
    assert obj.name == "Updated offer name"
    assert obj.description == "Updated offer description"
    assert obj.price == 100
    assert obj.count == 2

async def test_offer_error():
    obj = OfferError(detail="Error detail")
    assert obj.detail == "Error detail"
