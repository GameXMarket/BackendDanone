from typing import List

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from core.database import Base
from app.users.models import User


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
    name = Column(String)
    created_at = Column(Integer)
    updated_at = Column(Integer)

    childrens: Mapped[List["Category"]] = relationship(lazy="noload")
    author: Mapped[User] = relationship(lazy="noload")

    def to_json(self):
        """
        Будет адекватно работать только при lazy=selectin и подобных..
        Данный аргумент можно устанавливать непосредственно перед запросом.
        """
        result = {
            "id": self.id,
            "name": self.name,
        }

        if self.childrens:
            result["childrens"] = [child.to_json() for child in self.childrens]
        else:
            result["childrens"] = []

        return result
