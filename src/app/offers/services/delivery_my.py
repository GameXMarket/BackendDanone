from fastapi.encoders import jsonable_encoder

from .. import schemas as schemas_f
from .. import models as models_f
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


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
