from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import *
from services import users as UserService
from core.database import get_session


router = APIRouter()
# TODO Прописать модели response и другое


@router.post(path="/", responses={200: {"model": BaseUser}, 409: {"model": UserError}})
async def sign_up(
    request: Request, data: UserSignUp, db_session: AsyncSession = Depends(get_session)
):
    if await UserService.get_by_email(db_session, email=data.email):
        raise HTTPException(
            status_code=409,
            detail="The user with this email already exists in the system.",
        )
    if await UserService.get_by_username(db_session, username=data.username):
        raise HTTPException(
            status_code=409,
            detail="The user with this username already exists in the system.",
        )

    user = await UserService.create_(db_session, obj_in=data)
    # TODO send email verif here...
    return BaseUser(**user.to_dict())


@router.get(path="/{identifier}")
async def get_user(
    request: Request, identifier: str, db_session: AsyncSession = Depends(get_session)
):

    ...


@router.put(path="/")
async def update_user(db_session: AsyncSession = Depends(get_session)):

    ...


@router.delete(path="/{username}")
async def remove_user(
    request: Request, username: str, db_session: AsyncSession = Depends(get_session)
):

    ...
