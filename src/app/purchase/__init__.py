from fastapi import APIRouter

from .routers import router_purchase, router_sales


purchase_routers = APIRouter(tags=["purchase"])
purchase_routers.include_router(router_purchase, prefix="/purchase")

sales_routers = APIRouter(tags=["sales"])
sales_routers.include_router(router_sales, prefix="/sales")

purchase_logic_routers = APIRouter()
purchase_logic_routers.include_router(purchase_routers)
purchase_logic_routers.include_router(sales_routers)
