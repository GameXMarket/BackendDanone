import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_


class PurchaseManager:
    def __init__(self) -> None:
        pass
    
    #crud
    async def create_purchase(self):
        ...
    
    async def get_purchase(self):
        ...
    
    async def update_purchase(self):
        ...
    
    async def delete_purchase(self):
        ...
    

purchase_manager = PurchaseManager()
