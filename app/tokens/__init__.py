from fastapi import APIRouter

from .routers import auth_router


tokens_routers = APIRouter(tags=["auth"])
tokens_routers.include_router(auth_router)
