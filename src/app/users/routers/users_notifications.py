import logging

from fastapi import Depends, APIRouter, status
from sqlalchemy.ext.asyncio import AsyncSession

from core import depends as deps
from core.database import get_session
from app.tokens import schemas as schemas_t


logger = logging.getLogger("uvicorn")
router = APIRouter()
default_session = deps.UserSession()


@router.get("/listeners/notifications")
async def user_sse_notifications(
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)
    
    