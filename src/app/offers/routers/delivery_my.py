from fastapi import Depends, APIRouter, HTTPException, status
import logging
from core.depends import depends as deps
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_session
from app.users import models as models_u
from app.tokens import schemas as schemas_t
from .. import models as models_f
from .. import services as services_f
from .. import schemas as schemas_f

logger = logging.getLogger("uvicorn")
router = APIRouter()
base_session = deps.UserSession()


@router.post(
    path="/my/", responses=deps.build_response(deps.UserSession.get_current_active_user)
)
async def create_delivery(
        delivery: schemas_f.Delivery,
        current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
            base_session
        ),
        db_session: AsyncSession = Depends(get_session),
):
    delivery: models_f.delivery = await services_f.create_delivery(
        db_session, obj_in=delivery
    )
    return delivery


@router.put(
    path="/my/{delivery_id}/",
    responses={
        **deps.build_response(deps.UserSession.get_current_active_user),
    },
)
async def update_offer(
        delivery_id: int,
        delivery_in: schemas_f.Delivery,
        current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
            base_session
        ),
        db_session: AsyncSession = Depends(get_session),
):
    delivery_db = await services_f.get_delivery_by_id(db_session, delivery_id)

    if not delivery_db:
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

    deleted_delivery = await services_f.delete_delivery(
        db_session, delivery_id=delivery_id
    )

    if not deleted_delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return deleted_delivery


