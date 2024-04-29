import time
from inspect import cleandoc


from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, delete

from app.offers.services import get_raw_offer_by_id, update_offer
from .. import schemas as schemas_p, models as models_p
from app.offers import models as models_f


#  мб нужно начать писать более сложные обработчики ошибок, 
#   а не просто возвращать None в любое удобном случае
class PurchaseManager:
    def __init__(self) -> None:
        pass

    async def create_purchase(
        self,
        db_session: AsyncSession,
        user_id: int,
        new_purchase_data: schemas_p.PurchaseCreate,
    ):
        offer = await get_raw_offer_by_id(db_session, new_purchase_data.offer_id)
        
        if not offer:
            raise HTTPException(404, "Offer doesn't exist")
        
        # ! temp comment for debug
        #if offer.user_id == user_id:
        #    raise HTTPException(403, "BuyerID cannot be equal to the SellerID")
        
        offer_real_count = await offer.get_real_count(db_session)
        
        if new_purchase_data.count > offer_real_count:
            raise HTTPException(403, "There is not enough quantity")
        
        if not offer.is_autogive_enabled:
            await update_offer(db_session, offer, {"count": offer.count - new_purchase_data.count}, need_commit=False)
        
        # todo добавить логику времени на сделку
        purchase = models_p.Purchase(
            buyer_id=user_id,
            offer_id=offer.id,
            name=offer.name,
            description=offer.description,
            price=offer.price,
            count=new_purchase_data.count,
        )
        
        db_session.add(purchase)
        await db_session.flush()
        
        if offer.is_autogive_enabled:
            subquery = (
                select(models_f.Delivery.id)
                .where(models_f.Delivery.offer_id == offer.id).
                limit(new_purchase_data.count)
            )
            delete_delivery_subquery = (
                delete(models_f.Delivery)
                .where(models_f.Delivery.id.in_(subquery))
                .returning(models_f.Delivery.value)
            )
            q = await db_session.execute(delete_delivery_subquery)
            deleted_deliveries: list[str] = q.scalars().all()

            for delivery_value in deleted_deliveries:
                create_parcel_stmt = (
                    insert(models_p.Parcel)
                    .values(purchase_id=purchase.id, value=delivery_value)
                )
                await db_session.execute(create_parcel_stmt)
                await self.__update_purchase(db_session, purchase, {"status": "completed"})

        # todo добавить уведомления в систем месседж
        
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
            select(models_p.Purchase)
            .where(models_p.Purchase.id == purchase_id)
            .where(models_p.Purchase.buyer_id == buyer_id)
        )
        result = await db_session.execute(stmt)
        return result.scalars()

    async def __update_purchase(
        self,
        db_session: AsyncSession,
        db_obj: models_p.Purchase,
        obj_in: schemas_p.PurchaseInDB | dict
    ):
        obj_data = jsonable_encoder(db_obj)

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
            
        db_session.add(db_obj)
        await db_session.commit()
        await db_session.refresh(db_obj)

        return db_obj

    async def __delete_purchase(
        self,
        db_session: AsyncSession,
        user_id: int,
    ):
        pass
    
    async def get_all_purchases(
        self,
        db_session: AsyncSession,
        buyer_id: int,
        offset: int,
        limit: int

    ):
        stmt = (
            select(models_p.Purchase)
            .where(models_p.Purchase.buyer_id == buyer_id)
            .offset(offset)
            .limit(limit)
        )
        
        result = await db_session.execute(stmt)
        return result.scalars().all()


purchase_manager = PurchaseManager()
