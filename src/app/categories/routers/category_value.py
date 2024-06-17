import logging

from fastapi import Query, Depends, APIRouter, Request, HTTPException, status
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


""" 
Пример работы с cte sqlalchemy


WITH RECURSIVE included_parts(sub_part, part, quantity) AS (
    SELECT sub_part, part, quantity FROM parts WHERE part = 'our_product'
  UNION ALL
    SELECT p.sub_part, p.part, p.quantity
    FROM included_parts pr, parts p
    WHERE p.part = pr.sub_part
  )
SELECT sub_part, SUM(quantity) as total_quantity
FROM included_parts
GROUP BY sub_part



parts = Table('parts', metadata,
    Column('part', String),
    Column('sub_part', String),
    Column('quantity', Integer),
)

included_parts = select([
                    parts.c.sub_part,
                    parts.c.part,
                    parts.c.quantity]).\
                    where(parts.c.part=='our part').\
                    cte(recursive=True)


incl_alias = included_parts.alias()
parts_alias = parts.alias()
included_parts = included_parts.union_all(
    select([
        parts_alias.c.sub_part,
        parts_alias.c.part,
        parts_alias.c.quantity
    ]).
        where(parts_alias.c.part==incl_alias.c.sub_part)
)

statement = select([
            included_parts.c.sub_part,
            func.sum(included_parts.c.quantity).
              label('total_quantity')
        ]).\
        group_by(included_parts.c.sub_part)

"""


@router.get(path="/getassociated")
async def get_associated_values(
    root_value_ids: list[int] = Query(default=[3, 4, 5]),
    db_session: AsyncSession = Depends(get_session),
):
    """
    root_value_ids - id value, по которым будет поиск всех связанных value
    """
    values = await services.categories_values.get_associated_by_id(
        db_session, root_value_ids
    )

    if not values:
        raise HTTPException(status_code=404)

    return values


@router.get(path="/getmany")
async def get_many_by_ids(
    value_ids: list[int] = Query(default=[1, 2]),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Возвращает список пар [value:carcass, ...]
    """
    if not isinstance(value_ids, list):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    values = await services.categories_values.get_many_by_ids(
        db_session,
        ids=value_ids,
        options=[(selectinload, models.CategoryValue.carcass)],
        lazy_load_v="carcass"
    )

    if not values:
        raise HTTPException(status_code=404)

    return values


@router.post(path="/{carcass_id}")
async def create_value(
    carcass_id: int,
    value: schemas.ValueCreate,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Создаёт value у каркасса
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    if not user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    value = await services.categories_values.create_value(
        db_session, author_id=user.id, carcass_id=carcass_id, value=value
    )

    return value


@router.put(path="/{value_id}")
async def update_value(
    value_id: int,
    new_value: schemas.ValueUpdate,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Обновляет value по его id
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    if not user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    value = await services.categories_values.get_by_id(db_session, id=value_id)

    if not value:
        raise HTTPException(status_code=404)

    new_value = await services.categories_values.update_value(
        db_session, author_id=user.id, db_obj=value, value=new_value
    )

    return new_value


@router.delete(path="/{value_id}")
async def delete_value(
    value_id: int,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        base_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Удаляет value по его id
    """
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    if not user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    deleted_value = await services.categories_values.delete_value(
        db_session, value_id=value_id
    )

    if not deleted_value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return deleted_value


@router.get(path="/test_is_on_one_branch")
async def test_categories_on_one_branch(
    value_ids: list[int] = Query(default=[1, 2]),
    db_session: AsyncSession = Depends(get_session),
):
    if not isinstance(value_ids, list):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    return await services.categories_values.is_on_one_branch(db_session=db_session, ids=value_ids)
