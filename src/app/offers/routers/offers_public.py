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

logger = logging.getLogger("uvicorn")
router = APIRouter(responses={200: {"model": schemas_f.OfferPreDB}})


@router.get(
    "/get_offers_by_price_and_name",
    responses={
        200: {"model": schemas_f.OfferPreDB},
        404: {"model": schemas_f.OfferError}
    },
)
async def get_active_offers(
    search_query: str = None,
    category_values_ids: list[int] = Query(
        None, description="Список идентификаторов категорий"
    ),
    is_descending: bool = False,
    db_session: AsyncSession = Depends(get_session),
):
    offers = await services_f.get_offers_by_price_name_filter(
        db_session=db_session,
        is_descending=is_descending,
        search_query=search_query,
        category_values_ids=category_values_ids,
    )
    if not offers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return offers



@router.get(
    path="/getall/",
    responses={200: {"model": list[schemas_f.OfferMini]}},
)
async def test_get_mini_with_offset_limit(
        offset: int = 0,
        limit: int = 10,
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
    if category_value_ids and not isinstance(category_value_ids, list):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="example: [1,2]")

    offers = await services_f.get_mini_by_offset_limit(
        db_session,
        offset=abs(offset),
        limit=abs(limit),
        category_value_ids=category_value_ids,
    )

    return offers


@router.get(
    path="/{offer_id}/",
    responses={
        200: {"model": schemas_f.OfferPreDB},
        404: {"model": schemas_f.OfferError}
    },
)
async def get_by_id(offer_id: int, db_session: AsyncSession = Depends(get_session), ):
    offer = await services_f.get_by_offer_id(db_session, id=offer_id)

    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return offer
