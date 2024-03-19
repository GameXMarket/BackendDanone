import time
from typing import List

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists, delete, and_, asc, func
from sqlalchemy.orm import selectinload

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


async def get_offers_by_price_name_filter(
    db_session: AsyncSession,
    is_descending=False,
    search_query=None,
    status: models_f.Offer.status = "active",
    category_values_ids: list[int] = None,
) -> list[models_f.Offer]:
    query = select(models_f.Offer)

    query = query.filter(models_f.Offer.status == status)

    if category_values_ids:
        subquery = (
            select(models_f.OfferCategoryValue.offer_id)
            .where(
                models_f.OfferCategoryValue.category_value_id.in_(category_values_ids)
            )
            .distinct()
        )
        query = query.where(models_f.Offer.id.in_(subquery))
    if search_query:
        query = query.where(models_f.Offer.name.ilike(f"%{search_query}%"))

    if is_descending:
        query = query.order_by(models_f.Offer.price.desc())
    else:
        query = query.order_by(models_f.Offer.price.asc())

    res = await db_session.execute(query)
    return res.scalars().all()



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
