import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from app.offers.services import get_raw_offer_by_id, update_offer
from .. import schemas, models


#  мб нужно начать писать более сложные обработчики ошибок, 
#   а не просто возвращать None в любое удобном случае
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
            return 404
        
        offer_real_count = await offer.get_real_count(db_session)
        offer_with_delivery = offer.count == None
        
        if new_purchase_data.count > offer_real_count:
            return 403
        
        
        if not offer_with_delivery:
            await update_offer(db_session, offer, {"count": offer.count - new_purchase_data.count}, need_commit=False)
        
        # todo добавить логику времени на сделку
        purchase = models.Purchase(
            buyer_id=user_id,
            offer_id=offer.id,
            name=offer.name,
            description=offer.description,
            price=offer.price,
            count=new_purchase_data.count,
        )
        
        db_session.add(purchase)
        await db_session.flush()
        
        if offer_with_delivery:
            # todo тута перенос автовыдачи в покупку
            
            ...

        await db_session.commit()
        await db_session.refresh(purchase)
        
        return purchase

    async def get_purchase(
        self,
        db_session: AsyncSession,
        purchase_id: int,
        buyer_id: int,
    ):
        stmt = (
            select(models.Purchase)
            .where(models.Purchase.id == purchase_id)
            .where(models.Purchase.buyer_id == buyer_id)
        )
        result = await db_session.execute(stmt)
        return result.scalars()

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
        """
        Только для внутреннего использования
        """
        ...
    
    async def get_all_purchases(
        self,
        db_session: AsyncSession,
        buyer_id: int,
        offset: int,
        limit: int

    ):
        stmt = (
            select(models.Purchase)
            .where(models.Purchase.buyer_id == buyer_id)
            .offset(offset)
            .limit(limit)
        )
        
        result = await db_session.execute(stmt)
        return result.scalars().all()


purchase_manager = PurchaseManager()
