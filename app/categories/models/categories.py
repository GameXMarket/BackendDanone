from typing import List

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from core.database import Base
from app.users.models import User
from app.categories.schemas import ToJsonCategory


class Category(Base):
    """
    root --+---> child1
           +---> child2 --+--> subchild1
           |              +--> subchild2
           +---> child3
    """

    __tablename__ = "category"
    id = Column(Integer, primary_key=True, index=True)
    parrent_id = Column(Integer, ForeignKey("category.id", ondelete="CASCADE"))
    author_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    name = Column(String, nullable=False)
    is_last = Column(Boolean, default=False, nullable=False) # TODO запрещать создание если стоит ласт
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)

    childrens: Mapped[List["Category"]] = relationship(lazy="noload")
    author: Mapped[User] = relationship(lazy="noload")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def to_json(self):
        """
        Будет адекватно работать только при lazy=selectin и подобных..
        Данный аргумент можно устанавливать непосредственно перед запросом.
        """
        result = ToJsonCategory(**self.to_dict()).model_dump()

        if self.childrens:
            result["childrens"] = [child.to_json() for child in self.childrens]
        else:
            result["childrens"] = []

        return result
