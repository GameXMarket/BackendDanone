from fastapi import APIRouter

from .routers import router_my, router_public
from .routers import router_delivery

offers_routers = APIRouter(prefix="/offers", tags=["offers"])
delivery_routers = APIRouter(prefix="/delivery", tags=["delivery"])

offers_routers.include_router(router_public)
offers_routers.include_router(router_my)
delivery_routers.include_router(router_delivery)
