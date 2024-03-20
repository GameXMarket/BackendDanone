import time
from typing import List

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists, delete, and_, asc, func, desc
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

    if not offer:
        return None
    
    files =  await offer_attachment_manager.get_only_files(db_session, offer.id)
    offer = offer.to_dict()
    offer["files"] = files

    return offer


async def get_mini_by_offset_limit(
    db_session: AsyncSession,
    *,
    offset: int,
    limit: int,
    category_value_ids: list[int] = None,
    is_descending: bool = None,
    search_query: str = None,
    status: models_f.Offer.status = "active",
) -> list[models_f.Offer]:
    stmt = (
        select(
            models_f.Offer.id,
            models_f.Offer.name,
            models_f.Offer.description,
            models_f.Offer.price,
        )
        .where(
            models_f.Offer.status == status
        )
        .order_by(
            desc(models_f.Offer.created_at)
            if is_descending is None
            else desc(models_f.Offer.price)
            if is_descending
            else asc(models_f.Offer.price)
        )
        .offset(offset)
        .limit(limit)
    )

    if category_value_ids:
        stmt = stmt.where(
            and_(
                models_f.Offer.category_values.any(
                    models_f.OfferCategoryValue.category_value_id == cv_id
                )
                for cv_id in category_value_ids
            )
        )

    if search_query:
        stmt = stmt.where(models_f.Offer.name.ilike(f"%{search_query}%"))

    rows = await db_session.execute(stmt)

    result = []
    for row in rows:
        files = await offer_attachment_manager.get_only_files(db_session, row[0])
        offer = {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "price": row[3],
            "files": files,
        }
        result.append(offer)

    return result
