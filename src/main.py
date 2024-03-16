import os
import json
import logging
import secrets
from typing import Annotated
from contextlib import asynccontextmanager

import asyncpg
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

import core.settings as conf
from core.database import event_listener, init_models, context_get_session
from core.redis import redis_pool, get_redis_client
from core.logging import InfoHandlerTG, ErrorHandlerTG
from core.utils import check_dir_exists, setup_helper
from app.users import users_routers
from app.tokens import tokens_routers
from app.offers import offers_routers
from app.categories import category_routers
from app.messages import message_routers
from app.attachment import attachment_routers
# ниже импорты, для инит дб, лучше вынести в отдельный файл вместе с методом.
from app.users import models as models_u, schemas as schemas_u
from app.users.services import get_by_email, create_user


current_file_path = os.path.abspath(__file__)
locales_path = os.path.join(os.path.dirname(current_file_path), "_locales")


""" # Temp dev sql
INSERT INTO category_carcass (id, author_id, is_root, select_name, in_offer_name, admin_comment, is_last, created_at, updated_at)
VALUES  
(1,  1, true, 'Выберите игру', 'Игра', 'Рут, выбор игры, для удобства, нигде не видно данное поле.', false,  1707674165,  1707674165),
(2,  1, false, 'Выберите услугу', 'Тип объявления', 'Услуги для игры brawl stars', false,  1707674328,  1707674328),
(5,  1, false, 'Выберите уровни БП', 'Уровни БП', 'Уровни Боевоего пропуска для игры brawl stars', false,  1707675293,  1707675293),
(4,  1, false, 'Выберите номинал', 'Номинал', 'Номинал гемов для игры brawl stars,', false,  1707674593,  1707674593),
(3,  1, false, 'Выберите способ доставки', 'Способ доставки', 'Способы доставки для игры, для гемов brawl stars', false,  1707674536,  1707674536);
"""
"""
INSERT INTO category_value (id, carcass_id, next_carcass_id, author_id, value, created_at, updated_at)
VALUES
(1,  1,  2,  1, 'Brawl Stars',  1707674732,  1707674732),
(2,  2,  3,  1, 'Покупка гемов',  1707674857,  1707674857),
(3,  3,  4,  1, 'Supersell ID',  1707674900,  1707674900),
(4,  3,  4,  1, 'Встреча в жизни',  1707674918,  1707674918),
(5,  3,  4,  1, 'Через сторонние',  1707674933,  1707674933),
(6,  4, NULL,  1, '30 Гемов',  1707675066,  1707675066),
(7,  4, NULL,  1, '170 Гемов',  1707675071,  1707675071),
(8,  4, NULL,  1, '2000 Гемов',  1707675079,  1707675079),
(9,  2,  5,  1, 'Боевой пропуск',  1707675228,  1707676954),
(10,  5, NULL,  1, '1 уровень БП',  1707677022,  1707677022),
(11,  5, NULL,  1, '5 уровней БП',  1707677036,  1707677036),
(12,  5, NULL,  1, '10 уровней БП',  1707677041,  1707677041);
"""


class StartedFailed(Exception):
    def __init__(self, message):
        super().__init__(message)


async def __init_base_db():
    async with context_get_session() as db_session:
        user: models_u.User = await get_by_email(
            db_session, email=conf.BASE_ADMIN_MAIL_LOGIN
        )

        if not user:
            user: models_u.User = await create_user(
                db_session=db_session,
                obj_in=schemas_u.UserSignUp(
                    password=conf.BASE_ADMIN_MARKET_PASSWORD,
                    email=conf.BASE_ADMIN_MAIL_LOGIN,
                    username=conf.BASE_ADMIN_MARKET_LOGIN,
                ),
                additional_fields={"role_id": 3, "is_verified": True},
            )
        
        if conf.DEBUG:
            test_user: models_u.User = await get_by_email(
                db_session, email=conf.BASE_DEBUG_USER_EMAIL
            )
            if not test_user:
                test_user: models_u.User = await create_user(
                    db_session=db_session,
                    obj_in=schemas_u.UserSignUp(
                        password=conf.BASE_DEBUG_USER_PASS,
                        email=conf.BASE_DEBUG_USER_EMAIL,
                        username=conf.BASE_DEBUG_USER_LOGIN,
                    ),
                    additional_fields={"role_id": 0, "is_verified": True},
                )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ! Решение только на время разработки
    info_tg_handler = InfoHandlerTG()
    error_tg_handler = ErrorHandlerTG()

    uvi_access_logger = logging.getLogger("uvicorn.access")
    uvi_access_logger.addHandler(info_tg_handler)

    logger = logging.getLogger("uvicorn")
    logger.addHandler(info_tg_handler)
    logger.addHandler(error_tg_handler)

    await init_models(drop_all=conf.DROP_TABLES)
    await __init_base_db()
    
    await event_listener.open_listener_connection(logger, conf.ASYNCPG_DB_URL)
    await event_listener._PostgreListener__test__notify("test_main", "Ok")

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
    "https://test.yunikeil.ru",
    "https://fronted-danone-git-front-logic-dydecs-projects.vercel.app",
    "https://fronted-danone-git-development-dydecs-projects.vercel.app",
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
        proxy_headers=not conf.DEBUG,
    )
