from fastapi import APIRouter

from .routers import router_message_carcass


message_routers = APIRouter(prefix="/chat", tags=["chat"])
message_routers.include_router(router_message_carcass)
