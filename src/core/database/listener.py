import logging
from types import FunctionType

import asyncpg
from sqlalchemy.ext.asyncio.engine import AsyncEngine


class PostgreListener:
    def __init__(self, logger: logging.Logger, connection: asyncpg.connection.Connection) -> None:
        self.__logger = logger
        self.__connection = connection
        self.__listeners: list[str] = []
    
    @staticmethod
    async def create_new_listener(logger: logging.Logger, engine: AsyncEngine):
        sqlalchemy_raw_connection = await engine.raw_connection()
        connection = sqlalchemy_raw_connection.driver_connection
        return PostgreListener(logger, connection)
    
    async def add_listener(self, channel: str, callback: FunctionType) -> None:
        await self.__connection.add_listener(channel, callback)
        self.__listeners.append(channel)
        self.__logger.info(f"Added listener: channel: {channel}l callback: {callback.__name__}")
    
    async def remove_listener(self, channel: str, callback: FunctionType):
        await self.__connection.add_listener(channel, callback)
        self.__listeners.remove(channel)
        self.__logger.info(f"Deleted listener: channel: {channel}l callback: {callback.__name__}")

    async def __test__notify(self, channel: str, payload):
        await self.__connection.execute("NOTIFY $1, '$2'", channel, payload)
    
    @property
    def listeners(self):
        return self.__listeners

