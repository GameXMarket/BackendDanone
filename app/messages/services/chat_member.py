from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.messages.models import ChatMember


async def get_chat_member(session: AsyncSession, chat_member_id: int):
    result = await session.execute(select(ChatMember).where(ChatMember.id == chat_member_id))
    return result.scalar()


async def create_chat_member(session: AsyncSession, chat_id: int, user_id: int):
    chat_member_insert_stmt = insert(ChatMember).values(chat_id=chat_id, user_id=user_id)
    result = await session.execute(chat_member_insert_stmt)
    await session.commit()
    return result.first()


async def update_chat_member(session: AsyncSession, chat_member_id: int, new_user_id: int):
    chat_member_update_stmt = update(ChatMember).where(ChatMember.id == chat_member_id).values(user_id=new_user_id)
    result = await session.execute(chat_member_update_stmt)
    await session.commit()
    return result.rowcount


async def delete_chat_member(session: AsyncSession, chat_member_id: int):
    chat_member_delete_stmt = delete(ChatMember).where(ChatMember.id == chat_member_id)
    result = await session.execute(chat_member_delete_stmt)
    await session.commit()
    return result.rowcount > 0
