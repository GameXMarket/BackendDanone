import time
from typing import List, Literal, cast
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, aliased, make_transient
from sqlalchemy import select, update, exists, delete, and_, asc, func, desc

from .. import models as models_f
from .. import schemas as schemas_f
from app.users import models as models_u
from . import __offer_category_value as __ocv
from app.categories.models import CategoryCarcass, CategoryValue
from app.categories.services.categories_carcass import get_carcass_names
from app.categories.services.categories_values import get_many_by_ids, is_on_one_branch
from app.categories.services.categories_values import (
    get_value_ids_by_carcass,
    get_root_values,
)
from app.attachment.services import offer_attachment_manager
from app.attachment.services import category_value_attachment_manager


async def get_raw_offer_by_user_id(
    db_session: AsyncSession, user_id: int, offer_id: int
):
    stmt = select(models_f.Offer).where(
        models_f.Offer.user_id == user_id, models_f.Offer.id == offer_id
    )
    offer: models_f.Offer | None = (await db_session.execute(stmt)).scalar()

    if not offer:
        return None
    
    return offer


async def get_by_user_id_offer_id(
    db_session: AsyncSession, user_id: int, id: int
) -> dict | None:
    stmt = select(models_f.Offer).where(
        models_f.Offer.user_id == user_id, models_f.Offer.id == id
    )
    offer: models_f.Offer | None = (await db_session.execute(stmt)).scalar()

    if not offer:
        return None

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
    offer["files"] = files
    offer["category_values"] = category_value

    return offer


async def get_mini_by_user_id_offset_limit(
    db_session: AsyncSession,
    *,
    offset: int,
    limit: int,
    category_value_ids: list[int] = None,
    user_id: int,
    is_descending: bool = None,
    search_query: str = None,
    statuses: list[Literal["active", "hidden", "deleted"]] = ["active", "hidden", "deleted"],
) -> list[models_f.Offer]:
    stmt = (
        select(
            models_f.Offer.id,
            models_f.Offer.name,
            models_f.Offer.description,
            models_f.Offer.price,
        )
        .where(models_f.Offer.user_id == user_id)
        .where(models_f.Offer.status.in_(statuses))
        .order_by(
            desc(models_f.Offer.updated_at)
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
        offer = {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "price": row[3],
            "files_offer": files_offer,
            "category_values": category_value,
        }
        result.append(offer)

    return result


async def get_root_categories_count_with_offset_limit(
    db_session: AsyncSession, user_id, offset, limit
):
    result = []
    root_values = await get_root_values(db_session)
    if not root_values:
        return None

    for value in root_values:
        stmt = (
            select(func.count())
            .select_from(models_f.Offer)
            .where(models_f.Offer.user_id == user_id)
            .where(models_f.OfferCategoryValue.category_value_id == value[0])
            .where(models_f.Offer.id == models_f.OfferCategoryValue.offer_id)
            .offset(offset)
            .limit(limit)
        )
        offer_count = (await db_session.execute(stmt)).scalar_one_or_none()
        if offer_count:
            files = await category_value_attachment_manager.get_only_files(db_session, value[0])
            result.append(
                {
                    "value_id": value[0],
                    "value_name": value[1],
                    "next_carcass_id": value[2],
                    "offer_count": offer_count,
                    "files": files,
                }
            )

    return result


async def get_offers_by_carcass_id(
    db_session: AsyncSession, user_id, carcass_id, offset, limit
):
    carcass_names = await get_carcass_names(db_session, carcass_id)
    if not carcass_names:
        return None

    next_value_ids = await get_value_ids_by_carcass(db_session, carcass_id)
    if not next_value_ids:
        return None

    stmt = (
        select(
            models_f.Offer.id,
            models_f.Offer.name,
            models_f.Offer.price,
            models_f.Offer.count,
            CategoryValue.value,
        )
        .where(models_f.Offer.user_id == user_id)
        .where(models_f.Offer.id == models_f.OfferCategoryValue.offer_id)
        .where(models_f.OfferCategoryValue.category_value_id.in_(next_value_ids))
        .where(CategoryValue.id == models_f.OfferCategoryValue.category_value_id)
    )

    rows = await db_session.execute(stmt)

    result = []
    for row in rows:
        files = await offer_attachment_manager.get_only_files(db_session, row[0])
        offer = {
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "count": row[3],
            "files": files,
            "carcass_select_name": carcass_names[0],
            "carcass_in_offer_name": carcass_names[1],
            "carcass_in_offer_value": row[4],
        }
        result.append(offer)

    return result


async def get_offers_by_value_id(
    db_session: AsyncSession, user_id, value_id, offset, limit
):
    GameCategoryValue = aliased(CategoryValue)
    CategoryValueNext = aliased(CategoryValue)
    
    GameOfferCategoryValue = aliased(models_f.OfferCategoryValue)
    AllOfferCategoryValue = aliased(models_f.OfferCategoryValue)
    
    stmt = (
        select(
            models_f.Offer,
            CategoryValueNext.value,
            CategoryCarcass,
        )
        .join(GameOfferCategoryValue, GameOfferCategoryValue.offer_id == models_f.Offer.id)
        .join(GameCategoryValue, GameCategoryValue.id == GameOfferCategoryValue.category_value_id)
        .join(CategoryCarcass, CategoryCarcass.id == GameCategoryValue.next_carcass_id)
        .join(CategoryValueNext, CategoryValueNext.carcass_id == CategoryCarcass.id)
        .join(AllOfferCategoryValue, AllOfferCategoryValue.offer_id == models_f.Offer.id)
        .where(GameOfferCategoryValue.category_value_id == value_id)
        .where(models_f.Offer.user_id == user_id)
        .where(CategoryValueNext.id == AllOfferCategoryValue.category_value_id)
        .offset(offset)
        .limit(limit)
    )
    rows = await db_session.execute(stmt)
    
    result = []
    for row in rows:
        offer: models_f.Offer = row[0]
        carcass: CategoryCarcass = row[2]
        real_offer_count = await offer.get_real_count(db_session)

        offer_ = {
            "id": offer.id,
            "name": offer.name,
            "price": offer.price,
            "count": real_offer_count,
            "carcass_select_name": carcass.select_name,
            "carcass_in_offer_name": carcass.in_offer_name,
            "carcass_in_offer_value": row[1],
        }
        result.append(offer_)

    return result


async def create_offer(
    db_session: AsyncSession, user_id: int, obj_in: schemas_f.CreateOffer, status: str = None
) -> models_f.Offer:
    js_obj = obj_in.model_dump(exclude_unset=True)
    category_ids = js_obj.pop("category_value_ids")

    if not await is_on_one_branch(db_session, category_ids):
        raise HTTPException(403, "Category value must be on one branch")
    
    is_offer_with_delivery_stmt = select(
        exists(CategoryValue.is_offer_with_delivery)
        .where(CategoryValue.id.in_(category_ids))
        .where(CategoryValue.is_offer_with_delivery == True)
    )
    is_offer_with_delivery = (await db_session.execute(is_offer_with_delivery_stmt)).scalar_one_or_none()
    is_autogive_enabled = False if is_offer_with_delivery else None
    
    db_obj = models_f.Offer(
        user_id=user_id,
        is_autogive_enabled=is_autogive_enabled,
        upped_at=int(time.time()),
        **js_obj,
    )
    
    if status:
        db_obj.status = status

    db_session.add(db_obj)
    await db_session.flush()

    for category_id in category_ids:
        await __ocv.create_offer_category_value(
            db_session, category_value_id=category_id, offer_id=db_obj.id
        )

    await db_session.commit()
    await db_session.refresh(db_obj)
    
    return db_obj


# ! need refactor...
async def update_offer(
    db_session: AsyncSession, db_obj: models_f.Offer, obj_in: schemas_f.OfferBase, need_commit: bool = True
):
    
    obj_data = jsonable_encoder(db_obj)

    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)

    category_value_ids = update_data.get("category_value_ids")
    if not await is_on_one_branch(db_session, category_value_ids):
        raise HTTPException(403, "Category value must be on one branch")
    
    for field in obj_data:
        if field in update_data:
            setattr(db_obj, field, update_data[field])

    category_value_ids = update_data.get("category_value_ids")
    if category_value_ids:
        db_obj.category_values.clear()
        for value in category_value_ids:
            await __ocv.create_offer_category_value(
                    db_session, category_value_id=value, offer_id=db_obj.id
                )
        
    db_session.add(db_obj)
    await db_session.commit()
    await db_session.refresh(db_obj)

    return db_obj


async def delete_offer(db_session: AsyncSession, user_id: int, offer_id: int):
    offer = await get_raw_offer_by_user_id(db_session, user_id=user_id, offer_id=offer_id)

    if not offer:
        return None

    await db_session.delete(offer)
    await db_session.commit()

    return offer


async def up_offer(db_session: AsyncSession, offer: models_f.Offer, interval: float):
    unix_interval = interval * 60
    if offer.upped_at + unix_interval <= datetime.now().timestamp():
        offer.upped_at = datetime.now().timestamp()
        db_session.add(offer)
        await db_session.commit()
        return offer
    else:
        wait_seconds = offer.upped_at + unix_interval - datetime.now().timestamp()
        wait_time = timedelta(seconds=wait_seconds)
        return f"Wait time to up: {wait_time}"