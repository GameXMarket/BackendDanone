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

    purchase = await purchase_manager.get_purchase(db_session, purchase_id, user.id)
    if not purchase:
        raise HTTPException(404)
    
    return purchase


@router.get("/my/getall")
async def get_all_purchases(
    offset: int = 0,
    limit: int = 10,
    db_session: AsyncSession = Depends(get_session),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    purchases = await purchase_manager.get_all_purchases(db_session, user.id, offset, limit)
    if not purchases:
        raise HTTPException(404)
    
    return purchases


@router.post("/my/create")
async def create_purchase(
    new_purchase_data: schemas.PurchaseCreate,
    db_session: AsyncSession = Depends(get_session),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    # TODO доделать логику того, что один оффер нельзя купить дважды (пока не будет выполнен предыдущий)
    purchase = await purchase_manager.create_purchase(db_session, user.id, new_purchase_data)    
    if not purchase:
        raise HTTPException(404)
    
    return purchase


@router.post("/my/complete/")
async def confirm_purchase(
    state: bool,
    purchase_id: int,
    db_session: AsyncSession = Depends(get_session),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
):
    """
    Создаёт спор при state = False, при state = True подтверждает выполнение
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    purchase = await purchase_manager.change_confirmation_request_status(
        db_session=db_session,
        purchase_id=purchase_id,
        buyer_id=user.id,
        purchase_completed=state,
    )
    if not purchase:
        raise HTTPException(404)
    
    return purchase