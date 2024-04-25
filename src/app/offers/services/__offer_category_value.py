import time
from typing import List, Optional

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists, delete, and_, asc

from ..models import OfferCategoryValue


async def create_offer_category_value(
    db_session: AsyncSession, *, category_value_id: int, offer_id: int
) -> OfferCategoryValue:
    offer_category_value = OfferCategoryValue(
        category_value_id=category_value_id,
        offer_id=offer_id
    )
    db_session.add(offer_category_value)
    await db_session.commit()
    await db_session.refresh(offer_category_value)
    return offer_category_value


async def get_offer_category_value_by_ids(
    db_session: AsyncSession, *, category_value_id: int, offer_id: int
) -> Optional[OfferCategoryValue]:
    stmt = select(OfferCategoryValue).where(
        OfferCategoryValue.category_value_id == category_value_id,
        OfferCategoryValue.offer_id == offer_id
    )
    result: Optional[OfferCategoryValue] = (await db_session.execute(stmt)).scalar_one_or_none()
    return result


async def update_offer_category_value(
    db_session: AsyncSession, *, category_value_id: int, offer_id: int, **updates
) -> OfferCategoryValue:
    stmt = select(OfferCategoryValue).where(
        OfferCategoryValue.category_value_id == category_value_id,
        OfferCategoryValue.offer_id == offer_id
    )
    offer_category_value: OfferCategoryValue = (await db_session.execute(stmt)).scalar_one()
    for attr, value in updates.items():
        setattr(offer_category_value, attr, value)
    await db_session.commit()
    await db_session.refresh(offer_category_value)
    return offer_category_value


async def delete_offer_category_value(
    db_session: AsyncSession, *, category_value_id: int, offer_id: int
) -> None:
    stmt = select(OfferCategoryValue).where(
        OfferCategoryValue.category_value_id == category_value_id,
        OfferCategoryValue.offer_id == offer_id
    )
    offer_category_value: OfferCategoryValue = (await db_session.execute(stmt)).scalar_one()
    await db_session.delete(offer_category_value)
    await db_session.commit()
