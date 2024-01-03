from fastapi import APIRouter

from .routers import router_category


category_routers = APIRouter(prefix="/categories", tags=["categories"])
category_routers.include_router(router_category)
