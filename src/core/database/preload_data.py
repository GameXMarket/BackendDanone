import logging

from app.users import models as models_u, services as services_u, schemas as schemas_u
from app.categories import (
    models as models_c,
    services as services_c,
    schemas as schemas_c,
)
from app.offers import models as models_f, services as sevices_f, schemas as schemas_f
from core.settings import config as conf
from core.database import context_get_session
from core.database import event_listener


async def preload_db_main():
    logger = logging.getLogger("uvicorn")
    await event_listener.open_listener_connection(logger, conf.ASYNCPG_DB_URL)
    await event_listener._PostgreListener__test__notify("test_main", "Ok")
    await __init_base_db()


async def __init_base_db():
    await __init_user()
    await __init_categories()
    await __init_offers()


async def __init_categories():
    await __init_categories_carcass()
    await __init_categories_values()


async def __init_categories_carcass():
    async with context_get_session() as db_session:
        carcass = await services_c.categories_carcass.get_all(db_seesion=db_session)
        if not carcass or conf.DROP_TABLES:
            carcass: models_c.category_carcasses.CategoryCarcass = (
                await services_c.categories_carcass.create_category(
                    db_session=db_session,
                    author_id=1,
                    obj_in=schemas_c.CategoryCarcassCreate(
                        select_name="Выберите игру",
                        is_root=True,
                        in_offer_name="Игра",
                        admin_comment="Выбор игры",
                        is_last=False,
                    ),
                )
            )
            carcass: models_c.category_carcasses.CategoryCarcass = (
                await services_c.categories_carcass.create_category(
                    db_session=db_session,
                    author_id=1,
                    obj_in=schemas_c.CategoryCarcassCreate(
                        select_name="Выберите услугу",
                        is_root=False,
                        in_offer_name="Тип объявления",
                        admin_comment="Услуги для игры",
                        is_last=False,
                    ),
                )
            )
            carcass: models_c.category_carcasses.CategoryCarcass = (
                await services_c.categories_carcass.create_category(
                    db_session=db_session,
                    author_id=1,
                    obj_in=schemas_c.CategoryCarcassCreate(
                        select_name="Выберите уровни БП",
                        is_root=False,
                        in_offer_name="Уровни БП",
                        admin_comment="Уровни боевого пропуска для BrawlStars",
                        is_last=True,
                    ),
                )
            )
            carcass: models_c.category_carcasses.CategoryCarcass = (
                await services_c.categories_carcass.create_category(
                    db_session=db_session,
                    author_id=1,
                    obj_in=schemas_c.CategoryCarcassCreate(
                        select_name="Выберите способ доставки",
                        is_root=False,
                        in_offer_name="Способ доставки",
                        admin_comment="Способ доставки для игры BrawlStars",
                        is_last=False,
                    ),
                )
            )
            carcass: models_c.category_carcasses.CategoryCarcass = (
                await services_c.categories_carcass.create_category(
                    db_session=db_session,
                    author_id=1,
                    obj_in=schemas_c.CategoryCarcassCreate(
                        select_name="Выберите номинал",
                        is_root=False,
                        in_offer_name="Номинал",
                        admin_comment="Номинал гемов для игры BrawlStart",
                        is_last=True,
                    ),
                )
            )


async def __init_categories_values():
    async with context_get_session() as db_session:
        categorie_value: models_c.category_values.CategoryValue = (
            await services_c.categories_values.get_all(db_session=db_session)
        )
        if not categorie_value or conf.DROP_TABLES:
            categorie_value: models_c.category_values.CategoryValue = (
                await services_c.categories_values.create_value(
                    db_session=db_session,
                    author_id=1,
                    carcass_id=1,
                    value=schemas_c.catergories_value.ValueCreate(
                        value="Brawl Stars",
                        next_carcass_id=2,
                    ),
                )
            )
            categorie_value: models_c.category_values.CategoryValue = (
                await services_c.categories_values.create_value(
                    db_session=db_session,
                    author_id=1,
                    carcass_id=2,
                    value=schemas_c.catergories_value.ValueCreate(
                        value="Покупка гемов",
                        next_carcass_id=3,
                    ),
                )
            )
            categorie_value: models_c.category_values.CategoryValue = (
                await services_c.categories_values.create_value(
                    db_session=db_session,
                    author_id=1,
                    carcass_id=3,
                    value=schemas_c.catergories_value.ValueCreate(
                        value="Supersell ID",
                        next_carcass_id=4,
                    ),
                )
            )
            categorie_value: models_c.category_values.CategoryValue = (
                await services_c.categories_values.create_value(
                    db_session=db_session,
                    author_id=1,
                    carcass_id=3,
                    value=schemas_c.catergories_value.ValueCreate(
                        value="Встреча в жизни",
                        next_carcass_id=4,
                    ),
                )
            )
            categorie_value: models_c.category_values.CategoryValue = (
                await services_c.categories_values.create_value(
                    db_session=db_session,
                    author_id=1,
                    carcass_id=3,
                    value=schemas_c.catergories_value.ValueCreate(
                        value="Через сторонние",
                        next_carcass_id=4,
                    ),
                )
            )
            categorie_value: models_c.category_values.CategoryValue = (
                await services_c.categories_values.create_value(
                    db_session=db_session,
                    author_id=1,
                    carcass_id=4,
                    value=schemas_c.catergories_value.ValueCreate(
                        value="30 Гемов",
                        next_carcass_id=None,
                    ),
                )
            )
            categorie_value: models_c.category_values.CategoryValue = (
                await services_c.categories_values.create_value(
                    db_session=db_session,
                    author_id=1,
                    carcass_id=4,
                    value=schemas_c.catergories_value.ValueCreate(
                        value="170 Гемов",
                        next_carcass_id=None,
                    ),
                )
            )
            categorie_value: models_c.category_values.CategoryValue = (
                await services_c.categories_values.create_value(
                    db_session=db_session,
                    author_id=1,
                    carcass_id=4,
                    value=schemas_c.catergories_value.ValueCreate(
                        value="2000 Гемов",
                        next_carcass_id=None,
                    ),
                )
            )
            categorie_value: models_c.category_values.CategoryValue = (
                await services_c.categories_values.create_value(
                    db_session=db_session,
                    author_id=1,
                    carcass_id=2,
                    value=schemas_c.catergories_value.ValueCreate(
                        value="Боевой пропуск",
                        next_carcass_id=5,
                    ),
                )
            )
            categorie_value: models_c.category_values.CategoryValue = (
                await services_c.categories_values.create_value(
                    db_session=db_session,
                    author_id=1,
                    carcass_id=5,
                    value=schemas_c.catergories_value.ValueCreate(
                        value="1 уровень БП",
                        next_carcass_id=None,
                    ),
                )
            )
            categorie_value: models_c.category_values.CategoryValue = (
                await services_c.categories_values.create_value(
                    db_session=db_session,
                    author_id=1,
                    carcass_id=5,
                    value=schemas_c.catergories_value.ValueCreate(
                        value="5 уровеней БП",
                        next_carcass_id=None,
                    ),
                )
            )
            categorie_value: models_c.category_values.CategoryValue = (
                await services_c.categories_values.create_value(
                    db_session=db_session,
                    author_id=1,
                    carcass_id=5,
                    value=schemas_c.catergories_value.ValueCreate(
                        value="10 уровеней БП",
                        next_carcass_id=None,
                    ),
                )
            )


async def __init_offers():
    async with context_get_session() as db_session:
        offer: models_f.Offer = await sevices_f.get_mini_by_offset_limit(
            db_session=db_session, offset=0, limit=10
        )

        if (not offer or conf.DROP_TABLES) and conf.DEBUG:
            offer: models_f.Offer = await sevices_f.create_offer(
                db_session=db_session,
                user_id=1,
                obj_in=schemas_f.CreateOffer(
                    name="BrawStars...",
                    description="Brawl..stars",
                    price=100,
                    count=5,
                    category_value_ids=[1],
                ),
            )
            offer: models_f.Offer = await sevices_f.create_offer(
                db_session=db_session,
                user_id=1,
                obj_in=schemas_f.CreateOffer(
                    name="BrawStars...",
                    description="Brawl..stars",
                    price=50,
                    count=50,
                    category_value_ids=[2],
                ),
            )
            offer: models_f.Offer = await sevices_f.create_offer(
                db_session=db_session,
                user_id=1,
                obj_in=schemas_f.CreateOffer(
                    name="BrawStars...",
                    description="Brawl..stars",
                    price=1000,
                    count=20,
                    category_value_ids=[3],
                ),
            )


async def __init_user():
    async with context_get_session() as db_session:
        user: models_u.User = await services_u.get_by_email(
            db_session, email=conf.BASE_ADMIN_MAIL_LOGIN
        )

        if not user:
            user: models_u.User = await services_u.create_user(
                db_session=db_session,
                obj_in=schemas_u.UserSignUp(
                    password=conf.BASE_ADMIN_MARKET_PASSWORD,
                    email=conf.BASE_ADMIN_MAIL_LOGIN,
                    username=conf.BASE_ADMIN_MARKET_LOGIN,
                ),
                additional_fields={"role_id": 3, "is_verified": True},
            )

        if conf.DEBUG:
            test_user: models_u.User = await services_u.get_by_email(
                db_session, email=conf.BASE_DEBUG_USER_EMAIL
            )
            if not test_user:
                test_user: models_u.User = await services_u.create_user(
                    db_session=db_session,
                    obj_in=schemas_u.UserSignUp(
                        password=conf.BASE_DEBUG_USER_PASS,
                        email=conf.BASE_DEBUG_USER_EMAIL,
                        username=conf.BASE_DEBUG_USER_LOGIN,
                    ),
                    additional_fields={"role_id": 0, "is_verified": True},
                )
