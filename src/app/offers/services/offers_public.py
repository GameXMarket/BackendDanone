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
import app.categories.models as models_c
from app.attachment.services import offer_attachment_manager
from app.attachment.services import user_attachment_manager
from app.categories.services.categories_values import get_many_by_ids
from app.users.services import get_by_id


# Дублирование кода, можно переписать по нормальному старые методы,
#  однако пока не понятно как именно всё будет использоваться, потому
#  сейчас данный код будет дублироваться, до момента рефакторинга
async def get_raw_offer_by_id(
    db_session: AsyncSession, id: int,
):
    stmt = select(models_f.Offer).where(models_f.Offer.id == id).where(models_f.Offer.status == "active")
    offer: models_f.Offer | None = (await db_session.execute(stmt)).scalar()

    if not offer:
        return None

    return offer


async def get_offer_by_id(
    db_session: AsyncSession, id: int,
) -> None | dict:
    stmt = select(models_f.Offer).where(models_f.Offer.id == id).where(models_f.Offer.status == "active")
    offer: models_f.Offer | None = (await db_session.execute(stmt)).scalar()

    if not offer:
        return None

    user = await get_by_id(db_session=db_session, id=offer.user_id)
    user_files = await user_attachment_manager.get_only_files(
        db_session=db_session, user_id=user.id
    )
    stmt = select(models_f.OfferCategoryValue.category_value_id).where(
        models_f.OfferCategoryValue.offer_id == offer.id
    )
    values = await db_session.execute(stmt)
    category_value_ids = [row[0] for row in values.fetchall()]
    categories = await get_many_by_ids(
        db_session=db_session, ids=category_value_ids, lazy_load_v=None
    )
    category_value = [
        {"id": category["id"], "value": category["value"]} for category in categories
    ]
    files = await offer_attachment_manager.get_only_files(db_session, offer.id)
    offer = offer.to_dict()
    offer["offer_files"] = files
    offer["username"] = user.username
    offer["user_files"] = user_files
    offer["category_values"] = category_value

    return offer


async def get_mini_by_offset_limit(
    db_session: AsyncSession,
    *,
    offset: int,
    limit: int,
    category_value_ids: list[int] = None,
    is_descending: bool = None,
    search_query: str = None,
) -> list[models_f.Offer]:
    stmt = (
        select(
            models_f.Offer.id,
            models_f.Offer.name,
            models_f.Offer.description,
            models_f.Offer.price,
            models_f.Offer.user_id,
        )
        .where(models_f.Offer.status == "active")
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
        stmt = select(models_f.OfferCategoryValue.category_value_id).where(
            models_f.OfferCategoryValue.offer_id == row[0]
        )
        values = await db_session.execute(stmt)
        category_value_ids = [row_[0] for row_ in values.fetchall()]
        categories = await get_many_by_ids(
            db_session=db_session, ids=category_value_ids, lazy_load_v=None
        )
        category_value = [
            {"id": category["id"], "value": category["value"]} for category in categories
        ]
        files_offer = await offer_attachment_manager.get_only_files(db_session, row[0])
        files_user = await user_attachment_manager.get_only_files(db_session, row[4])
        user = await get_by_id(db_session=db_session, id=row[4])
        offer = {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "price": row[3],
            "files_offer": files_offer,
            "files_user": files_user,
            "username": user.username,
            "category_values": category_value,
        }
        result.append(offer)

    return result
