import logging

from fastapi import Depends, APIRouter, HTTPException, WebSocketDisconnect
from fastapi.responses import JSONResponse
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


@router.get("/my/getdialog/")
async def get_dialog_id_by_user_id(
    interlocutor_id: int,
    db_session: AsyncSession = Depends(get_session),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
) -> JSONResponse:
    """
    В диалогах - максимум двое участников, но физически может быть и больше
    Чаты сделаны с заделом на будущее, однако методы могут быть заточены именно под 2 участников
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    if user.id == interlocutor_id:
        raise HTTPException(404)

    chat_id = await services.message_manager.get_dialog_id_by_user_id(
        db_session, user.id, interlocutor_id
    )
    if not chat_id:
        chat_id = await services.message_manager.create_new_chat_with_members(
            db_session, user.id, interlocutor_id
        )

    return JSONResponse({"chat_id": chat_id})


@router.get("/my/getall")
async def get_all_chats_with_offset_limit(
    offset: int = 0,
    limit: int = 10,
    db_session: AsyncSession = Depends(get_session),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
) -> JSONResponse:
    """
    Получаем все чаты текущего пользователя
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    chats_ids = await services.message_manager.get_all_user_chats_ids_by_user_id(
        db_session, user.id, offset, limit
    )
    
    if not chats_ids:
        raise HTTPException(404)
    
    return JSONResponse({"chats_ids": chats_ids})


@router.get("/my/getmessages")
async def get_all_messages_with_offset_limit(
    chat_id: int,
    offset: int = 0,
    limit: int = 10,
    db_session: AsyncSession = Depends(get_session),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    messages = await services.message_manager.get_messages_by_chat_id_user_id(
        db_session, chat_id, user.id, offset, limit
    )
    
    if not messages:
        raise HTTPException(404)
    
    return messages


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
