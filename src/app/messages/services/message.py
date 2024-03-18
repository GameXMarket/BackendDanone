import time
from typing import Any
from json.decoder import JSONDecodeError
from dataclasses import dataclass

from pydantic import ValidationError
from fastapi import Depends, WebSocket, WebSocketException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from core import depends as deps
from core.database import context_get_session
from app.messages import models as models_m
from app.messages import schemas as schemas_m
from app.messages import services as services_m
from app.tokens import schemas as schemas_t


# Chats crud
async def create_chat(db_session: AsyncSession) -> models_m.Chat:
    new_chat = models_m.Chat()
    db_session.add(new_chat)
    await db_session.commit()
    await db_session.refresh(new_chat)
    return new_chat


async def get_chat(db_session: AsyncSession, chat_id: int) -> models_m.Chat | None:
    stmt = select(models_m.Chat).where(models_m.Chat.id == chat_id)
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def update_chat(db_session: AsyncSession, chat_id: int) -> None:
    pass


async def delete_chat(db_session: AsyncSession, chat_id: int) -> models_m.Chat | None:
    chat = await db_session.get(models_m.Chat, chat_id)
    if chat:
        await db_session.delete(chat)
        await db_session.commit()
    
    return chat


# ChatMember crud
async def create_chat_member(db_session: AsyncSession, user_id: int, chat_id: int) -> models_m.ChatMember:
    new_member = models_m.ChatMember(user_id=user_id, chat_id=chat_id)
    db_session.add(new_member)
    await db_session.commit()
    await db_session.refresh(new_member)
    return new_member


async def get_chat_member(db_session: AsyncSession, member_id: int) -> models_m.ChatMember | None:
    stmt = select(models_m.ChatMember).where(models_m.ChatMember.id == member_id)
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def update_chat_member(db_session: AsyncSession, member_id: int, new_user_id: int, new_chat_id: int) -> models_m.ChatMember | None:
    member = await db_session.get(models_m.ChatMember, member_id)
    if member:
        member.user_id = new_user_id
        member.chat_id = new_chat_id
        await db_session.commit()
        return member


async def delete_chat_member(db_session: AsyncSession, member_id: int) -> models_m.ChatMember | None:
    member = await db_session.get(models_m.ChatMember, member_id)
    if member:
        await db_session.delete(member)
        await db_session.commit()
        return member


# Message crud
async def create_message(db_session: AsyncSession, chat_member_id: int, content: str, created_at: int) -> models_m.Message:
    new_message = models_m.Message(chat_member=chat_member_id, content=content, created_at=created_at)
    db_session.add(new_message)
    await db_session.commit()
    await db_session.refresh(new_message)
    return new_message


async def get_message(db_session: AsyncSession, message_id: int) -> models_m.Message | None:
    stmt = select(models_m.Message).where(models_m.Message.id == message_id)
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def update_message(db_session: AsyncSession, message_id: int, new_content: str, new_created_at: int) -> models_m.Message | None:
    message = await db_session.get(models_m.Message, message_id)
    if message:
        message.content = new_content
        message.created_at = new_created_at
        await db_session.commit()
        return message


async def delete_message(db_session: AsyncSession, message_id: int) -> models_m.Message | None:
    message = await db_session.get(models_m.Message, message_id)
    if message:
        await db_session.delete(message)
        await db_session.commit()
        return message


# Old functions
async def create_message(
    db_session: AsyncSession,
    sender_id: int,
    obj_in: schemas_m.Message,
) -> models_m.Message:
    db_obj = models_m.Message(
        **obj_in.model_dump(), sender_id=sender_id, created_at=int(time.time())
    )
    db_session.add(db_obj)
    await db_session.commit()
    return db_obj


@dataclass(frozen=True)
class ConnectionContext:
    """
    websocket: WebSocket
    user_id: int
    """

    websocket: WebSocket
    user_id: int


# TODO проверку на существавание юзера и тд
# Пока просто будут исключения из-за ограничений на бд
class ChatConnectionManager:
    ws_connections: dict[int, set[WebSocket]] = {}

    def __init__(self):
        pass

    async def __call__(
        self,
        websocket: WebSocket,
        current_session: tuple[schemas_t.JwtPayload, deps.WsUserSession]
        | None = Depends(deps.WsUserSession()),
    ) -> Any:
        if current_session:
            user_id = current_session[0].user_id
        else:
            await self.__raise(ConnectionContext(websocket, -1), 4000, reason="Could not validate credentials")

        return ConnectionContext(websocket, user_id), self

    async def __raise(
        self, conn_context: ConnectionContext, code: int, reason: str | None = None
    ):
        if conn_context.user_id != -1:
            await self.disconnect(conn_context)
        raise WebSocketException(code, reason)

    async def connect(self, conn_context: ConnectionContext):
        await conn_context.websocket.accept()
        if conn_context.user_id not in self.ws_connections:
            self.ws_connections[conn_context.user_id] = set()
            
        self.ws_connections[conn_context.user_id].add(conn_context.websocket)

    async def disconnect(self, conn_context: ConnectionContext):
        all_current_connections = self.ws_connections[conn_context.user_id]
        all_current_connections.remove(conn_context.websocket)
        if len(all_current_connections) == 0:
            del self.ws_connections[conn_context.user_id]

    async def broadcast(
        self, conn_context: ConnectionContext, message: models_m.Message
    ):
        all_current_user_connections = self.ws_connections[conn_context.user_id]
        
        for ws in all_current_user_connections:
            await ws.send_json(message.to_dict())
        
        if message.receiver_id == conn_context.user_id:
            return
        
        if message.receiver_id not in self.ws_connections:
            return

        all_current_chat_connections = self.ws_connections[message.receiver_id]
        for ws in all_current_chat_connections:
            await ws.send_json(message.to_dict())

    async def start_listening(self, conn_context: ConnectionContext):
        while True:
            try:
                new_message: schemas_m.Message = schemas_m.Message.model_validate(
                    await conn_context.websocket.receive_json()
                )
            except JSONDecodeError:
                await self.__raise(
                    conn_context,
                    code=status.WS_1003_UNSUPPORTED_DATA,
                )
            except ValidationError as e:
                await conn_context.websocket.send_text(
                    e.json(
                        include_context=False, include_input=False, include_url=False
                    )
                )
                await self.__raise(
                    conn_context,
                    code=status.WS_1003_UNSUPPORTED_DATA,
                )

            async with context_get_session() as db_session:
                message = await services_m.create_message(
                    db_session, conn_context.user_id, new_message
                )

            await self.broadcast(conn_context, message)
