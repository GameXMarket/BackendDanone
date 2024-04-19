from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import create_new_token_set

from app.users.models import User
from app.users.schemas import UserSignUp
from app.users.services import create_user, update_user
from tests.conftest import async_session, clear_db


test_password = "12341234"
test_email = "jugerror@gmail.com"
test_username = "kropkakirpich"


second_test_password = "12341234"
second_test_email = "kropkasecond@gmail.com"
second_test_username = "kropkasecond"

third_test_username = "GAMEX"

base_endpoint = "users/me"
update_endpoint = base_endpoint + "/update"


async def test_drop_current_db():
    await clear_db()
    assert 1 == 1


async def insert_test_user(session: AsyncSession, cookies: bool = True):
    user: User = await create_user(
        db_session=session,
        obj_in=UserSignUp(
            password=second_test_password,
            email=second_test_email,
            username=second_test_username,
        ),
    )

    user = await update_user(
        db_session=session, db_obj=user, obj_in={"is_verified": True}
    )

    if not cookies:
        return user

    access, refresh = create_new_token_set(email=second_test_email, user_id=user.id)
    return user, access, refresh


async def test_user_sign_up(async_client: AsyncClient):
    response = await async_client.post(
        base_endpoint,
        json={
            "password": test_password,
            "email": test_email,
            "username": test_username,
        },
    )
    assert response.status_code == 200


async def test_user_without_auth(async_client: AsyncClient):
    response = await async_client.get(base_endpoint)
    assert response.status_code == 401


async def test_user_with_auth(async_client: AsyncClient):
    async with async_session() as session:
        user_data, access, refresh = await insert_test_user(session=session)
    async_client.cookies = {"access": access, "refresh": refresh}
    response = await async_client.get(base_endpoint)
    assert response.status_code == 200
    assert response.json()["email"] == second_test_email
    assert response.json()["username"] == second_test_username


async def test_update_username_already_exist(async_client: AsyncClient):
    response = await async_client.patch(
        update_endpoint + "/username", json={"username": test_username}
    )
    assert response.status_code == 409


async def test_update_username(async_client: AsyncClient):
    response = await async_client.patch(
        update_endpoint + "/username", json={"username": third_test_username}
    )
    assert response.status_code == 200
    assert response.json()["username"] == third_test_username


async def test_oldmail_code(async_client: AsyncClient):
    response = await async_client.post(
        base_endpoint + "/oldmail"
    )
    assert response.status_code == 200


async def test_reset_password(async_client: AsyncClient):
    response = await async_client.post(
        "users/reset-password", json={"email": second_test_email}
    )
    assert response.status_code == 200
