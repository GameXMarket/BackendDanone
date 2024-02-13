import time
from typing import Tuple, List, Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, exists, delete, and_

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


async def get_associated_by_id(
    db_session: AsyncSession, root_id: int, options: List[Tuple[Any]] = None, v_ids: set = set()
):
    ...    

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
