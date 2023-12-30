from fastapi import APIRouter

from .routers import router_my, router_public


offers_routers = APIRouter(prefix="/offers", tags=["offers"])

offers_routers.include_router(router_public)
offers_routers.include_router(router_my)
