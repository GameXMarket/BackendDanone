from dataclasses import dataclass
from uuid import uuid4

from fastapi.responses import StreamingResponse
from fastapi import Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.utils.sse import SseQueue
from core.database import get_session
from core.settings import config
from core import depends as deps
from app.tokens import schemas as schemas_t


default_session = deps.UserSession()


@dataclass
class SseManagerContext:
    listeners: dict[str, SseQueue]

    @staticmethod
    def get_new_manager() -> "SseManagerContext":
        return SseManagerContext({})

    def create_listener(self):
        user_uuid = uuid4().hex
        self.listeners[user_uuid] = SseQueue()
        return user_uuid

    def delete_listener(self, user_uuid: str):
        del self.listeners[user_uuid]

    def get_listener(self, user_uuid: str) -> SseQueue:
        return self.listeners.get(user_uuid)

    async def create_event(self, **event_data):
        """
        event: Optional[str] = None,
        data: Optional[str] = None,
        id: Optional[int] = None,
        retry: Optional[int] = None,
        comment: Optional[str] = None,
        """
        for listener in self.listeners.values():
            await listener.create_event(**event_data)


class __UserNotificationManager:
    def __init__(self) -> None:
        self.sse_managers: dict[int, SseManagerContext] = {}

    async def __call__(
        self,
        current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
            default_session
        ),
        db_session: AsyncSession = Depends(get_session),
    ) -> StreamingResponse:
        token_data, user_context = current_session
        user = await user_context.get_current_active_user(db_session, token_data)
        sse_response = await self.add_user(user.id)

        return sse_response

    async def add_user(self, user_id: int):
        context = self.sse_managers.get(user_id)
        if not context:
            context = SseManagerContext.get_new_manager()

        user_uuid = context.create_listener()
        self.sse_managers[user_id] = context

        if config.DEBUG:
            await context.create_event(
                event="system",
                data=f"connected - {user_uuid}\n"\
                    f"connected len: {len(context.listeners)}\n"\
                    f"members len: {len(self.sse_managers)}",
                comment="base message for create new connection",
            )

        return self.get_sse_response(user_id, user_uuid)

    def get_sse_response(self, user_id: int, user_uuid: str):
        context = self.sse_managers[user_id]
        if not context:
            return None

        listener = context.get_listener(user_uuid)

        bd_tasks = BackgroundTasks()
        bd_tasks.add_task(context.delete_listener, user_uuid)
        response = StreamingResponse(
            content=listener.get_events(),
            media_type="text/event-stream",
            background=bd_tasks,
        )
        response.headers["Cache-Control"] = "no-cache"
        response.headers["Connection"] = "keep-alive"

        return response


user_notification_manager = __UserNotificationManager()
