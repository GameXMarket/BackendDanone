import time
from typing import List

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, exists, delete, and_, asc, func

from .. import models as models_f
from .. import schemas as schemas_f
from app.users import models as models_u
from . import __offer_category_value as __ocv
from app.categories.models import CategoryCarcass, CategoryValue


async def get_by_user_id_offer_id(
    db_session: AsyncSession, user_id: int, id: int
) -> models_f.Offer | None:
    stmt = select(models_f.Offer).where(
        models_f.Offer.user_id == user_id, models_f.Offer.id == id
    )
    offer: models_f.Offer | None = (await db_session.execute(stmt)).scalar()
    return offer


async def get_mini_by_user_id_offset_limit(
    db_session: AsyncSession, user_id, offset: int, limit: int
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
            attachment_id=offer[1],
            name=offer[2],
            description=offer[3],
            price=offer[4],
        )
        for offer in (await db_session.execute(stmt)).all()
    ]

    return offers


async def __get_root_values(db_session: AsyncSession):
    root_values = (
        await db_session.execute(
            select(CategoryValue.id, CategoryValue.value)
            .where(CategoryCarcass.is_root == True)
            .where(CategoryValue.carcass_id == CategoryCarcass.id)  
        )
    ).all()
        
    return root_values


async def get_root_categories_with_offset_count(db_session: AsyncSession, user_id, offset, limit):
    root_values = await __get_root_values(db_session)
    result = []
    for value in root_values:
        rrr = (
            await db_session.execute(
                select(func.count())
                .select_from(models_f.Offer)
                .where(models_f.Offer.user_id == user_id)
                .where(models_f.OfferCategoryValue.category_value_id == value[0])
                .where(models_f.Offer.id == models_f.OfferCategoryValue.offer_id)
                .offset(offset).limit(limit)
            )
        ).scalar_one_or_none()
        result.append({"value_id": value[0], "value_name": value[1], "offer_count": rrr})
    
    return result
    
    
async def create_offer(
    db_session: AsyncSession, user_id: int, obj_in: schemas_f.CreateOffer
) -> models_f.Offer:
    js_obj = obj_in.model_dump(exclude_unset=True)
    category_ids = js_obj.pop("category_value_ids")
    db_obj = models_f.Offer(
        user_id=user_id,
        status="active",  # ! Temp testing
        **js_obj,
        created_at=int(time.time()),
        updated_at=int(time.time()),
        upped_at=int(time.time()),
    )

    db_session.add(db_obj)
    await db_session.flush()

    for category_id in category_ids:
        await __ocv.create_offer_category_value(
            db_session, category_value_id=category_id, offer_id=db_obj.id
        )

    await db_session.commit()
    return db_obj


# ! need refactor...
async def update_offer(
    db_session: AsyncSession, db_obj: models_f.Offer, obj_in: schemas_f.OfferBase
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

    category_ids_in: List[int] = obj_in.category_value_ids
    current_category_ids = {
        offer_category.category_value_id for offer_category in db_obj.category_values
    }

    # Create new associations
    for category_id in category_ids_in:
        if category_id not in current_category_ids:
            await __ocv.create_offer_category_value(
                db_session, category_value_id=category_id, offer_id=db_obj.id
            )
            current_category_ids.add(category_id)

    # Delete old associations
    for category_id in current_category_ids - set(category_ids_in):
        await __ocv.delete_offer_category_value(
            db_session, category_value_id=category_id, offer_id=db_obj.id
        )
        current_category_ids.remove(category_id)

    db_session.add(db_obj)
    await db_session.commit()

    return db_obj


async def delete_offer(db_session: AsyncSession, user_id: int, offer_id: int):
    offer = await get_by_user_id_offer_id(db_session, user_id=user_id, id=offer_id)

    if not offer:
        return None

    await db_session.delete(offer)
    await db_session.commit()

    return offer
