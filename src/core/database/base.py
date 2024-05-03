from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy import Column, Integer
from time import time


class Base(AsyncAttrs, DeclarativeBase):
    created_at = Column(Integer, default=lambda: int(time()), nullable=False)
    updated_at = Column(Integer, default=lambda: int(time()), onupdate=lambda: int(time()), nullable=False)

    def to_dict(self, base_dict: dict = {}):
        main_dict = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return main_dict | base_dict
