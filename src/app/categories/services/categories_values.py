import time
from inspect import cleandoc
from typing import Tuple, List, Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, aliased
from sqlalchemy import select, distinct, union_all, update, exists, delete, and_, text

from .. import models, schemas
from app.attachment.services import category_value_attachment_manager


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
    db_session: AsyncSession,
    ids: list[int],
    options: List[Tuple[Any]] = None,
    lazy_load_v: str = None,
):
    stmt = select(models.CategoryValue).where(models.CategoryValue.id.in_(ids))
    if options:
        for option in options:
            stmt = stmt.options(option[0](option[1]))
    values = (await db_session.execute(stmt)).scalars().all()
    
    return [{**v.to_dict(lazy_load_v), "files": await category_value_attachment_manager.get_only_files(db_session, v.id)} for v in values]



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
        .distinct()
        .join(stmt, models.CategoryValue.id == stmt.c.id)
    )
    
    return [{**m.to_dict(), "files": await category_value_attachment_manager.get_only_files(db_session, m.id)} for m in result.scalars().all()]


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


async def get_root_values(db_session: AsyncSession):
    stmt = (
        select(
            models.CategoryValue.id,
            models.CategoryValue.value,
            models.CategoryValue.next_carcass_id,
        )
        .where(models.CategoryCarcass.is_root == True)
        .where(models.CategoryValue.carcass_id == models.CategoryCarcass.id)
    )
    root_values = (await db_session.execute(stmt)).all()
    if root_values:
        return root_values
    return None


async def get_value_ids_by_carcass(db_session: AsyncSession, carcass_id: int):
    stmt = select(models.CategoryValue.id).where(
        models.CategoryValue.carcass_id == carcass_id
    )
    value_ids = (await db_session.execute(stmt)).scalars().all()
    if value_ids:
        return value_ids
    return None


async def get_all(db_session: AsyncSession):
    stmt = select(
        models.category_values.CategoryValue
    )
    return (await db_session.execute(stmt)).all()
