from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
