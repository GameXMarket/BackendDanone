from fastapi import APIRouter

from .routers import router_category_carcass, router_category_value


category_routers = APIRouter(prefix="/categories", tags=["categories"])
category_routers.include_router(router_category_carcass, prefix="/carcass")
category_routers.include_router(router_category_value, prefix="/value")
