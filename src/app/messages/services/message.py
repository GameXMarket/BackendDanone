import time
from typing import cast, Any, NoReturn, Sequence
from json.decoder import JSONDecodeError
from dataclasses import dataclass

from pydantic import ValidationError
from fastapi import Depends, WebSocket, WebSocketException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import aliased

from core import depends as deps
from core.database import context_get_session
from core.redis import get_redis_client, get_redis_pipeline
from app.messages import models as models_m
from app.messages import schemas as schemas_m
from app.messages import services as services_m
from app.tokens import schemas as schemas_t


class BaseChatManager:
    def __init__(self) -> None:
        pass

    async def create_chat(self, db_session: AsyncSession) -> models_m.Chat:
        new_chat = models_m.Chat()
        db_session.add(new_chat)
        await db_session.commit()
        await db_session.refresh(new_chat)
        return new_chat

    async def get_chat(
        self, db_session: AsyncSession, chat_id: int
    ) -> models_m.Chat | None:
        stmt = select(models_m.Chat).where(models_m.Chat.id == chat_id)
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_chat(self, db_session: AsyncSession, chat_id: int) -> None:
        pass

    async def delete_chat(
        self, db_session: AsyncSession, chat_id: int
    ) -> models_m.Chat | None:
        chat = await db_session.get(models_m.Chat, chat_id)
        if chat:
            await db_session.delete(chat)
            await db_session.commit()

        return chat

    async def get_all_user_chats_ids_by_user_id(
        self, db_session: AsyncSession, user_id: int, offset: int, limit: int
    ) -> Sequence[int]:
        """
        Непубличный метод для подгрузки чатов пользователя
        """
        stmt = (
            select(models_m.ChatMember.chat_id)
            .where(models_m.ChatMember.user_id == user_id)
            .offset(offset)
            .limit(limit)
        )
        result = await db_session.execute(stmt)
        return result.scalars().all()

    async def get_dialog_id_by_user_id(
        self, db_session: AsyncSession, user_id: int, interlocutor_id: int
    ) -> int | None:
        """
        Публичный метод для получения чата с данным пользователем
        user_id - тот, кто запрашивает чат
        """
        FirstChatMember = aliased(models_m.ChatMember)
        SecondChatMember = aliased(models_m.ChatMember)

        stmt = (
            select(models_m.Chat.id)
            .where(models_m.Chat.is_dialog == True)
            .join(FirstChatMember, models_m.Chat.id == FirstChatMember.chat_id)
            .join(SecondChatMember, models_m.Chat.id == SecondChatMember.chat_id)
            .where(
                and_(
                    FirstChatMember.user_id == user_id,
                    SecondChatMember.user_id == interlocutor_id,
                )
            )
        )

        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()


class BaseChatMemberManager(BaseChatManager):
    def __init__(self) -> None:
        super().__init__()

    async def create_chat_member(
        self, db_session: AsyncSession, user_id: int, chat_id: int
    ) -> models_m.ChatMember:
        new_member = models_m.ChatMember(user_id=user_id, chat_id=chat_id)
        db_session.add(new_member)
        await db_session.commit()
        await db_session.refresh(new_member)
        return new_member

    async def get_chat_member(
        self, db_session: AsyncSession, chat_member_id: int
    ) -> models_m.ChatMember | None:
        stmt = select(models_m.ChatMember).where(models_m.ChatMember.id == chat_member_id)
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_chat_member(
        self,
        db_session: AsyncSession,
        member_id: int,
        new_user_id: int,
        new_chat_id: int,
    ) -> None:
        pass

    async def delete_chat_member(
        self, db_session: AsyncSession, chat_member_id: int
    ) -> models_m.ChatMember | None:
        member = await db_session.get(models_m.ChatMember, chat_member_id)
        if member:
            await db_session.delete(member)
            await db_session.commit()
            return member

    async def create_new_chat_with_members(
        self, db_session: AsyncSession, *users_ids: int
    ):
        chat = await self.create_chat(db_session)
        for user_id in users_ids:
            await self.create_chat_member(db_session, user_id, chat.id)

        return chat.id

    async def get_chat_member_id_by_chat_user_ids(self, db_session: AsyncSession, chat_id: int, user_id: int) -> int | None:
        stmt = (
            select(models_m.ChatMember.id)
            .where(models_m.ChatMember.chat_id == chat_id)
            .where(models_m.ChatMember.user_id == user_id)
        )
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()


class BaseMessageManager(BaseChatMemberManager):
    def __init__(self) -> None:
        super().__init__()

    async def create_message(
        self,
        db_session: AsyncSession,
        chat_member_id: int,
        content: str,
    ) -> models_m.Message:
        new_message = models_m.Message(
            chat_member_id=chat_member_id, content=content, created_at=int(time.time())
        )
        db_session.add(new_message)
        await db_session.commit()
        await db_session.refresh(new_message)
        return new_message

    async def get_message(
        self, db_session: AsyncSession, message_id: int
    ) -> models_m.Message | None:
        stmt = select(models_m.Message).where(models_m.Message.id == message_id)
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_message(
        self,
        db_session: AsyncSession,
        message_id: int,
        new_content: str,
        new_created_at: int,
    ) -> None:
        pass

    async def delete_message(
        self, db_session: AsyncSession, message_id: int
    ) -> models_m.Message | None:
        message = await db_session.get(models_m.Message, message_id)
        if message:
            await db_session.delete(message)
            await db_session.commit()
            return message

    async def get_messages_by_chat_id_user_id(
        self,
        db_session: AsyncSession,
        chat_id: int,
        user_id: int,
        offset: int,
        limit: int,
    ) -> Sequence[models_m.Message]:
        user_in_chat_stmt = select(models_m.ChatMember).where(
            and_(
                models_m.ChatMember.chat_id == chat_id,
                models_m.ChatMember.user_id == user_id,
            )
        )
        user_in_chat = await db_session.execute(user_in_chat_stmt)
        if not user_in_chat.scalar_one_or_none():
            return None

        messages_stmt = (
            select(models_m.Message, models_m.ChatMember.user_id)
            .join(
                models_m.ChatMember,
                models_m.Message.chat_member_id == models_m.ChatMember.id,
            )
            .where(models_m.ChatMember.chat_id == chat_id)
            .offset(offset)
            .limit(limit)
        )
        messages = await db_session.execute(messages_stmt)
        return [
            {**cast(models_m.Message, message).to_dict(), "user_id": cast(int, user_id)}
            for message, user_id in messages
        ]
    
    async def send_message(
        self,
        db_session: AsyncSession,
        sender_id: int,
        message: schemas_m.MessageCreate
    ):
        chat_member_id = await self.get_chat_member_id_by_chat_user_ids(db_session, message.chat_id, sender_id)
        await self.create_message(db_session, chat_member_id, message.content)
        
message_manager = BaseMessageManager()


@dataclass(frozen=True)
class ConnectionContext:
    """
    websocket: WebSocket
    user_id: int
    """

    websocket: WebSocket
    user_id: int


class ChatConnectionManager:
    #ws_connections: {user_id, set[ws_connection]}
    ws_connections: dict[int, set[WebSocket]] = {}

    def __init__(self) -> None:
        pass

    async def __call__(
        self,
        websocket: WebSocket,
        current_session: tuple[schemas_t.JwtPayload, deps.WsUserSession]
        | None = Depends(deps.WsUserSession()),
    ) -> tuple[ConnectionContext, "ChatConnectionManager"]:
        if current_session:
            user_id = current_session[0].user_id
        else:
            await self.__raise(
                ConnectionContext(websocket, -1),
                4000,
                reason="Could not validate credentials",
            )

        return ConnectionContext(websocket, user_id), self

    async def __raise(
        self, conn_context: ConnectionContext, code: int, reason: str | None = None
    ) -> NoReturn:
        if conn_context.user_id != -1:
            await self.disconnect(conn_context)
        raise WebSocketException(code, reason)

    async def connect(self, conn_context: ConnectionContext) -> None:
        await conn_context.websocket.accept()
        if conn_context.user_id not in self.ws_connections:
            self.ws_connections[conn_context.user_id] = set()

        self.ws_connections[conn_context.user_id].add(conn_context.websocket)

    async def disconnect(self, conn_context: ConnectionContext) -> None:
        all_current_connections = self.ws_connections[conn_context.user_id]
        all_current_connections.remove(conn_context.websocket)
        if len(all_current_connections) == 0:
            del self.ws_connections[conn_context.user_id]

    async def broadcast(
        self, conn_context: ConnectionContext, message: models_m.Message
    ):

        ...

    async def __send_message(
        self, conn_context: ConnectionContext, message: schemas_m.MessageCreate
    ):
        print(message.model_dump())
        async with context_get_session() as db_session:
            await message_manager.send_message(db_session, conn_context.user_id, message)
        
        

    async def start_listening(self, conn_context: ConnectionContext):
        while True:
            try:
                new_message: schemas_m.MessageCreate = (
                    schemas_m.MessageCreate.model_validate(
                        await conn_context.websocket.receive_json()
                    )
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

            await self.__send_message(conn_context, new_message)
