import logging

from fastapi import Depends, APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.depends import depends as deps
from core.database import get_session
from app.tokens import schemas as schemas_t
from .. import models, schemas, services


logger = logging.getLogger("uvicorn")
router = APIRouter()
base_session = deps.UserSession()
purchase_manager = services.PurchaseManager()


@router.get("/my")
async def get_purchase(
    purchase_id: int,
    db_session: AsyncSession = Depends(get_session),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    ...


@router.get("/my/getall")
async def get_all_purchases(
    db_session: AsyncSession = Depends(get_session),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    ...


@router.post("/my/create")
async def create_purchase(
    offer_id: int,
    db_session: AsyncSession = Depends(get_session),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    ...
