import logging

from fastapi import Depends, APIRouter, HTTPException, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from core.depends import depends as deps
from core.database import get_session
from .. import models, schemas, services
from app.tokens import schemas as schemas_t


logger = logging.getLogger("uvicorn")
router = APIRouter()
base_session = deps.UserSession()
base_manager = ...


@router.get(path="/")
async def get_messages(
    receiver_id: int,
    current_session: tuple[schemas_t.JwtPayload ,deps.UserSession] = Depends(base_session),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)
    
    messages = await services.get_with_offset_limit(db_session, user.id, receiver_id)
    
    if not messages:
        raise HTTPException(404)
    
    return messages


@router.get(path="/{message_id}")
async def get_message(
    message_id: int,
    current_session: tuple[schemas_t.JwtPayload ,deps.UserSession] = Depends(base_session),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)
    
    message = await services.get_by_id(db_session, user.id, message_id)
    
    if not message:
        raise HTTPException(404)
    
    return message


@router.websocket("/online/")
async def lazy_users_online(ws_context_data: tuple[ConnectionContext, OnlineConnectionManager] = Depends(base_manager)):
    conn_context, conn_manager = ws_context_data
    await conn_manager.connect(conn_context)
    
    try:
        await conn_manager.start_listening(conn_context)
    except WebSocketDisconnect:
        await conn_manager.disconnect(conn_context)



