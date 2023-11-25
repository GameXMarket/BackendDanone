from fastapi import Request, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from services import users as UserService
from core import security
from core.database import get_session


async def get_current_user(
    request: Request, db_session: AsyncSession = Depends(get_session)
):
    token_data = security.verify_access_token(request.cookies.get("token"))

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    user = await UserService.get_by_email(db_session, email=token_data.email)
    return user


async def get_current_active_user():
    pass


async def get_current_superuser():
    pass
