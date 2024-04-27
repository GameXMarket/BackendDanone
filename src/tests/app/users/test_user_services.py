from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import async_session

from app.users.services.users_base import *
from app.users.services.users_online import *
from app.users.models import User
from app.users.schemas.users_online import *
from app.users.schemas.users import *


test_password = "12341234"
test_email = "kropkaalutiytest@gmail.com"
test_username = "kropkaakirpich"


second_test_password = "12341234"
second_test_email = "kropakasecond@gmail.com"
second_test_username = "kropkaasecond"


async def test_user_create():
    async with async_session() as session:
        user: User = await create_user(
            db_session=session,
            obj_in=UserSignUp(
                password=test_password, email=test_email, username=test_username
            ),
        )
        assert user.username == test_username
        assert user.email == test_email


async def test_user_get_by_id():
    async with async_session() as session:
        user: User = await get_by_id(db_session=session, id=3)
        assert user.username == test_username
        assert user.email == test_email


async def test_user_get_by_email():
    async with async_session() as session:
        user: User = await get_by_email(db_session=session, email=test_email)
        assert user.username == test_username
        assert user.email == test_email


async def test_user_get_by_username():
    async with async_session() as session:
        user: User = await get_by_username(db_session=session, username=test_username)
        assert user.username == test_username
        assert user.email == test_email


async def test_update_user():
    async with async_session() as session:
        user: User = await get_by_username(db_session=session, username=test_username)
        new_user = await update_user(
            db_session=session,
            db_obj=user,
            obj_in=UserInDB(
                email=second_test_email,
                username=second_test_username,
                id=user.id,
                is_verified=user.is_verified,
                role_id=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at,
                hashed_password=user.hashed_password,
            ),
        )
        assert new_user.username == second_test_username
        assert new_user.email == second_test_email


async def test_user_auth():
    async with async_session() as session:
        user: User = await authenticate(
            db_session=session, email=second_test_email, password=second_test_password
        )
        assert user.username == second_test_username
        assert user.email == second_test_email


async def test_user_active():
    async with async_session() as session:
        user: User = await get_by_id(db_session=session, id=1)
        un_verif: bool = is_active(user=user)

        user.is_verified = True

        verif: bool = is_active(user=user)
        assert un_verif == False
        assert verif == True


async def test_user_get_role_id():
    async with async_session() as session:
        user: User = await get_by_id(db_session=session, id=1)
        role_id = get_role_id(user=user)
        assert role_id == 0


async def test_delete_user():
    async with async_session() as session:
        await delete_user(db_session=session, email=second_test_email)
