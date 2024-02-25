from typing import Any
import logging
import os


logger = logging.getLogger("uvicorn")


def check_dir_exists(path: str | Any, auto_create: bool = True):
    """
    Проверяет существование директории, по умолчанию, если не нашлась, создаёт её 
    """
    if os.path.exists(path):
        return True
    elif auto_create:
        os.mkdir(path)
        logger.info(f"Directory {path} created.")
        return True
    
    return False


