import time
import asyncio
from typing import cast, Any, NoReturn, Sequence
from json.decoder import JSONDecodeError
from dataclasses import dataclass

from pydantic import ValidationError
from fastapi import Depends, WebSocket, WebSocketException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, union_all, desc, or_, and_, text, func
from sqlalchemy.orm import aliased
import sqlalchemy

from core import depends as deps
from core.database import context_get_session
from core.redis import get_redis_client, get_redis_pipeline
from app.messages import models as models_m
from app.messages import schemas as schemas_m
from app.messages import services as services_m
from app.users import models as models_u, services as services_u
from app.attachment.services import message_attachment_manager, user_attachment_manager
from app.tokens import schemas as schemas_t


class BaseChatManager:
    def __init__(self) -> None:
        pass

    async def create_chat(
        self, db_session: AsyncSession, need_commit: bool = True
    ) -> models_m.Chat:
        new_chat = models_m.Chat()
        db_session.add(new_chat)

        if need_commit:
            await db_session.commit()
        else:
            await db_session.flush()

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

    async def get_all_user_dialogs_ids_by_user_id(
        self, db_session: AsyncSession, user_id: int, offset: int, limit: int
    ) -> Sequence[int]:
        """
        Непубличный метод для подгрузки диалогов пользователя
        """
        FirstChatMember = aliased(models_m.ChatMember)
        SecondChatMember = aliased(models_m.ChatMember)
        
        stmt = (
            select(FirstChatMember.chat_id, models_u.User.username, models_u.User.id)
            .join(SecondChatMember, SecondChatMember.chat_id == FirstChatMember.chat_id)
            .join(models_u.User, models_u.User.id == SecondChatMember.user_id)
            .join(models_m.Chat, models_m.Chat.id == FirstChatMember.chat_id)
            .where(
                and_(
                    models_m.Chat.is_dialog == True,
                    FirstChatMember.user_id == user_id,
                    SecondChatMember.user_id != user_id,
                )
            )
            .offset(offset)
            .limit(limit)
        )
        rows = (await db_session.execute(stmt)).fetchall()
        
        dialogs_data = []
        for row in rows:
            count_msg_stmt = (
                select(func.count(models_m.Message.id))
                .join(models_m.ChatMember, models_m.ChatMember.id == models_m.Message.chat_member_id)
                .where(models_m.ChatMember.chat_id == row[0])
            )
            
            if (msg_count := (await db_session.execute(count_msg_stmt)).scalar()) == 0:
                continue
            
            dialog_data = {
                "chat_id": row[0],
                "message_count": msg_count,
                "interlocutor_id": row[2],
                "interlocutor_username": row[1],
                "interlocutor_files": await user_attachment_manager.get_only_files(
                    db_session, row[2]
                ),
            }
            dialogs_data.append(dialog_data)
        
        return dialogs_data

    async def get_dialog_id_by_user_id(
        self, db_session: AsyncSession, user_id: int, interlocutor_id: int
    ) -> int | None:
        """
        Публичный метод для получения чата с данным пользователем
        user_id - тот, кто запрашивает чат
        """
        FirstChatMember = aliased(models_m.ChatMember)
        SecondChatMember = aliased(models_m.ChatMember)

        interlocutor = await services_u.get_by_id(db_session, id=interlocutor_id)
        if not interlocutor: # Переделать когда будет более подробная обработка ошибок
            return None
        
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
        
        chat_id = (await db_session.execute(stmt)).scalar_one_or_none()
        if not chat_id:
            return None
        
        chat_data = {
            "chat_id": chat_id,
            "interlocutor_id": interlocutor_id,
            "interlocutor_username": interlocutor.username,
            "interlocutor_files": await user_attachment_manager.get_only_files(db_session, interlocutor_id)
        }
        
        return chat_data


class BaseChatMemberManager(BaseChatManager):
    def __init__(self) -> None:
        super().__init__()

    async def create_chat_member(
        self,
        db_session: AsyncSession,
        user_id: int,
        chat_id: int,
        need_commit: bool = True,
    ) -> models_m.ChatMember:
        new_member = models_m.ChatMember(user_id=user_id, chat_id=chat_id)
        db_session.add(new_member)

        if need_commit:
            await db_session.commit()
        else:
            await db_session.flush()

        await db_session.refresh(new_member)
        return new_member

    async def get_chat_member(
        self, db_session: AsyncSession, chat_member_id: int
    ) -> models_m.ChatMember | None:
        stmt = select(models_m.ChatMember).where(
            models_m.ChatMember.id == chat_member_id
        )
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
        chat = await self.create_chat(db_session, need_commit=False)
        for user_id in users_ids:
            await self.create_chat_member(
                db_session, user_id, chat.id, need_commit=False
            )

        await db_session.commit()
        return chat.id

    async def create_dialog(
        self, db_session: AsyncSession, user_id: int, interlocutor_id: int
    ):
        interlocutor = await services_u.get_by_id(db_session, id=interlocutor_id)
        if not interlocutor:
            return None

        chat_data = {
            "chat_id": await self.create_new_chat_with_members(db_session, user_id, interlocutor_id),
            "interlocutor_id": interlocutor_id,
            "interlocutor_username": interlocutor.username,
            "interlocutor_files": await user_attachment_manager.get_only_files(db_session, interlocutor_id)
        }
        
        return chat_data
    
    async def get_chat_member_id_by_chat_user_ids(
        self, db_session: AsyncSession, chat_id: int, user_id: int
    ) -> int | None:
        stmt = (
            select(models_m.ChatMember.id)
            .where(models_m.ChatMember.chat_id == chat_id)
            .where(models_m.ChatMember.user_id == user_id)
        )
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_users_ids_by_chat_id(
        self, db_session: AsyncSession, chat_id: int
    ) -> Sequence[int]:
        stmt = select(models_m.ChatMember.user_id).where(
            models_m.ChatMember.chat_id == chat_id
        )
        result = await db_session.execute(stmt)
        return result.scalars().all()


class BaseMessageManager(BaseChatMemberManager):
    def __init__(self) -> None:
        super().__init__()

    async def create_message(
        self,
        db_session: AsyncSession,
        chat_member_id: int,
        content: str,
        need_wait: int = 0,
    ) -> models_m.Message:
        new_message = models_m.Message(
            chat_member_id=chat_member_id,
            content=content,
            created_at=int(time.time()) + need_wait,
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
    
    async def create_system_message(self, db_session: AsyncSession, chat_id: int, content: str):
        new_message = models_m.SystemMessage(chat_id=chat_id, content=content)
        db_session.add(new_message)
        await db_session.commit()
        await db_session.refresh(new_message)
        return new_message

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
            select(models_m.Message.id, models_m.Message.content, models_m.Message.created_at, models_m.ChatMember.user_id)
            .join(
                models_m.ChatMember,
                models_m.Message.chat_member_id == models_m.ChatMember.id,
            )
            .where(models_m.ChatMember.chat_id == chat_id)
        )
        system_message_stmt = (
            cast(sqlalchemy.Select, select(models_m.SystemMessage.id, models_m.SystemMessage.content, models_m.SystemMessage.created_at, -1))
            .where(models_m.SystemMessage.chat_id == chat_id)
        )
        all_messages_stmt = (
            union_all(messages_stmt, system_message_stmt)
            .order_by(desc(text("created_at")))
            .offset(offset)
            .limit(limit)
        )
        
        rows = await db_session.execute(all_messages_stmt)
        
        result = []
        for id, content, created_at, user_id_ in rows:
            data = {
                "content": content,
                "created_at": created_at,
                "user_id": user_id_,
                "files":  await message_attachment_manager.get_only_files(
                    db_session, id
                ),
            }
            result.append(data)
        
        return result[::-1]
    
    async def create_message_by_sender_id(
        self, db_session: AsyncSession, sender_id: int, message: schemas_m.MessageCreate
    ):
        chat_member_id = await self.get_chat_member_id_by_chat_user_ids(
            db_session, message.chat_id, sender_id
        )
        
        if not chat_member_id:
            return None
        
        return await self.create_message(
            db_session, chat_member_id, message.content, message.need_wait
        )


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
    # ws_connections: {user_id, set[ws_connection]}
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
        self, message: schemas_m.MessageBroadcast, target_users_ids: list[int | bytes]
    ):
        for user_id in target_users_ids:
            if not (user_websockets := self.ws_connections.get(int(user_id))):
                continue

            msg_json = message.model_dump()
            for ws in user_websockets:
                await ws.send_json(msg_json)

    async def __send_message(
        self, conn_context: ConnectionContext, new_message: schemas_m.MessageCreate
    ):
        users_ids = None
        files = None

        async with get_redis_client() as redis:
            users_ids = await redis.smembers(f"chat_members:{new_message.chat_id}")

            async with context_get_session() as db_session:
                message = await message_manager.create_message_by_sender_id(
                    db_session, conn_context.user_id, new_message
                )
                
                if not message:
                    await self.__raise(conn_context, status.WS_1002_PROTOCOL_ERROR, "Not real chat_id")
                
                # todo сюда можно придумать решение получше, конечно
                #  а-ля проверять появился ли файл или нет или
                #  добавить pg listener на таблицу и уже там чекать
                #  но в pg listener могут быть проблемы, а проверка создаст ненужные? запросы
                if new_message.need_wait:
                    await conn_context.websocket.send_json(
                        {"message_id": message.id, "waiting": new_message.need_wait}
                    )
                    await asyncio.sleep(new_message.need_wait)
                    files = await message_attachment_manager.get_only_files(
                        db_session, message.id
                    )

                if not users_ids:
                    users_ids = await message_manager.get_users_ids_by_chat_id(
                        db_session, new_message.chat_id
                    )
                    await redis.sadd(f"chat_members:{new_message.chat_id}", *users_ids)
                    await redis.expire(f"chat_members:{new_message.chat_id}", 60 * 10)

        message_broadcast = schemas_m.MessageBroadcast(
            **{
                **message.to_dict(),
                "chat_id": new_message.chat_id,
                "user_id": conn_context.user_id,
                "files": files,
            }
        )
        await self.broadcast(message_broadcast, users_ids)

    async def start_listening(self, conn_context: ConnectionContext) -> NoReturn:
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
            else:
                await self.__send_message(conn_context, new_message)
