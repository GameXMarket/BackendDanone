import logging

from fastapi import Depends, APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from core import settings as conf
from core.database import get_session
from .. import models, schemas, services


logger = logging.getLogger("uvicorn")
router = APIRouter()


@router.get(
    path="/gettall"
)
async def get_mini_with_offset_limit(
    offset: int = 0,
    limit: int = 1,
):
    """ 
    Получаем список всех root категорий, без наследников
    """
    
    ...


@router.get(
    path="/{category_id}"
)
async def get_by_id(category_id: int, db_session: AsyncSession = Depends(get_session)):
    """
    Получаем по id категорию (root/child/subchild/и т.д.) и всех её наследников 
    <pre>
    root --+---> child1                    <br>
           +---> child2 --+--> subchild1   <br>
           |              +--> subchild2   <br>
           +---> child3                    <br>
    </pre>
    """
    category: models.Category = await services.get_by_id(db_session, id=category_id, options=(selectinload, models.Category.childrens))
    
    ...


@router.post(
    path="/"
)
async def create_category():
    """
    Создаёт новую root-категорию (игру, платформу и т.д.)
    <pre>
    root --+---> child1                    <br>
           +---> child2 --+--> subchild1   <br>
           |              +--> subchild2   <br>
           +---> child3                    <br>
    </pre>
    """
    
    ...


@router.post(
    path="/{category_id}"
)
async def create_subcategory(category_id: int, new_category: schemas.SubcategoryCreate):
    """
    Создаёт новую подкатегорию (валюта, прокачка и тд)
    <pre>
    root --+---> child1                    <br>
           +---> child2 --+--> subchild1   <br>
           |              +--> subchild2   <br>
           +---> child3                    <br>
    </pre>
    """
    
    ...


@router.put(
    path="/{category_id}"
)
async def update_category(category_id: int, new_category: schemas.CategoryUpdate):
    
    ...


@router.delete(
    path="/{category_id}"
)
async def delete_category(category_id: int):
    
    ...


