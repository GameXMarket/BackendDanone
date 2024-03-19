import time
from typing import List

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists, delete, and_, asc, func

from .. import models as models_f
from .. import schemas as schemas_f
from app.users import models as models_u
from . import __offer_category_value as __ocv
from app.attachment.services import offer_attachment_manager


# Дублирование кода, можно переписать по нормальному старые методы,
#  однако пока не понятно как именно всё будет использоваться, потому
#  сейчас данный код будет дублироваться, до момента рефакторинга
async def get_by_offer_id(
        db_session: AsyncSession, *, id: int
) -> models_f.Offer | None:
    stmt = select(models_f.Offer).where(models_f.Offer.id == id)
    offer: models_f.Offer | None = (await db_session.execute(stmt)).scalar()
    files = await offer_attachment_manager.get_only_files(db_session, offer.id)
    offer = offer.to_dict()
    offer["files"] = files

    return offer


async def get_offers_by_price_filter(
        db_session: AsyncSession, price_min: int, price_max: int,
        status: models_f.Offer.status = "active"
) -> list[models_f.Offer]:
    stmt = select(models_f.Offer). \
        filter(models_f.Offer.price.between(price_min, price_max)). \
        filter(models_f.Offer.status == status)
    results = await db_session.execute(stmt)
    offers = results.scalars().all()

    filtered_offers = []
    for offer in offers:
        offer_info = await get_by_offer_id(db_session, id=offer.id)
        filtered_offers.append(offer_info)

    return filtered_offers


async def get_mini_by_offset_limit(
        db_session: AsyncSession, *, offset: int, limit: int, category_value_ids: list[int] = None
):
    stmt = (
        select(
            models_f.Offer.id,
            models_f.Offer.name,
            models_f.Offer.description,
            models_f.Offer.price,
        )
        .order_by(asc(models_f.Offer.created_at))
        .offset(offset)
        .limit(limit)
    )

    # сортировка по ids
    if category_value_ids:
        stmt = stmt.where(
            and_(
                models_f.Offer.category_values.any(models_f.OfferCategoryValue.category_value_id == cv_id)
                for cv_id in category_value_ids
            )
        )

    rows = (await db_session.execute(stmt)).all()

    r = []  # Уже лучше, но что-то не то
    for row in rows:
        files = await offer_attachment_manager.get_only_files(db_session, row[0])
        offer = {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "price": row[3],
            "files": files,
        }
        r.append(offer)

    return r
