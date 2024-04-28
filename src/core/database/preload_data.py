import logging

from fastapi import Depends

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from app.users import models as models_u, services as services_u, schemas as schemas_u
from app.categories import (
    models as models_c,
    services as services_c,
    schemas as schemas_c,
)
from app.offers import models as models_f, services as sevices_f, schemas as schemas_f
from core.settings import config as conf
from core.database import get_session
from core.database import event_listener


async def preload_db_main(db_session: AsyncSession):
    logger = logging.getLogger("uvicorn")
    await event_listener.open_listener_connection(logger, conf.ASYNCPG_DB_URL)
    await event_listener._PostgreListener__test__notify("test_main", "Ok")
    await __init_base_db(db_session)


async def __init_base_db(db_session: AsyncSession):
    try:
        await __init_user(db_session)
        await __init_categories(db_session)
        await __init_offers(db_session)
    except sqlalchemy.exc.IntegrityError:
        logging.getLogger("uvicorn").warning("cant init dbase, IntegrityError!")


async def __init_categories(db_session: AsyncSession):
    await __init_categories_carcass(db_session)
    await __init_categories_values(db_session)


async def __init_categories_carcass(db_session: AsyncSession):
    categories_to_create = [
        {
            "select_name": "Выберите игру",
            "is_root": True,
            "in_offer_name": "Игра",
            "admin_comment": "Выбор игры",
            "is_last": False,
        },
        {
            "select_name": "Выберите услугу",
            "is_root": False,
            "in_offer_name": "Тип объявления",
            "admin_comment": "Услуги для игры BrawlStars",
            "is_last": False,
        },
        {
            "select_name": "Выберите услугу",
            "is_root": False,
            "in_offer_name": "Тип объявления",
            "admin_comment": "Услуги для игры CS2",
            "is_last": False,
        },
        {
            "select_name": "Выберите услугу",
            "is_root": False,
            "in_offer_name": "Тип объявления",
            "admin_comment": "Услуги для игры Dota2",
            "is_last": False,
        },
        {
            "select_name": "Выберите уровни БП",
            "is_root": False,
            "in_offer_name": "Уровни БП",
            "admin_comment": "Уровни боевого пропуска для BrawlStars",
            "is_last": True,
        },
        {
            "select_name": "Выберите способ доставки",
            "is_root": False,
            "in_offer_name": "Способ доставки",
            "admin_comment": "Способ доставки для игры",
            "is_last": False,
        },
        {
            "select_name": "Выберите номинал",
            "is_root": False,
            "in_offer_name": "Номинал",
            "admin_comment": "Номинал гемов для игры BrawlStars",
            "is_last": True,
        },
        {
            "select_name": "Выберите количество ММР",
            "is_root": False,
            "in_offer_name": "Количество ММР",
            "admin_comment": "Количество ММР для игры Dota 2",
            "is_last": True,
        },
        {
            "select_name": "Выберите количество ELO",
            "is_root": False,
            "in_offer_name": "Количество ELO",
            "admin_comment": "Количество ELO для игры CS2",
            "is_last": True,
        },
    ]
    carcass = await services_c.categories_carcass.get_all(db_seesion=db_session)
    if not carcass or conf.DROP_TABLES:
        for category_data in categories_to_create:
            await services_c.categories_carcass.create_category(
                db_session=db_session,
                author_id=1,
                obj_in=schemas_c.CategoryCarcassCreate(**category_data),
            )


async def __init_categories_values(db_session: AsyncSession):
    values_to_create = [
        # New category CS2
        {"carcass_id": 1, "value": "Counter-Strike 2", "next_carcass_id": 3}, # 1
        # Subcategory
        {"carcass_id": 3, "value": "Буст ELO)", "next_carcass_id": 9}, # 2

        {"carcass_id": 9, "value": "25 ELO", "next_carcass_id": None, "is_offer_with_delivery": False}, # 3
        {"carcass_id": 9, "value": "50 ELO", "next_carcass_id": None, "is_offer_with_delivery": False}, # 4
        {"carcass_id": 9, "value": "100 ELO", "next_carcass_id": None, "is_offer_with_delivery": True}, # 5
        {"carcass_id": 9, "value": "200 ELO", "next_carcass_id": None, "is_offer_with_delivery": True}, # 6

        # New category Dota2
        {"carcass_id": 1, "value": "Dota 2", "next_carcass_id": 4}, # 7
        # Subcategory
        {"carcass_id": 4, "value": "Буст эмэмэрау)", "next_carcass_id": 8}, # 8

        {"carcass_id": 8, "value": "100 ММР", "next_carcass_id": None, "is_offer_with_delivery": False}, # 9 
        {"carcass_id": 8, "value": "1000 ММР", "next_carcass_id": None, "is_offer_with_delivery": False}, # 10
        {"carcass_id": 8, "value": "2000 ММР", "next_carcass_id": None, "is_offer_with_delivery": True}, # 11
        {"carcass_id": 8, "value": "3000 ММР", "next_carcass_id": None, "is_offer_with_delivery": True}, # 12

        # New category BrawlStars
        {"carcass_id": 1, "value": "Brawl Stars", "next_carcass_id": 2}, # 13
        # Subcategory
        {"carcass_id": 2, "value": "Покупка гемов", "next_carcass_id": 6}, # 14
        # Subcategory
        {"carcass_id": 2, "value": "Боевой пропуск", "next_carcass_id": 5}, # 15

        {"carcass_id": 6, "value": "Supersell ID", "next_carcass_id": 7}, # 16
        {"carcass_id": 6, "value": "Встреча в жизни", "next_carcass_id": 7}, # 17
        {"carcass_id": 6, "value": "Через сторонние", "next_carcass_id": 7}, # 18

        {"carcass_id": 7, "value": "30 Гемов", "next_carcass_id": None, "is_offer_with_delivery": False}, # 19
        {"carcass_id": 7, "value": "170 Гемов", "next_carcass_id": None, "is_offer_with_delivery": False}, # 20
        {"carcass_id": 7, "value": "2000 Гемов", "next_carcass_id": None, "is_offer_with_delivery": False}, # 21
        
        {"carcass_id": 5, "value": "1 уровень БП", "next_carcass_id": None, "is_offer_with_delivery": True}, # 22
        {"carcass_id": 5, "value": "5 уровней БП", "next_carcass_id": None, "is_offer_with_delivery": True}, # 23
        {"carcass_id": 5, "value": "10 уровней БП", "next_carcass_id": None, "is_offer_with_delivery": True}, # 24
    ]

    values = await services_c.categories_values.get_all(db_session=db_session)
    if not values or conf.DROP_TABLES:
        for value_data in values_to_create:
            await services_c.categories_values.create_value(
                db_session=db_session,
                author_id=1,
                carcass_id=value_data["carcass_id"],
                value=schemas_c.ValueCreate(**value_data),
            )


async def __init_offers(db_session: AsyncSession):
    offers_to_create = [
        {
            "name": "CS2 50 elo without delivery 😦",
            "description": "Просто описание для 50 elo без автовыдачи",
            "price": 1000,
            "count": 20,
            "category_value_ids": [1, 2, 4],
        },
        {
            "name": "CS2 100 elo with delivery 🎉",
            "description": "Просто описание для 100 elo с автовыдачей",
            "price": 1000,
            "count": 20,
            "category_value_ids": [1, 2, 5],
        },
        {
            "name": "Dota2 буст 1000ммр без автовыдачи ✨",
            "description": "Просто описание для буста 1000ммр без автовыдачи",
            "price": 50,
            "count": 50,
            "category_value_ids": [7, 8, 10],
        },
        {
            "name": "Dota2 буст 2000ммр с автовыдачей ❤️",
            "description": "Просто описание для буста 2000ммр автовыдачей",
            "price": 50,
            "count": 50,
            "category_value_ids": [7, 8, 11],
        },
        {
            "name": "BrawStars gems without delivery 🤍",
            "description": "Просто описание для гемов без автовыдачи",
            "price": 100,
            "count": 5,
            "category_value_ids": [13, 14, 16, 19],
        },
        {
            "name": "BrawStars battle pass with delivery 😭",
            "description": "Просто описания для бп с автовыдачей",
            "price": 100,
            "count": 5,
            "category_value_ids": [13, 15, 23],
        },
    ]

    offers = await sevices_f.get_mini_by_offset_limit(
        db_session=db_session, offset=0, limit=10
    )

    if not offers or conf.DROP_TABLES:
        for offer_data in offers_to_create:
            await sevices_f.create_offer(
                db_session=db_session,
                user_id=1,
                obj_in=schemas_f.CreateOffer(**offer_data),
            )


async def __init_user(db_session: AsyncSession):
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
