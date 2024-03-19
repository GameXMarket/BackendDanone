import logging

from fastapi import Depends, APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from core import settings as conf
from core.depends import depends as deps
from core.database import get_session
from .. import models, schemas, services
from app.tokens import schemas as schemas_t

logger = logging.getLogger("uvicorn")
router = APIRouter()
base_session = deps.UserSession()


@router.get(path="/gettall/")
async def get_root_with_offset_limit(
        offset: int = 0,
        limit: int = 1,
        db_session: AsyncSession = Depends(get_session),
):
    """
    Получаем список всех root каркасов, без наследников
    """
    categories_rows = await services.categories_carcass.get_all_with_offset_limit(
        db_session, offset=abs(offset), limit=abs(limit), options=[(selectinload, models.CategoryCarcass.values)]
    )

    return [row for row in categories_rows]


@router.get(path="/{category_id}")
async def get_by_id(category_id: int, db_session: AsyncSession = Depends(get_session)):
    """
    Получаем по id каркасс (root/child/subchild/и т.д.) и всех его наследников в одном поколении
    <pre>
    root --+---> child1
           +---> child2 --+--> subchild1
           |              +--> subchild2
           +---> child3
    </pre>
    """
    category: models.CategoryCarcass = await services.categories_carcass.get_by_id(
        db_session, id=category_id,
        options=([(selectinload, models.CategoryCarcass.values), (selectinload, models.CategoryCarcass.values)])
    )

    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return category


@router.post(path="/")
async def create_category_carcass(
        new_category: schemas.CategoryCarcassCreate,
        current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(base_session),
        db_session: AsyncSession = Depends(get_session),
):
    """
    Создаёт новый каркасс (игру, платформу и т.д.) <br>
    Требуются права администратора
    root-каркасс должен быть только один.
    <pre>
    root --+---> child1
           +---> child2 --+--> subchild1
           |              +--> subchild2
           +---> child3
    </pre>
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    if not user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    category = await services.categories_carcass.create_category(
        db_session, author_id=user.id, obj_in=new_category
    )

    return category


@router.put(path="/{category_id}")
async def update_category_carcass(
        category_id: int,
        new_category: schemas.CategoryCarcassUpdate,
        current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(base_session),
        db_session: AsyncSession = Depends(get_session),
):
    """
    Обновляет каркасс по его id <br>
    Требуются права администратора
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    if not user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    old_category = await services.categories_carcass.get_by_id(db_session, id=category_id)

    if not old_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    updated_category = await services.categories_carcass.update_category(
        db_session, author_id=user.id, db_obj=old_category, obj_in=new_category
    )

    return updated_category


@router.delete(path="/{category_id}")
async def delete_category_carcass(
        category_id: int,
        current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(base_session),
        db_session: AsyncSession = Depends(get_session),
):
    """
    Удаляет каркасс по его id <br>
    Требуются права администратора
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    if not user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    deleted_category = await services.categories_carcass.delete_category(
        db_session, category_id=category_id
    )

    if not deleted_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return deleted_category
