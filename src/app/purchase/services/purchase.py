import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from .. import schemas


class PurchaseManager:
    def __init__(self) -> None:
        pass
    
    #crud
    async def create_purchase(self, db_session: AsyncSession, user_id: int, new_purchase_data: schemas.PurchaseCreate):
        ...
    
    async def get_purchase(self, db_session: AsyncSession, user_id: int,):
        ...
    
    async def update_purchase(self, db_session: AsyncSession, user_id: int,):
        ...
    
    async def delete_purchase(self, db_session: AsyncSession, user_id: int,):
        ...
    

purchase_manager = PurchaseManager()
