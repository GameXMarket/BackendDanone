from typing import Any
import logging
import aiofiles.os
from uvicorn.main import Server


logger = logging.getLogger("uvicorn")


async def check_dir_exists(path: str | Any, auto_create: bool = True):
    """
    Проверяет существование директории, по умолчанию, если не нашлась, создаёт её
    """

    path_exist = await aiofiles.os.path.exists(path)

    if path_exist:
        return True
    elif auto_create:
        await aiofiles.os.makedirs(path)
        logger.info(f"Directory {path} created.")
        return True

    return False


original_handler = Server.handle_exit

class AppStatus:
    should_exit = False
    
    @staticmethod
    def handle_exit(*args, **kwargs):
        AppStatus.should_exit = True
        original_handler(*args, **kwargs)

Server.handle_exit = AppStatus.handle_exit
