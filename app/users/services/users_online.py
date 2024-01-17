import random
from typing import Any
from dataclasses import dataclass

from fastapi import Depends, WebSocket

from core import depends as deps
from core.redis import get_redis_client
from ..schemas import users_online
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
    ws_connections: dict[int, WebSocket] = {}
    
    def __init__(self):
        pass
    
    def __call__(
        self, websocket: WebSocket, current_session: tuple[schemas_t.JwtPayload, deps.WsUserSession] | None = Depends(deps.WsUserSession())
    ) -> Any: # переписать всю эту поеботу
        if current_session:
            is_auth_user = True
            token_data, user_context = current_session
            unique_id = token_data.user_id
        else:
            is_auth_user = False
            unique_id = random.randrange(10**19, 10**20)
        
        return ConnectionContext(websocket, is_auth_user, unique_id), self

    async def connect(self, conn_context: ConnectionContext):        
        await conn_context.websocket.accept()
        self.ws_connections[conn_context.unique_id] = conn_context.websocket

        async with get_redis_client() as redis_client:
            if conn_context.is_auth_user:
                await redis_client.sadd("online_users", conn_context.unique_id)
            
            # Добавить рассылку при изменении стейта
            subscribers = await redis_client.smembers(f"pub:{conn_context.unique_id}")
            
        print(f"user {conn_context.unique_id} connected\npubs: {subscribers}")
        await self.broadcast(True, subscribers, conn_context)

    async def disconnect(self, conn_context: ConnectionContext):
        del self.ws_connections[conn_context.unique_id]
        
        async with get_redis_client() as redis_client:
            if conn_context.is_auth_user:
                await redis_client.srem("online_users", conn_context.unique_id)
            
            # Добавить рассылку при изменении стейта
            subscribers = await redis_client.smembers(f"pub:{conn_context.unique_id}")
            
            # Удаление из всех ключей "sub:{conn_context.unique_id}" подписчика
            keys_to_delete = await redis_client.smembers(f"sub:{conn_context.unique_id}")
            await redis_client.delete(f"sub:{conn_context.unique_id}")
            
            for key in keys_to_delete:
                await redis_client.srem(f"pub:{int(key)}", conn_context.unique_id)
        
        await self.broadcast(False, subscribers, conn_context)

    async def broadcast(self, state: bool, subscribers: list[bytes], conn_context: ConnectionContext):
        for client in subscribers:
            if ws := self.ws_connections.pop(int(client), None):
                await ws.send_json({int(conn_context.unique_id): state})
    
    async def start_listening(self, conn_context: ConnectionContext):
        while True:
            # subscribe, unsubscribe
            # sub - subcriber (тот, кто подписывается)
            # pub - publisher (тот, кто раздаёт ивенты, на кого подписываются)
            data: dict[str, list[int]] = await conn_context.websocket.receive_json()
            subscribers: list[int] = data.get("subscribe", [])
            unsubscribers: list[int] = data.get("unsubscribe", [])
            
            if not subscribers and not unsubscribers:               
                continue
            
            response: dict = {}
            
            async with get_redis_client() as redis_client:
                if subscribers:
                    # Записываем пользователю всех на кого подписался
                    await redis_client.sadd(f"sub:{conn_context.unique_id}", *subscribers)
                    response["subscribe"] = []
                
                if unsubscribers:
                    # Удаляем у пользователя всех от кого отписался
                    await redis_client.srem(f"sub:{conn_context.unique_id}", *unsubscribers)
                    response["unsubscribe"] = "ok"
            
                for client in subscribers:
                    # Создаём список онлайн пользователей для отправки
                    response["subscribe"].append(
                        bool(await redis_client.sismember("online_users", client))
                    )
                    
                    # Расписываем саббера по публишерам
                    await redis_client.sadd(f"pub:{client}", conn_context.unique_id)
                    
                
                for client in unsubscribers:
                    
                    # Удаляем саббера из публишеров
                    await redis_client.srem(f"pub:{client}", conn_context.unique_id)
                    
            await conn_context.websocket.send_json(response)
