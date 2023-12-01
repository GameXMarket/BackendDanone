import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists, delete, and_

import models, schemas


async def get_by_payload(
    db_session: AsyncSession, *, payload: schemas.JwtPayload
) -> bool:
    stmt = select(models.BannedToken).where(
        models.BannedToken.session == payload.session
    )
    banned_token: models.BannedToken | None = (await db_session.execute(stmt)).scalar()
    return banned_token


async def create_(
    db_session: AsyncSession, *, token: str, payload: schemas.JwtPayload
) -> models.BannedToken | None:
    """
    Создаёт новую запись в банлисте
    """
    db_obj = models.BannedToken(expired_at=payload.exp, session=payload.session)

    db_session.add(db_obj)
    await db_session.commit()

    return db_obj


async def clean_expired(db_session: AsyncSession) -> int:
    """Очищает все просроченные jwt токены из блек листа"""
    current_time = int(time.time())
    stmt = select(models.BannedToken).where(
        models.BannedToken.expired_at < current_time
    )
    expired_tokens = (await db_session.execute(stmt)).scalars().all()

    for token in expired_tokens:
        db_session.delete(token)

    await db_session.commit()

    return len(expired_tokens)
