from typing import List

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from core.database import Base
from app.users.models import User

from .category_carcasses import CategoryCarcass


class CategoryValue(Base):
    """
    Значения, привязанные к каркассу категории
    """

    __tablename__ = "category_carcass"
    id = Column(Integer, primary_key=True, index=True)
    carcass_id = Column(Integer, ForeignKey("category_carcass.id", ondelete="CASCADE"))
    value = Column(String, nullable=False)
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)

    carcass: Mapped["CategoryCarcass"] = relationship(lazy="noload", back_populates="values")
    author: Mapped[User] = relationship(lazy="noload")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

