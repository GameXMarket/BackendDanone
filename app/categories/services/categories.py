import time
from typing import Tuple, Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists, delete, and_

from .. import models, schemas


async def get_by_id(db_session: AsyncSession, *, id: int, options: Tuple[Any] = None):
    stmt = select(models.Category).where(models.Category.id == id)
    if options:
        stmt = stmt.options(options[0](options[1]))
    category: models.Category | None = (await db_session.execute(stmt)).scalar()
    return category


async def get_all_with_offset_limit(db_session: AsyncSession, offset: int, limit: int):
    stmt = (
        select(models.Category)
        .where(models.Category.parrent_id == None)
        .order_by(models.Category.created_at)
        .offset(offset)
        .limit(limit)
    )
    categories = [row.to_json() for row in (await db_session.execute(stmt)).scalars()]
    return categories


async def create_category(
    db_session: AsyncSession,
    *,
    author_id: int,
    obj_in: schemas.CategoryCreate,
    parrent_id: int | None = None,
):
    db_obj = models.Category(
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
    db_obj: models.Category,
    obj_in: schemas.CategoryUpdate,
):
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

    ...


async def delete_category(db_session: AsyncSession, *, category_id: int):
    category = await get_by_id(db_session, id=category_id)

    if not category:
        return None

    await db_session.delete(category)
    await db_session.commit()

    return category
