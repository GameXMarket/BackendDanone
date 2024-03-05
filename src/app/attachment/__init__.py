from fastapi import APIRouter

from .routers import router as attachment_router


attachment_routers = APIRouter(tags=["attacment"])
attachment_routers.include_router(attachment_router, prefix="/attacment")
