from types import CoroutineType
from asyncio import create_task


class __SetupHelper:   
    def __init__(self) -> None:
        self.to_setup: list[CoroutineType] = []
    
    def add_new_coroutine_def(self, func: CoroutineType):
        """
        Поддерживаются только async функции
        """
        if not isinstance(func, CoroutineType):
            raise ValueError
        
        self.to_setup.append(func)
    
    def start_setup(self):
        for coro in self.to_setup:
            create_task(coro)

setup_helper =  __SetupHelper()
