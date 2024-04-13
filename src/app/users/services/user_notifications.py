from typing import Any

from fastapi.responses import StreamingResponse
from fastapi import Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.utils.sse import SseQueue
from core.database import get_session
from app.tokens import schemas as schemas_t
from core import depends as deps


default_session = deps.UserSession()


class UserNotificationManager:
    def __init__(self) -> None:
        self.sse_managers: dict[int, SseQueue] = {}

    async def __call__(
        self,
        current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
            default_session
        ),
        db_session: AsyncSession = Depends(get_session),
    ) -> StreamingResponse:
        token_data, user_context = current_session
        user = await user_context.get_current_active_user(db_session, token_data)        
        await self.__create_new_notification_listener(user.id)
        sse_respone = self.get_sse_response(user.id)
        if not sse_respone:
            raise HTTPException(404)
        
        return sse_respone 

    async def __create_new_notification_listener(self, user_id: int):
        notification_listener = SseQueue()
        await notification_listener.create_event(
            event="system",
            data="connected",
            comment="base message for create new connection",
        )
        self.sse_managers[user_id] = notification_listener

    def get_user_listener(self, user_id: int):
        return self.sse_managers.get(user_id)

    def delete_user_listener(self, user_id: int):
        del self.sse_managers[user_id]
    
    def get_sse_response(self, user_id: int) -> None:
        listener = self.get_user_listener(user_id)
        if not listener:
            return None

        bd_tasks = BackgroundTasks()
        bd_tasks.add_task(self.delete_user_listener, user_id)
        response = StreamingResponse(
            listener.get_events(),
            media_type="text/event-stream",
            background=bd_tasks,
        )
        response.headers["Cache-Control"] = "no-cache"
        response.headers["Connection"] = "keep-alive"

        return response


user_notification_manager = UserNotificationManager()
