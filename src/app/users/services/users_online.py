import random
from typing import Any
from dataclasses import dataclass
from json.decoder import JSONDecodeError

from pydantic import ValidationError
from fastapi import Depends, WebSocket, WebSocketException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core import depends as deps
from core.database import get_session
from core.redis import get_redis_client, get_redis_pipeline
from app.users import schemas as schemas_u
from app.tokens import schemas as schemas_t


@dataclass(frozen=True)
class ConnectionContext:
    """
    websocket: WebSocket
    is_auth_user: bool
    unique_id: int
    """

    websocket: WebSocket
    is_auth_user: bool
    unique_id: int


class OnlineConnectionManager:
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
            is_auth_user = True
            unique_id = current_session[0].user_id
        else:
            is_auth_user = False
            unique_id = random.randrange(10**19, 10**20)

        return ConnectionContext(websocket, is_auth_user, unique_id), self

    async def __raise(
        self, conn_context: ConnectionContext, code: int, reason: str | None = None
    ):
        await self.disconnect(conn_context)
        raise WebSocketException(code, reason)

    async def connect(self, conn_context: ConnectionContext):
        await conn_context.websocket.accept()
        if conn_context.unique_id not in self.ws_connections:
            self.ws_connections[conn_context.unique_id] = set()

        self.ws_connections[conn_context.unique_id].add(conn_context.websocket)

        async with get_redis_client() as redis_client:
            if conn_context.is_auth_user:
                await redis_client.sadd("online_users", conn_context.unique_id)
                subscribers = await redis_client.smembers(
                    f"pub:{conn_context.unique_id}"
                )

        if conn_context.is_auth_user and subscribers:
            await self.broadcast(True, subscribers, conn_context)

    async def disconnect(self, conn_context: ConnectionContext):
        all_current_connections = self.ws_connections[conn_context.unique_id]
        all_current_connections.remove(conn_context.websocket)
        if len(all_current_connections) == 0:
            del self.ws_connections[conn_context.unique_id]
            

        async with get_redis_client() as redis_client:
            if conn_context.is_auth_user:
                await redis_client.srem("online_users", conn_context.unique_id)
                subscribers = await redis_client.smembers(
                    f"pub:{conn_context.unique_id}"
                )

            # Удаление из всех ключей "sub:{conn_context.unique_id}" подписчика
            keys_to_delete = await redis_client.smembers(
                f"sub:{conn_context.unique_id}"
            )
            await redis_client.delete(f"sub:{conn_context.unique_id}")

            for key in keys_to_delete:
                await redis_client.srem(f"pub:{int(key)}", conn_context.unique_id)

        if conn_context.is_auth_user and subscribers:
            await self.broadcast(False, subscribers, conn_context)

    async def broadcast(
        self, state: bool, subscribers: list[bytes], conn_context: ConnectionContext
    ):
        for client in subscribers:
            all_current_connections = self.ws_connections[int(client)]
            for ws in all_current_connections:
                await ws.send_json({int(conn_context.unique_id): state})

    async def start_listening(self, conn_context: ConnectionContext):
        while True:
            # subscribe, unsubscribe
            # sub - subcriber (тот, кто подписывается)
            # pub - publisher (тот, кто раздаёт ивенты, на кого подписываются)

            try:
                data: schemas_u.ReceiveData = schemas_u.ReceiveData.model_validate(
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

            if (
                conn_context.unique_id in data.subscribers
                or conn_context.unique_id in data.unsubscribers
            ):
                await self.__raise(
                    conn_context,
                    code=status.WS_1002_PROTOCOL_ERROR,
                    reason="user_id in subscribers or user_id in unsubscribers",
                )

            response: dict = {}

            async with get_redis_pipeline(need_client=True) as (
                redis_pipeline,
                pipe_client,
            ):

                if data.subscribers:
                    # Записываем пользователю всех на кого подписался
                    await redis_pipeline.sadd(
                        f"sub:{conn_context.unique_id}", *data.subscribers
                    )
                    await redis_pipeline.expire(
                        f"sub:{conn_context.unique_id}", 60 * 60 * 24
                    )
                    response["subscribe"] = []

                if data.unsubscribers:
                    # Удаляем у пользователя всех от кого отписался
                    await redis_pipeline.srem(
                        f"sub:{conn_context.unique_id}", *data.unsubscribers
                    )
                    response["unsubscribe"] = "ok"

                for client in data.subscribers:
                    # Создаём список онлайн пользователей для отправки,
                    # Выполням запрос вне пайплайна
                    response["subscribe"].append(
                        bool(await pipe_client.sismember("online_users", client))
                    )

                    if client in data.unsubscribers:
                        await self.__raise(
                            conn_context,
                            code=status.WS_1002_PROTOCOL_ERROR,
                            reason="subscribers user_id in unsubscribers",
                        )

                    # Расписываем саббера по публишерам
                    await redis_pipeline.sadd(f"pub:{client}", conn_context.unique_id)
                    await redis_pipeline.expire(f"pub:{client}", 60 * 60 * 24)

                for client in data.unsubscribers:
                    if client in data.subscribers:
                        await self.__raise(
                            conn_context,
                            code=status.WS_1002_PROTOCOL_ERROR,
                            reason="unsubscribers user_id in subscribers",
                        )

                    # Удаляем саббера из публишеров
                    await redis_pipeline.srem(f"pub:{client}", conn_context.unique_id)

            await conn_context.websocket.send_json(response)
