from fastapi import APIRouter

from .routers import user_router, ws_online_user_router, notification_user_router


users_routers = APIRouter(tags=["users"])
users_routers.include_router(user_router, prefix="/users")
users_routers.include_router(ws_online_user_router, prefix="/ws/users")
users_routers.include_router(notification_user_router, prefix="/users")