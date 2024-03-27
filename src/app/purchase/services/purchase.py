import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from app.offers.services import get_raw_offer_by_id
from .. import schemas, models


class PurchaseManager:
    def __init__(self) -> None:
        pass

    async def create_purchase(
        self,
        db_session: AsyncSession,
        user_id: int,
        new_purchase_data: schemas.PurchaseCreate,
    ):
        offer = await get_raw_offer_by_id(db_session, new_purchase_data.offer_id)
        
        if not offer:
            return None
        
        purchase = models.Purchase(
            buyer_id=user_id,
            offer_id=offer.id,
            name=offer.name,
            description=offer.description,
            price=offer.price
        )
        

    async def get_purchase(
        self,
        db_session: AsyncSession,
        user_id: int,
    ):
        ...

    async def update_purchase(
        self,
        db_session: AsyncSession,
        user_id: int,
    ):
        ...

    async def delete_purchase(
        self,
        db_session: AsyncSession,
        user_id: int,
    ):
        ...


purchase_manager = PurchaseManager()
