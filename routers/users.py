from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dto.users import BaseUser as BaseUserDTO
from dto.users import UserNoSecret as UserNoSecretDTO
from dto.users import UserInDBase as UserInDBaseDTO
from dto.users import UserError as UserErrorDTO
from services import users as UsersService
from core.database import get_session


router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={
        200: {"model": UserNoSecretDTO},
    },
)


def __convert_db_user_to_no_secret(db_user: UserInDBaseDTO) -> UserNoSecretDTO:
    if not isinstance(db_user, UserInDBaseDTO):
        raise ValueError(f"Required {type(UserInDBaseDTO)}, received {type(db_user)}")
    return UserNoSecretDTO(**db_user.model_dump())


@router.post(
    path="/", responses={409: {"model": UserErrorDTO}}
)  # временный ендпоинт для отладки
async def temp_create_user(
    request: Request, data: BaseUserDTO, db_session: AsyncSession = Depends(get_session)
):
    result = await UsersService.create_user(data, db_session)

    if exception := result.get("error"):
        raise exception

    return __convert_db_user_to_no_secret(result.get("ok"))


@router.get(path="/{username}", responses={404: {"model": UserErrorDTO}})
async def get_user(
    request: Request, username: str, db_session: AsyncSession = Depends(get_session)
):
    result = await UsersService.get_user(username, db_session)

    if exception := result.get("error"):
        raise exception

    return __convert_db_user_to_no_secret(result.get("ok"))


@router.put(
    path="/{username}",
    responses={404: {"model": UserErrorDTO}, 409: {"model": UserErrorDTO}},
)
async def update_user(
    request: Request,
    username: str,
    data: BaseUserDTO,
    db_session: AsyncSession = Depends(get_session),
):
    result = await UsersService.update_user(username, data, db_session)

    if exception := result.get("error"):
        raise exception

    return __convert_db_user_to_no_secret(result.get("ok"))


@router.delete(path="/{username}", responses={404: {"model": UserErrorDTO}})
async def remove_user(
    request: Request, username: str, db_session: AsyncSession = Depends(get_session)
):
    result = await UsersService.remove_user(username, db_session)

    if exception := result.get("error"):
        raise exception

    return __convert_db_user_to_no_secret(result.get("ok"))
