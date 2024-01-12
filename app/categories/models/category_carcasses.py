from typing import List, TYPE_CHECKING

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from core.database import Base
from app.users.models import User

if TYPE_CHECKING:
    from .category_values import CategoryValue


class CategoryCarcass(Base):
    """
    root --+---> child1
           +---> child2 --+--> subchild1
           |              +--> subchild2
           +---> child3
    """

    __tablename__ = "category_carcass"
    id = Column(Integer, primary_key=True, index=True)
    parrent_id = Column(Integer, ForeignKey("category_carcass.id", ondelete="CASCADE"))
    author_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    name = Column(String, nullable=False)
    is_last = Column(Boolean, default=False, nullable=False)
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)

    childrens: Mapped[List["CategoryCarcass"]] = relationship(lazy="noload")
    values: Mapped[List["CategoryValue"]] = relationship(lazy="noload", back_populates="carcass")
    author: Mapped[User] = relationship(lazy="noload")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

