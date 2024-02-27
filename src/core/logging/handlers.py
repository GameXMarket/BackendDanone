import traceback
import logging
import asyncio

from core.utils.telegram import send_telegram_message
from core.settings.config import TG_LOG_TOKEN, TG_ERROR_LOG_CHANNEL, TG_INFO_LOG_CHANNEL


class CoreHandler(logging.Handler):
    def __init__(
        self,
        level: int | str = 0,
    ) -> None:
        self.levelnoms: dict = {
            0: self.process_notset,
            10: self.process_debug,
            20: self.process_info,
            30: self.process_warning,
            40: self.process_error,
            50: self.process_critical,
        }
        super().__init__(level)

    async def process_notset(self, record: logging.LogRecord):
        pass

    async def process_debug(self, record: logging.LogRecord):
        pass

    async def process_info(self, record: logging.LogRecord):
        message = f"`{record.levelname} - {record.message}`"
        await send_telegram_message(
            TG_LOG_TOKEN, TG_INFO_LOG_CHANNEL, message, need_keyboard=False
        )

    async def process_warning(self, record: logging.LogRecord):
        pass

    async def process_error(self, record: logging.LogRecord):
        exc_info = record.exc_info
        if exc_info:
            exc_type, exc_value, exc_traceback = exc_info
            tb_str = "".join(
                traceback.format_exception(exc_type, exc_value, exc_traceback)
            )

        message = f"`{record.levelname}\t{record.message}`\n```shell\n{tb_str}\n```"
        await send_telegram_message(TG_LOG_TOKEN, TG_ERROR_LOG_CHANNEL, message)

    async def process_critical(self, record: logging.LogRecord):
        pass

    def emit(self, record: logging.LogRecord) -> None:
        asyncio.create_task(self.levelnoms[record.levelno](record))
