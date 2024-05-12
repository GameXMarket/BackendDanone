import logging
import json

import fastapi
from fastapi import Depends, APIRouter, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .. import models as models_f
from .. import schemas as schemas_f
from .. import services as services_f
from core import settings as conf
from core.database import get_session
from core.depends import depends as deps
from app.users import models as models_u
from app.tokens import schemas as schemas_t


logger = logging.getLogger("uvicorn")
router = APIRouter()
base_session = deps.UserSession()


@router.get(
    path="/getall/",
    responses={200: {"model": list[schemas_f.OfferMini]}},
)
async def test_get_mini_with_offset_limit(
    offset: int = 0,
    limit: int = 10,
    search_query: str = None,
    is_descending: bool = None,
    category_value_ids: list[int] = fastapi.Query(default=None, examples=["[1, 2]"]),
    db_session: AsyncSession = Depends(get_session),
):
    """
    <mark>ФУНКЦИЯ ДЛЯ ТЕСТОВ</mark><br>
    Получает мини офферы авторизованного пользователя, требуется два паметра: offset, limit<br>
    &nbsp;- если offset == 10, то первые 10 строк будут пропущены, и выборка начнется с 11-й строки<br>
    &nbsp;- если limit == 20, то запрос вернёт только первые 20 строк результата

    Соритрует результат по дате создания от старых к новым (id могут идти не по порядку)
    """

    offers = await services_f.get_mini_by_offset_limit(
        db_session,
        offset=abs(offset),
        limit=abs(limit),
        category_value_ids=category_value_ids,
        is_descending=is_descending,
        search_query=search_query,
    )

    return offers


@router.get(path="/withstatus")
async def get_with_purchase_data(
    offer_id: int,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user: models_u.User = await user_context.get_current_active_user(
        db_session, token_data
    )

    offer = await services_f.get_offer_by_id_with_purchase_data(
        db_session, offer_id=offer_id, buyer_id=user.id
    )
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return offer


@router.get(path="/{offer_id}/")
async def get_by_id(
    offer_id: int,
    db_session: AsyncSession = Depends(get_session),
):
    offer = await services_f.get_offer_by_id(db_session, id=offer_id)

    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return offer
