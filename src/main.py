import os
import json
import logging
import secrets
from typing import Annotated
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

import core.settings as conf
from core.database import event_listener, init_models, context_get_session

from core.redis import redis_pool, get_redis_client
from core.logging import InfoHandlerTG, WarningHandlerTG, ErrorHandlerTG
from core.utils import check_dir_exists, setup_helper
from app.users import users_routers
from app.tokens import tokens_routers
from app.offers import offers_routers, delivery_routers
from app.categories import category_routers
from app.messages import message_routers
from app.attachment import attachment_routers
#Не дай бог строчку ниже куда - либо перенести...
from core.database.preload_data import preload_db_main


current_file_path = os.path.abspath(__file__)
locales_path = os.path.join(os.path.dirname(current_file_path), "_locales")


class StartedFailed(Exception):
    def __init__(self, message):
        super().__init__(message)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ! Решение только на время разработки
    # Info handlers ОЧЕНЬ сильно резали производительность
    #info_tg_handler = InfoHandlerTG()
    warning_tg_handler = WarningHandlerTG()
    error_tg_handler = ErrorHandlerTG()

    uvi_access_logger = logging.getLogger("uvicorn.access")
    #uvi_access_logger.addHandler(info_tg_handler)
    uvi_access_logger.addHandler(warning_tg_handler)

    logger = logging.getLogger("uvicorn")
    #logger.addHandler(info_tg_handler)
    logger.addHandler(warning_tg_handler)
    logger.addHandler(error_tg_handler)

    await init_models(drop_all=conf.DROP_TABLES)
    async with context_get_session() as session:
        await preload_db_main(session)

    
    async with get_redis_client() as client:
        logger.info(f"Redis ping returned with: {await client.ping()}.")

    await check_dir_exists(conf.DATA_PATH, auto_create=True)
    
    setup_helper.start_setup()
        
    yield
    
    await event_listener.close_listener_connection()
    await redis_pool.aclose()
    logger.info("RedisPool closed.")


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

origins = [
    "http://localhost:80",
    "http://localhost:8080",
    "http://localhost:3000",
    "https://fronted-danone-k7l2.vercel.app",
    "http://31.129.111.90:8090",
    "https://test.yunikeil.ru",
    "https://fronted-danone-git-front-logic-dydecs-projects.vercel.app",
    "https://fronted-danone-git-development-dydecs-projects.vercel.app",
    "https://fronted-danone.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
app.include_router(category_routers)
app.include_router(message_routers)
app.include_router(attachment_routers)
app.include_router(delivery_routers)


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
    return get_openapi(title=conf.TITLE, version=conf.VERSION, routes=app.routes, tags=openapi_tags)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app="main:app",
        host=conf.SERVER_IP,
        port=conf.SERVER_PORT,
        reload=conf.DEBUG,
        proxy_headers=not conf.DEBUG,
    )
