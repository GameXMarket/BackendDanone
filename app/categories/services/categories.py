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


