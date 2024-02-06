import time
from typing import List

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists, delete, and_, asc

from .. import models as models_f
from .. import schemas as schemas_f
from app.users import models as models_u


async def get_by_user_id_offer_id(
    db_session: AsyncSession, *, user_id: int, id: int
) -> models_f.Offer | None:
    stmt = select(models_f.Offer).where(
        models_f.Offer.user_id == user_id, models_f.Offer.id == id
    )
    offer: models_f.Offer | None = (await db_session.execute(stmt)).scalar()
    return offer


async def get_mini_by_user_id_offset_limit(
    db_session: AsyncSession, *, user_id, offset: int, limit: int
):
    stmt = (
        select(
            models_f.Offer.id,
            models_f.Offer.attachment_id,
            models_f.Offer.name,
            models_f.Offer.description,
            models_f.Offer.price,
        )
        .where(models_f.Offer.user_id == user_id)
        .order_by(asc(models_f.Offer.created_at))
        .offset(offset)
        .limit(limit)
    )

    offers = [
        schemas_f.OfferMini(
            id=offer[0],
            attachment_id=offer[1], name=offer[2], description=offer[3], price=offer[4]
        )
        for offer in (await db_session.execute(stmt)).all()
    ]

    return offers


async def create_offer(
    db_session: AsyncSession, *, user_id: int, obj_in: schemas_f.CreateOffer
) -> models_f.Offer:
    db_obj = models_f.Offer(
        user_id=user_id,
        status="active", # ! Temp testing
        **obj_in.model_dump(exclude_unset=True),
        created_at=int(time.time()),
        updated_at=int(time.time()),
        upped_at=int(time.time()),
    )

    db_session.add(db_obj)
    await db_session.commit()

    return db_obj


async def update_offer(
    db_session: AsyncSession, *, db_obj: models_f.Offer, obj_in: schemas_f.OfferBase
):
    db_obj.updated_at = int(time.time())

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


async def delete_offer(db_session: AsyncSession, *, user_id: int, offer_id: int):
    offer = await get_by_user_id_offer_id(db_session, user_id=user_id, id=offer_id)

    if not offer:
        return None

    await db_session.delete(offer)
    await db_session.commit()

    return offer
