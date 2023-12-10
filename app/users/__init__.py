from fastapi import APIRouter

from .routers import user_router


users_routers = APIRouter(tags=["users"])
users_routers.include_router(user_router)
