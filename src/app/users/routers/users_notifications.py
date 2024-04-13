import logging

from fastapi import APIRouter, Depends
from app.users.services import user_notification_manager

# for debug
from fastapi import HTTPException
from core.database import get_session
from app.tokens import schemas as schemas_t
from core import depends as deps
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_session
from core.utils.sse import SseQueue


default_session = deps.UserSession()


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
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    notify_listener: SseQueue = user_notification_manager.get_user_listener(user.id)
    if not notify_listener:
        raise HTTPException(404)

    await notify_listener.create_event(
        
        event=event,
        data="pong" if data == "ping" else data,
        comment=comment,
    )

    return {"status": "ok"}
