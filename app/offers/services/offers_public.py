import time
from typing import List

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists, delete, and_, asc

from .. import models as models_f
from .. import schemas as schemas_f
from app.users import models as models_u


# Дублирование кода, можно переписать по нормальному старые методы,
#  однако пока не понятно как именно всё будет использоваться, потому
#  сейчас данный код будет дублироваться, до момента рефакторинга
async def get_by_offer_id(
    db_session: AsyncSession, *, id: int
) -> models_f.Offer | None:
    stmt = select(models_f.Offer).where(models_f.Offer.id == id)
    offer: models_f.Offer | None = (await db_session.execute(stmt)).scalar()
    
    return offer


async def get_mini_by_offset_limit(
    db_session: AsyncSession, *, offset: int, limit: int
):
    stmt = (
        select(
            models_f.Offer.id,
            models_f.Offer.attachment_id,
            models_f.Offer.name,
            models_f.Offer.description,
            models_f.Offer.price,
        )
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


