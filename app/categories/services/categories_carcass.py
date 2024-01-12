import time
from typing import Tuple, List, Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists, delete, and_

from .. import models, schemas


async def get_by_id(db_session: AsyncSession, *, id: int, options: List[Tuple[Any]] = None) -> models.CategoryCarcass | None:
    stmt = select(models.CategoryCarcass).where(models.CategoryCarcass.id == id)
    if options:
        for option in options:
            stmt = stmt.options(option[0](option[1]))
    category: models.CategoryCarcass | None = (await db_session.execute(stmt)).scalar()
    return category


async def get_all_with_offset_limit(db_session: AsyncSession, offset: int, limit: int, options: List[Tuple[Any]] = None) -> List[models.CategoryCarcass]:
    stmt = (
        select(models.CategoryCarcass)
        .where(models.CategoryCarcass.parrent_id == None)
        .order_by(models.CategoryCarcass.created_at)
        .offset(offset)
        .limit(limit)
    )
    if options:
        for option in options:
            stmt = stmt.options(option[0](option[1]))
    categories = (await db_session.execute(stmt)).scalars()
    return categories


async def get_parents_recursive(db_session: AsyncSession, category_id: int) -> List[models.CategoryCarcass]:
    parents = []

    async def get_parent_recursive(category_id):
        parent_category: models.CategoryCarcass = await get_by_id(db_session, id=category_id)
        if parent_category:
            parents.append(parent_category)
            await get_parent_recursive(parent_category.parrent_id)

    await get_parent_recursive(category_id)    
    return sorted(parents, key=lambda x: x.created_at, reverse=True)


async def create_category(
    db_session: AsyncSession,
    *,
    author_id: int,
    obj_in: schemas.CategoryCarcassCreate,
    parrent_id: int | None = None,
) -> models.CategoryCarcass:
    db_obj = models.CategoryCarcass(
        parrent_id=parrent_id,
        author_id=author_id,
        name=obj_in.name,
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )

    db_session.add(db_obj)
    await db_session.commit()

    return db_obj


async def update_category(
    db_session: AsyncSession,
    *,
    author_id: int,
    db_obj: models.CategoryCarcass,
    obj_in: schemas.CategoryCarcassUpdate,
) -> models.CategoryCarcass:
    db_obj.updated_at = int(time.time())
    db_obj.author_id = author_id
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


async def delete_category(db_session: AsyncSession, *, category_id: int) -> models.CategoryCarcass:
    category = await get_by_id(db_session, id=category_id)

    if not category:
        return None

    await db_session.delete(category)
    await db_session.commit()

    return category
