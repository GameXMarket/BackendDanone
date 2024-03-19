import logging

from fastapi import Depends, APIRouter, HTTPException, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from core.depends import depends as deps
from core.database import get_session
from .. import models, schemas, services
from app.tokens import schemas as schemas_t


logger = logging.getLogger("uvicorn")
router = APIRouter()
ws_router = APIRouter()
base_session = deps.UserSession()
base_connection_manager = services.ChatConnectionManager()


@router.get("/my/getchat/")
async def get_chat_by_user_id(user_id: int):
    
    ...


@router.get("/my/getall")
async def get_all_chats_with_offset_limit(offser: int, limit: int):
    
    ...


@router.get("/my/getmessages")
async def get_all_messages_with_offset_limit(chat_id: int, offser: int, limit: int):
    
    ...


@ws_router.websocket("/my")
async def users_chat_listener(
    ws_context_data: tuple[
        services.ConnectionContext, services.ChatConnectionManager
    ] = Depends(base_connection_manager),
):
    conn_context, conn_manager = ws_context_data
    await conn_manager.connect(conn_context)

    try:
        await conn_manager.start_listening(conn_context)
    except WebSocketDisconnect:
        await conn_manager.disconnect(conn_context)
