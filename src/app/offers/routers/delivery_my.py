import logging

from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from app.users import models as models_u
from app.tokens import schemas as schemas_t
from core.depends import depends as deps
from .. import models as models_f
from .. import services as services_f
from .. import schemas as schemas_f

logger = logging.getLogger("uvicorn")
router = APIRouter()
base_session = deps.UserSession()


@router.get(
    "/my/getall"
)
async def get_all_by_offer_id(
        offer_id: int,
        offset: int = 0,
        limit: int = 10,
        current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
            base_session
        ),
        db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user: models_u.User = await user_context.get_current_active_user(
        db_session, token_data
    )
    if not await services_f.get_by_user_id_offer_id(db_session, user.id, offer_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    deliveries = await services_f.get_deliveries_by_offer_id(
        db_session=db_session, offer_id=offer_id, limit=limit, offset=offset
    )
    
    if not deliveries:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return deliveries


@router.get(
    path="/my"
)
async def get_delivery_by_id(
        delivery_id: int,
        current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
            base_session
        ),
        db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user: models_u.User = await user_context.get_current_active_user(
        db_session, token_data
    )
    delivery = await services_f.get_delivery_by_id(db_session, delivery_id=delivery_id)
    is_user_delivery = await services_f.is_user_delivery(db_session, user_id=user.id, delivery=delivery)

    if not delivery or not is_user_delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return delivery


@router.post(
    path="/my/", responses=deps.build_response(deps.UserSession.get_current_active_user)
)
async def create_delivery(
        deliveries: list[schemas_f.Delivery],
        current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
            base_session
        ),
        db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user: models_u.User = await user_context.get_current_active_user(
        db_session, token_data
    )
    
    created_deliveries = []
    for delivery in deliveries:
        offer = await services_f.get_raw_offer_by_user_id(db_session, user.id, delivery.offer_id)
        if not offer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        elif not offer.is_autogive_enabled:
            raise HTTPException(403, detail="Offer does not support delivery")
        
        created_delivery: models_f.Delivery = await services_f.create_delivery(
            db_session, obj_in=delivery
        )
        created_deliveries.append(created_delivery)
    
    return created_deliveries


@router.put(
    path="/my/{delivery_id}/",
    responses={
        **deps.build_response(deps.UserSession.get_current_active_user),
    },
)
async def update_delivery(
        delivery_id: int,
        delivery_in: schemas_f.Delivery,
        current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
            base_session
        ),
        db_session: AsyncSession = Depends(get_session),
):
    delivery_db = await services_f.get_delivery_by_id(db_session, delivery_id)
    token_data, user_context = current_session
    user: models_u.User = await user_context.get_current_active_user(
        db_session, token_data
    )
    is_user_delivery = await services_f.is_user_delivery(db_session, user_id=user.id, delivery=delivery_db)

    if not delivery_db or not is_user_delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    new_delivery = await services_f.update_delivery(
        db_session, db_obj=delivery_db, obj_in=delivery_in
    )

    return new_delivery


@router.delete(
    path="/my/{delivery_id}/",
    responses={
        **deps.build_response(deps.UserSession.get_current_active_user),
    },
)
async def delete_delivery(
        delivery_id: int,
        current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
            base_session
        ),
        db_session: AsyncSession = Depends(get_session),
):
    delivery_db = await services_f.get_delivery_by_id(db_session, delivery_id)
    token_data, user_context = current_session
    user: models_u.User = await user_context.get_current_active_user(
        db_session, token_data
    )
    is_user_delivery = await services_f.is_user_delivery(db_session, user_id=user.id, delivery=delivery_db)

    if not delivery_db or not is_user_delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    deleted_delivery = await services_f.delete_delivery(
        db_session, delivery_id=delivery_id
    )

    if not deleted_delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return deleted_delivery
