import logging

from fastapi import APIRouter, Depends

from core.sse.manager import BaseNotificationManager
# for debug
from fastapi import HTTPException
from core.database import get_session
from app.tokens import schemas as schemas_t
from core import depends as deps
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_session
from core.sse.queue import SseQueue


default_session = deps.UserSession()
user_notification_manager = BaseNotificationManager()


# Тут я скорее тестирую способы полной обработки роутеров в сервисах, чем пишу юзабельный код


logger = logging.getLogger("uvicorn")
router = APIRouter()


@router.get("/me/listeners/notifications")
async def user_sse_notifications_listener(
    sse_response=Depends(user_notification_manager),
):
    return sse_response


# debug
@router.post("/me/dev/create_notification")
async def test_function_for_tests(
    event: str = "test",
    data: str = "ping",
    comment: str = "comment",
    user_id: int = 1,
):
    context_manager = user_notification_manager.sse_managers.get(user_id)
    if not context_manager:
        raise HTTPException(404)

    await context_manager.create_event(
        event=event,
        data="pong" if data == "ping" else data,
        comment=comment,
    )

    return {"status": "ok"}
