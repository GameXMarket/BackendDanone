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


@router.get(path="/gettall")
async def get_root_with_offset_limit(
    offset: int = 0,
    limit: int = 1,
    db_session: AsyncSession = Depends(get_session),
):
    """
    Метод не готов <br>
    Получаем список всех root категорий, без наследников
    """
    categories = await services.get_all_with_offset_limit(
        db_session, offset=abs(offset), limit=abs(limit)
    )

    return categories


@router.get(path="/{category_id}")
async def get_by_id(category_id: int, db_session: AsyncSession = Depends(get_session)):
    """
    Получаем по id категорию (root/child/subchild/и т.д.) и всех её наследников в одном поколении
    <pre>
    root --+---> child1                    <br>
           +---> child2 --+--> subchild1   <br>
           |              +--> subchild2   <br>
           +---> child3                    <br>
    </pre>
    """
    category: models.Category = await services.get_by_id(
        db_session, id=category_id, options=(selectinload, models.Category.childrens)
    )

    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return category.to_json()


@router.post(path="/")
async def create_category(
    new_category: schemas.CategoryCreate,
    session: deps.UserSession = Depends(base_session),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Создаёт новую root-категорию (игру, платформу и т.д.) <br>
    Требуются права администратора
    <pre>
    root --+---> child1                    <br>
           +---> child2 --+--> subchild1   <br>
           |              +--> subchild2   <br>
           +---> child3                    <br>
    </pre>
    """
    user = await session.get_current_active_user()

    if not user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    category = await services.create_category(
        db_session, author_id=user.id, obj_in=new_category
    )

    return category.to_json()


@router.post(path="/{category_id}")
async def create_subcategory(
    category_id: int,
    new_category: schemas.SubcategoryCreate,
    session: deps.UserSession = Depends(base_session),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Создаёт новую подкатегорию (валюта, прокачка и тд) <br>
    Требуются права администратора
    <pre>
    root --+---> child1                    <br>
           +---> child2 --+--> subchild1   <br>
           |              +--> subchild2   <br>
           +---> child3                    <br>
    </pre>
    """
    user = await session.get_current_active_user()

    if not user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    parrent = await services.get_by_id(db_session, id=category_id)

    if not parrent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    category = await services.create_category(
        db_session, author_id=user.id, obj_in=new_category, parrent_id=category_id
    )

    return category.to_json()


@router.put(path="/{category_id}")
async def update_category(
    category_id: int,
    new_category: schemas.CategoryUpdate,
    session: deps.UserSession = Depends(base_session),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Обновляет категорию по её id <br>
    Требуются права администратора
    """

    user = await session.get_current_active_user()

    if not user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    old_category = await services.get_by_id(db_session, id=category_id)

    if not old_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    new_category = await services.update_category(
        db_session, author_id=user.id, db_obj=old_category, obj_in=new_category
    )

    return new_category.to_json()


@router.delete(path="/{category_id}")
async def delete_category(
    category_id: int,
    session: deps.UserSession = Depends(base_session),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Удаляет категорию по её id <br>
    Требуются права администратора
    """

    user = await session.get_current_active_user()

    if not user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    deleted_category = await services.delete_category(
        db_session, category_id=category_id
    )

    if not deleted_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return deleted_category.to_json()
