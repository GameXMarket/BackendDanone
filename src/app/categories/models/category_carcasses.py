from typing import List, TYPE_CHECKING

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from core.database import Base
from app.users.models import User

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
    author_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    is_root = Column(Boolean, nullable=False)
    select_name = Column(String(50), nullable=False)
    in_offer_name = Column(String(25), nullable=False)
    admin_comment = Column(String(200), nullable=True)
    is_last = Column(Boolean, default=False, nullable=False)

    values: Mapped[List[CategoryValue]] = relationship(lazy="noload", back_populates="carcass", foreign_keys=[CategoryValue.carcass_id])
    author: Mapped[User] = relationship(lazy="noload")
