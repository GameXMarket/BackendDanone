import logging
from typing import Literal

import fastapi
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
    by_last_udpate: bool = False,
    search_query: str = None,
    is_reviewed: bool = None,
    statuses: list[
        Literal["process", "review", "completed", "dispute", "refund"]
    ] = fastapi.Query(
        default=["process", "review", "completed", "dispute", "refund"], alias="status"
    ),
    db_session: AsyncSession = Depends(get_session),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
):
    """
    Получаем список всех покупок <br>
     * by_last_udpate - Сортировка по последнему обновлению или по созданию (по умолчанию по созданию)
     * search_query - Поиск по названию
     * is_reviewed - Поиск по наличию отзыва
     * statuses - Поиск по статусам
      # Предварительные статусы, жду момента, когда распишут всё
      * process - Покупка только создалась, деньги зарезервировались, ждём подтверждения продавцом о выполнении
      * review - Продавец подтвердил выполнение, ждём подтверждения пользователя
      * completed - Покупатель подтвердил выполнение (или заказ был с автовыдачей или поддержка решила, что заказ готов)
      * dispute - Покупатель открыл спор по заказу, ждём решение администрации
      * refund - Деньги возвращаются покупателю (по желанию продавца или поддержки)
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    purchases = await purchase_manager.get_all_purchases(
        db_session=db_session,
        buyer_id=user.id,
        offset=offset,
        limit=limit,
        by_last_udpate=by_last_udpate,
        search_query=search_query,
        is_reviewed=is_reviewed,
        statuses=statuses,
    )
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

    purchase = await purchase_manager.create_purchase(
        db_session, user.id, new_purchase_data
    )
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


@router.post("/me/createreview")
async def create_review(
    review_data: schemas.ReviewCreate,
    db_session: AsyncSession = Depends(get_session),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    review = await purchase_manager.create_review(user.id, review_data, db_session)
    if not review:
        raise HTTPException(404)
    
    return review
