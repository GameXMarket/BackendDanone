import logging

from fastapi import Depends, APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from core import settings as conf
from core.depends import depends as deps
from core.database import get_session
from .. import models, schemas, services


logger = logging.getLogger("uvicorn")
router = APIRouter()
base_session = deps.UserSession()


@router.post(
    path="/{carcass_id}"
)
async def create_value(carcass_id: int, value: schemas.ValueCreate, session: deps.UserSession = Depends(base_session), db_session: AsyncSession = Depends(get_session)):
    """
    Создаёт value у каркасса
    """
    user = await session.get_current_active_user()

    if not user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    value = await services.categories_values.create_value(db_session, author_id=user.id, carcass_id=carcass_id, value=value)
    
    return value


@router.put(
    path="/{value_id}"
)
async def update_value(value_id: int, value: schemas.ValueUpdate, session: deps.UserSession = Depends(base_session), db_session: AsyncSession = Depends(get_session)):
    """
    Обновляет value по его id
    """
    user = await session.get_current_active_user()

    if not user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    value = await services.categories_values.get_by_id(db_session, id=value_id)
    
    if not value:
        raise HTTPException(status_code=404)
    
    new_value = await services.categories_values.update_value(db_session, author_id=user.id, db_obj=value, value=value)
    
    return new_value



@router.delete(
    path="/{value_id}"
)
async def delete_value(value_id: int, session: deps.UserSession = Depends(base_session), db_session: AsyncSession = Depends(get_session)):
    """
    Удаляет value по его id
    """
    user = await session.get_current_active_user()

    if not user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    deleted_value = await services.categories_values.delete_value(db_session, value_id=value_id)

    if not deleted_value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return deleted_value
