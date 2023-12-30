import os
import json
import secrets
from typing import Annotated
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from sqlalchemy.ext.asyncio import AsyncSession

import core.settings as conf
from core.database import init_models, get_session
from app.users import users_routers
from app.tokens import tokens_routers
from app.offers import offers_routers
from app.users import models as models_u, schemas as schemas_u
from app.users.services import get_by_email, create_user


current_file_path = os.path.abspath(__file__)
locales_path = os.path.join(os.path.dirname(current_file_path), "_locales")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models(drop_all=conf.DROP_TABLES)

    db_session: AsyncSession = await anext(get_session())
    user: models_u.User = await get_by_email(
        db_session, email=conf.BASE_ADMIN_MAIL_LOGIN
    )

    if not user:
        user: models_u.User = await create_user(
            db_session=db_session,
            obj_in=schemas_u.AdminSignUp(
                password=conf.BASE_ADMIN_MARKET_PASSWORD,
                email=conf.BASE_ADMIN_MAIL_LOGIN,
                username=conf.BASE_ADMIN_MARKET_LOGIN,
            ),
        )
    
    yield


security = HTTPBasic()
openapi_tags = json.loads(open(f"{locales_path}/tags_metadata.json", "r").read())
app = FastAPI(
    debug=conf.DEBUG,
    version=conf.VERSION,
    title=conf.TITLE,
    summary=conf.SUMMARY,
    openapi_tags=openapi_tags,
    openapi_url="/openapi.json" if conf.DEBUG else None,
    docs_url="/docs" if conf.DEBUG else None,
    redoc_url=None,
    lifespan=lifespan,
)

# На время разработки...
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if conf.DEBUG:
    from debug import debug_routers

    app.include_router(debug_routers)

app.include_router(users_routers)
app.include_router(tokens_routers)
app.include_router(offers_routers)


def __temp_get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = b"danone_test"
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = b"password"
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/docs", include_in_schema=False)
async def get_swagger_documentation(
    username: str = Depends(__temp_get_current_username),
):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


@app.get("/openapi.json", include_in_schema=False)
async def openapi(username: str = Depends(__temp_get_current_username)):
    return get_openapi(title=conf.TITLE, version=conf.VERSION, routes=app.routes)


if __name__ == "__main__":
    uvicorn.run(
        app="main:app" if conf.DEBUG else app,
        host=conf.SERVER_IP,
        port=conf.SERVER_PORT,
        reload=conf.DEBUG,
    )
