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


@router.get("/my/getall")
async def get_all_my_sales(
    offset: int = 0,
    limit: int = 10,
    db_session: AsyncSession = Depends(get_session),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
):
    """
    Получение всех продаж (продавец)
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    sells = await purchase_manager.get_all_sells(offset, limit, user.id, db_session)
    if not sells:
        raise HTTPException(404)
    
    return sells


@router.get("/my/byoffer")
async def get_sales_by_offer(
    offer_id: int,
    offset: int = 0,
    limit: int = 10,
    db_session: AsyncSession = Depends(get_session),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
):
    """
    Получение всех продаж по офферу  (продавец)
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    sells = await purchase_manager.get_all_sells_by_offer(offset, limit, offer_id, user.id, db_session)
    if not sells:
        raise HTTPException(404)
    
    return sells


@router.post("/my/confirmation")
async def create_confirmation_request(
    purchase_id: int,
    db_session: AsyncSession = Depends(get_session),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
):
    """
    Подтверждение выполнения продажи (продавец)
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    purchase = await purchase_manager.create_confirmation_request(db_session, purchase_id, user.id)
    return purchase


