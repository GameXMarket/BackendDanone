import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.messages import models as messages_models
from app.messages import schemas as messages_shemas


async def get_by_id(db_session: AsyncSession, sender_id: int, message_id: int):
    stmt = select(messages_models.Message).where(messages_models.Message.sender_id == sender_id and messages_models.Message.id == message_id)
    return (await db_session.execute(stmt)).scalar_one_or_none()


async def get_with_offset_limit(db_session: AsyncSession, sender_id: int, receiver_id: int):
    stmt = select(messages_models.Message).where(messages_models.Message.sender_id == sender_id and messages_models.Message.receiver_id == receiver_id)
    return (await db_session.execute(stmt)).scalars().all()


async def create_message(
    db_session: AsyncSession,
    *,
    sender_id: int,
    obj_in: messages_shemas.Message,
):
    db_obj = messages_models.Message(
        **obj_in.model_dump(),
        sender_id=sender_id,
        created_at=int(time.time())
        
    )
    db_session.add(db_obj)
    await db_session.commit()
    return db_obj




