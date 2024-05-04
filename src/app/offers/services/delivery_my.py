from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .. import schemas as schemas_f
from .. import models as models_f


async def get_deliveries_by_offer_id(
        db_session: AsyncSession,
        offer_id: int,
        offset: int,
        limit: int
) -> list:
    stmt = select(models_f.Delivery).filter_by(
        offer_id=offer_id
    ).order_by(models_f.Delivery.created_at).offset(offset).limit(limit)
    result = await db_session.execute(stmt)
    deliveries = list(map(lambda delivery: delivery.to_dict(), result.scalars()))

    return deliveries


async def is_user_delivery(
        db_session: AsyncSession,
        user_id: int,
        delivery: models_f.Delivery
) -> bool:
    if not delivery:
        return False
    offer = await db_session.get(models_f.Offer, delivery.offer_id)
    return offer.user_id == user_id if offer else False


async def create_delivery(
        db_session: AsyncSession, obj_in: schemas_f.Delivery
) -> models_f.Delivery:
    js_obj = obj_in.model_dump(exclude_unset=True)
    db_obj = models_f.Delivery(
        **js_obj,
    )
    db_session.add(db_obj)
    await db_session.commit()
    return db_obj


async def update_delivery(
        db_session: AsyncSession, db_obj: models_f.Delivery, obj_in: schemas_f.Delivery
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

    return db_obj


async def get_delivery_by_id(db_session: AsyncSession, delivery_id: int):
    stmt = select(models_f.Delivery).where(
        models_f.Delivery.id == delivery_id
    )
    delivery: models_f.Delivery | None = (await db_session.execute(stmt)).scalar()

    if not delivery:
        return None

    return delivery


async def delete_delivery(db_session: AsyncSession, delivery_id: int):
    delivery = await get_delivery_by_id(db_session, delivery_id=delivery_id)

    if not delivery:
        return None

    await db_session.delete(delivery)
    await db_session.commit()

    return delivery
