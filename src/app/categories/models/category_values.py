from typing import List, TYPE_CHECKING

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import validates, relationship, Mapped

from core.database import Base
from app.users.models import User

if TYPE_CHECKING:
    from .category_carcasses import CategoryCarcass


class CategoryValue(Base):
    """
    Значения, привязанные к каркассу категории
    """

    __tablename__ = "category_value"
    id = Column(Integer, primary_key=True, index=True)
    carcass_id = Column(Integer, ForeignKey("category_carcass.id", ondelete="CASCADE"), nullable=False)
    next_carcass_id = Column(Integer, ForeignKey("category_carcass.id", ondelete="SET NULL"), nullable=True)
    author_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    value = Column(String, nullable=False)
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)

    carcass: Mapped["CategoryCarcass"] = relationship(lazy="noload", back_populates="values", foreign_keys=[carcass_id])
    next_carcass: Mapped["CategoryCarcass"] = relationship(lazy="noload", foreign_keys=[next_carcass_id])
    author: Mapped[User] = relationship(lazy="noload")
