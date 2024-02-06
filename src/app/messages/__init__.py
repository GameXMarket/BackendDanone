from fastapi import APIRouter

from .routers import router_message_carcass, ws_router_message_carcass


message_routers = APIRouter(tags=["chat"])
message_routers.include_router(router_message_carcass, prefix="/chat")
message_routers.include_router(ws_router_message_carcass, prefix="/ws/chat")
