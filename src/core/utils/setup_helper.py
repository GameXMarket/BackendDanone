from typing import Any
from types import MethodType, FunctionType
from asyncio import create_task


class __SetupHelper:   
    def __init__(self) -> None:
        self.to_setup: list[tuple[FunctionType, tuple[Any]]] = []
    
    def add_new_coroutine_def(self, func: MethodType | FunctionType, *args):
        """
        Поддерживаются только async функции
        """
        if not isinstance(func, (MethodType, FunctionType)):
            raise ValueError
        
        self.to_setup.append((func, args))
    
    def start_setup(self):
        for coro, args in self.to_setup:
            create_task(coro(*args))


setup_helper =  __SetupHelper()
