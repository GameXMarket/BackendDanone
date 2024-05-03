import logging
from typing import Literal

import fastapi
from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .. import models as models_f
from .. import schemas as schemas_f
from .. import services as services_f
from core.database import get_session
from core.depends import depends as deps
from app.users import models as models_u
from app.tokens import schemas as schemas_t
from app.attachment.services import category_value_attachment_manager


logger = logging.getLogger("uvicorn")
router = APIRouter()
base_session = deps.UserSession()


@router.post(
    path="/my/", responses=deps.build_response(deps.UserSession.get_current_active_user)
)
async def create_offfer(
    offer: schemas_f.CreateOffer,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Создаётся новый оффер у авторизованного пользователя
    """
    token_data, user_context = current_session
    user: models_u.User = await user_context.get_current_active_user(
        db_session, token_data
    )
    offer: models_f.Offer = await services_f.create_offer(
        db_session, user_id=user.id, obj_in=offer
    )

    return offer


@router.get(
    path="/my/getall/",
    responses={
        **{200: {"model": list[schemas_f.OfferMini]}},
        **deps.build_response(deps.UserSession.get_current_active_user),
    },
)
async def get_mini_with_offset_limit(
    offset: int = 0,
    limit: int = 10,
    search_query: str = None,
    is_descending: bool = None,
    statuses: list[Literal["active", "hidden", "deleted"]] = fastapi.Query(default=["active", "hidden", "deleted"], alias="status"),
    category_value_ids: list[int] = fastapi.Query(default=None, examples=["[1, 2]"]),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Получает мини офферы авторизованного пользователя, требуется два паметра: offset, limit<br>
    &nbsp;- если offset == 10, то первые 10 строк будут пропущены, и выборка начнется с 11-й строки<br>
    &nbsp;- если limit == 20, то запрос вернёт только первые 20 строк результата

    Соритрует результат по дате создания от старых к новым (id могут идти не по порядку)
    """
    token_data, user_context = current_session
    user: models_u.User = await user_context.get_current_active_user(
        db_session, token_data
    )
    offers = await services_f.get_mini_by_user_id_offset_limit(
        db_session,
        user_id=user.id,
        offset=abs(offset),
        limit=abs(limit),
        search_query=search_query,
        is_descending=is_descending,
        category_value_ids=category_value_ids,
        statuses=statuses
    )

    return offers


@router.get(path="/my/bycategories")
async def get_root_categories_count_with_offset_limit(
    offset: int = 0,
    limit: int = 10,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Возвращает ваши категории + кол-во лотов
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    categories = await services_f.get_root_categories_count_with_offset_limit(
        db_session, user.id, offset, limit
    )
    if not categories:
        raise HTTPException(404)

    return categories


@router.get(path="/my/bycarcassid")
async def get_offers_by_category(
    carcass_id: int,
    offset: int = 0,
    limit: int = 10,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Возвращает ваши категории + кол-во лотов
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    offers = await services_f.get_offers_by_carcass_id(
        db_session, user.id, carcass_id, offset, limit
    )
    if not offers:
        raise HTTPException(404)

    return offers


@router.get(path="/my/byvalueid")
async def get_offers_by_category(
    value_id: int,
    offset: int = 0,
    limit: int = 10,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Возвращает ваши категории + кол-во лотов
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    offers = await services_f.get_offers_by_value_id(
        db_session, user.id, value_id, offset, limit
    )
    if not offers:
        raise HTTPException(404)

    value_file = await category_value_attachment_manager.get_only_files(db_session=db_session, category_value_id=value_id)

    return {"offers": offers, "files": value_file}


@router.patch(path="/my/delivery")
async def change_offer_delivery_status(
    enabled: bool,
    offer_id: int,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
    db_session: AsyncSession = Depends(get_session),

):
    """
    Метод включает и отключает delivery для оффера, после отключения количество устанавливается на 0
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    offer = await services_f.offers_my.get_raw_offer_by_user_id(db_session, user.id, offer_id)
    if not offer:
        raise HTTPException(404)
    
    elif offer.is_autogive_enabled is None:
        raise HTTPException(403, "Offer does not support delivery")
    
    new_offer = await services_f.offers_my.update_offer(db_session, db_obj=offer, obj_in={"is_autogive_enabled": enabled})
    
    return new_offer


@router.patch(path="/my/status_change")
async def change_offer_status(
    status: Literal["active", "hidden"],
    offer_id: int,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    "Метод меняет видимоть оффера для отсальных людей"
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    offer = await services_f.offers_my.get_raw_offer_by_user_id(db_session, user.id, offer_id)
    if not offer:
        raise HTTPException(404)

    new_offer = await services_f.offers_my.update_offer(db_session, db_obj=offer, obj_in={"status": status})
    
    return new_offer


@router.get(
    path="/my/{offer_id}",
)
async def get_by_id(
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

    offer = await services_f.get_by_user_id_offer_id(
        db_session, user_id=user.id, id=offer_id
    )

    if not offer:
        raise HTTPException(404)

    return offer


@router.put(
    path="/my/{offer_id}",
    responses={
        **{404: {"model": schemas_f.OfferError}},
        **deps.build_response(deps.UserSession.get_current_active_user),
    },
)
async def update_offer(
    offer_id: int,
    offer_in: schemas_f.CreateOffer,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Обновляется оффер у авторизованного пользователя по его id
    """
    token_data, user_context = current_session
    user: models_u.User = await user_context.get_current_active_user(
        db_session, token_data
    )
    offer_db = await services_f.get_raw_offer_by_user_id(
        db_session, user_id=user.id, offer_id=offer_id
    )

    if not offer_db:
        raise HTTPException(404)

    new_offer = await services_f.update_offer(
        db_session, db_obj=offer_db, obj_in=offer_in
    )

    return new_offer


@router.delete(
    path="/my/{offer_id}",
    responses={
        **{404: {"model": schemas_f.OfferError}},
        **deps.build_response(deps.UserSession.get_current_active_user),
    },
)
async def delete_offer(
    offer_id: int,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Удаляется оффер у авторизованного пользователя по его id
    """
    token_data, user_context = current_session
    user: models_u.User = await user_context.get_current_active_user(
        db_session, token_data
    )
    deleted_offer = await services_f.delete_offer(
        db_session, user_id=user.id, offer_id=offer_id
    )

    if not deleted_offer:
        raise HTTPException(404)

    return deleted_offer
