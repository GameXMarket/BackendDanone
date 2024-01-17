import logging

from fastapi import Depends, APIRouter, WebSocket, WebSocketDisconnect, WebSocketException, status

from core import depends as deps
from app.users.services import ConnectionContext, OnlineConnectionManager


logger = logging.getLogger("uvicorn")
router = APIRouter()
base_manager = OnlineConnectionManager()


@router.websocket("/online/")
async def lazy_users_online(ws_context_data: tuple[ConnectionContext, OnlineConnectionManager] = Depends(base_manager)):
    conn_context, conn_manager = ws_context_data
    await conn_manager.connect(conn_context)
    
    try:
        await conn_manager.start_listening(conn_context)
    except BaseException: # WebSocketDisconnect
        await conn_manager.disconnect(conn_context)
