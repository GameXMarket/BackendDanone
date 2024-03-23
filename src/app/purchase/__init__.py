from fastapi import APIRouter

from .routers import router_purchase


purchase_routers = APIRouter(tags=["purchase"])
purchase_routers.include_router(router_purchase, prefix="/purchase")
