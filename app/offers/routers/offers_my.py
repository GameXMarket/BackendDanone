import logging

from fastapi import Depends, APIRouter, HTTPException, status
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


@router.post(
    path="/my/", responses=deps.build_response(deps.UserSession.get_current_active_user)
)
async def create_offfer(
    offer: schemas_f.CreateOffer,
    session: deps.UserSession = Depends(deps.UserSession()),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Создаётся новый оффер у авторизованного пользователя
    """
    user: models_u.User = await session.get_current_active_user()
    offer: models_f.Offer = await services_f.create_offer(
        db_session, user_id=user.id, obj_in=offer
    )

    return schemas_f.OfferPreDB(**offer.to_dict())


@router.get(
    path="/my/getall/",
    responses={
        **{200: {"model": list[schemas_f.OfferMini]}},
        **deps.build_response(deps.UserSession.get_current_active_user),
    },
)
async def get_mini_with_offset_limit(
    offset: int = 0,
    limit: int = 1,
    session: deps.UserSession = Depends(deps.UserSession()),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Получает мини офферы авторизованного пользователя, требуется два паметра: offset, limit<br>
    &nbsp;- если offset == 10, то первые 10 строк будут пропущены, и выборка начнется с 11-й строки<br>
    &nbsp;- если limit == 20, то запрос вернёт только первые 20 строк результата

    Соритрует результат по дате создания от старых к новым (id могут идти не по порядку)
    """
    user: models_u.User = await session.get_current_active_user()
    offers: list[
        schemas_f.OfferMini
    ] = await services_f.get_mini_by_user_id_offset_limit(
        db_session,
        user_id=user.id,
        offset=abs(offset),
        limit=abs(limit),
    )

    return offers


@router.get(
    path="/my/{offer_id}/",
    responses={
        **{200: {"model": schemas_f.OfferPreDB}, 404: {"model": schemas_f.OfferError}},
        **deps.build_response(deps.UserSession.get_current_active_user),
    },
)
async def get_by_id(
    offer_id: int,
    session: deps.UserSession = Depends(deps.UserSession()),
    db_session: AsyncSession = Depends(get_session),
):
    user: models_u.User = await session.get_current_active_user()

    offer = await services_f.get_by_user_id_offer_id(
        db_session, user_id=user.id, id=offer_id
    )

    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return schemas_f.OfferPreDB(**offer.to_dict())


@router.put(
    path="/my/{offer_id}/",
    responses={
        **{404: {"model": schemas_f.OfferError}},
        **deps.build_response(deps.UserSession.get_current_active_user),
    },
)
async def update_offer(
    offer_id: int,
    offer_in: schemas_f.CreateOffer,
    session: deps.UserSession = Depends(deps.UserSession()),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Обновляется оффер у авторизованного пользователя по его id
    """
    user: models_u.User = await session.get_current_active_user()
    offer_db = await services_f.get_by_user_id_offer_id(
        db_session, user_id=user.id, id=abs(offer_id)
    )

    if not offer_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    new_offer = await services_f.update_offer(
        db_session, db_obj=offer_db, obj_in=offer_in
    )

    return schemas_f.OfferPreDB(**new_offer.to_dict())


@router.delete(
    path="/my/{offer_id}/",
    responses={
        **{404: {"model": schemas_f.OfferError}},
        **deps.build_response(deps.UserSession.get_current_active_user),
    },
)
async def delete_offer(
    offer_id: int,
    session: deps.UserSession = Depends(deps.UserSession()),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Удаляется оффер у авторизованного пользователя по его id
    """
    user: models_u.User = await session.get_current_active_user()
    deleted_offer = await services_f.delete_offer(
        db_session, user_id=user.id, offer_id=abs(offer_id)
    )

    if not deleted_offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return schemas_f.OfferPreDB(**deleted_offer.to_dict())
