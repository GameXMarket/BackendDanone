import logging
from typing import Union
from types import FunctionType

import asyncpg
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from core.settings import config


class PostgreListener:
    def __init__(self) -> None:
        self.__started = False
        self.__logger: logging.Logger = None
        self.__connection: asyncpg.connection.Connection = None
        self.__listeners: list[str] = []

    async def open_listener_connection(
        self, logger: logging.Logger, connection_url: str
    ):
        self.__connection = await asyncpg.connect(connection_url)
        self.__logger = logger
        self.__started = True

    async def close_listener_connection(self):
        self.__started = False
        await self.__connection.close()

    async def add_listener(self, channel: str, callback: FunctionType) -> None:
        if not self.__started:
            raise ValueError

        await self.__connection.add_listener(channel, callback)
        self.__listeners.append(channel)
        self.__logger.info(
            f"Added pg listener: channel: {channel}; callback: {callback.__name__}"
        )

    async def remove_listener(self, channel: str, callback: FunctionType):
        if not self.__started:
            raise ValueError

        await self.__connection.add_listener(channel, callback)
        self.__listeners.remove(channel)
        self.__logger.info(
            f"Deleted pg listener: channel: {channel}; callback: {callback.__name__}"
        )

    async def __test__notify(self, channel: str, payload):
        if not self.__started:
            raise ValueError

        await self.add_listener("test_main", self.__test_notify_callback)
        await self.__connection.execute(f"NOTIFY {channel}, '{payload}'")
        await self.remove_listener("test_main", self.__test_notify_callback)

    async def __test_notify_callback(
        self,
        connection: asyncpg.connection.Connection,
        pid: str,
        channel: str,
        payload: str,
    ):
        self.__logger.info(f"Test notification received from: {channel}; data: {payload}!")
