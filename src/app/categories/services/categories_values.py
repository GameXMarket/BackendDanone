import time
from inspect import cleandoc
from typing import Tuple, List, Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, aliased
from sqlalchemy import select, distinct, union_all, update, exists, delete, and_, text

from .. import models, schemas


async def get_by_id(
    db_session: AsyncSession, id: int, options: List[Tuple[Any]] = None
) -> models.CategoryValue | None:
    stmt = select(models.CategoryValue).where(models.CategoryValue.id == id)
    if options:
        for option in options:
            stmt = stmt.options(option[0](option[1]))
    value: models.CategoryValue | None = (await db_session.execute(stmt)).scalar()
    return value


async def get_many_by_ids(
    db_session: AsyncSession, ids: list[int], options: List[Tuple[Any]] = None
):
    stmt = select(models.CategoryValue).where(models.CategoryValue.id.in_(ids))
    if options:
        for option in options:
            stmt = stmt.options(option[0](option[1]))    
    values = (await db_session.execute(stmt)).scalars().all()
    
    return [v.to_dict("carcass") for v in values]


async def get_associated_by_id(
    db_session: AsyncSession, root_ids: List[int], options: List[Tuple[Any]] = None
) -> List[models.CategoryValue]:
    CategoryValueAlias = aliased(models.CategoryValue)

    stmt = (
        select(models.CategoryValue)
        .where(models.CategoryValue.id.in_(root_ids))
        .cte(name="categorytree", recursive=True)
    )

    recursive = select(CategoryValueAlias).join(
        stmt, CategoryValueAlias.carcass_id == stmt.c.next_carcass_id
    )
    stmt = stmt.union_all(recursive)

    result = await db_session.execute(
        select(models.CategoryValue)
        .where(models.CategoryValue.id.not_in(root_ids))
        .order_by(models.CategoryValue.id)
        .distinct().join(stmt, models.CategoryValue.id == stmt.c.id)
    )
    
    return [m.to_dict() for m in result.scalars().all()]


async def get_by_carcass_id(
    db_session: AsyncSession, *, carcass_id: int, options: List[Tuple[Any]] = None
) -> List[models.CategoryValue] | List[None]:
    stmt = select(models.CategoryValue).where(
        models.CategoryValue.carcass_id == carcass_id
    )
    if options:
        for option in options:
            stmt = stmt.options(option[0](option[1]))
    values: List[models.CategoryValue] | List[None] = (
        await db_session.execute(stmt)
    ).scalars()
    return values


async def create_value(
    db_session: AsyncSession,
    *,
    author_id: int,
    carcass_id: int,
    value: schemas.ValueCreate,
) -> models.CategoryValue:
    db_obj = models.CategoryValue(
        author_id=author_id,
        carcass_id=carcass_id,
        **value.model_dump(),
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )

    db_session.add(db_obj)
    await db_session.commit()

    return db_obj


async def update_value(
    db_session: AsyncSession,
    *,
    author_id: int,
    db_obj: models.CategoryValue,
    value: schemas.ValueCreate,
) -> models.CategoryValue:
    db_obj.updated_at = int(time.time())
    db_obj.author_id = author_id
    db_obj.value = value.value
    db_obj.next_carcass_id = value.next_carcass_id

    db_session.add(db_obj)
    await db_session.commit()
    return db_obj


async def delete_value(
    db_session: AsyncSession, *, value_id: int
) -> models.CategoryValue:
    value = await get_by_id(db_session, id=value_id)

    if not value:
        return None

    await db_session.delete(value)
    await db_session.commit()

    return value
