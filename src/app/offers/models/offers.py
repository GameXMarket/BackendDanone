from typing import List

from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from core.database import Base
from app.users.models import User
from .delivery import Delivery


## Добавить ограничения стринга на длину (varchar) относится не только к данной таблице


class Offer(Base):
    __tablename__ = "offer"
    id = Column(Integer, primary_key=True, index=True)
    # About ondelete arg:
    # https://docs.sqlalchemy.org/en/20/core/constraints.html#sqlalchemy.schema.ForeignKey.params.ondelete
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))  # ForeignKey to user_id
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    count = Column(Integer, nullable=False)
    status = Column(Enum('active', 'hidden', 'deleted', name="offer_statuses"), nullable=False, default="active")
    upped_at = Column(Integer, nullable=False)

    user: Mapped["User"] = relationship(back_populates="offers", lazy="noload")
    category_values: Mapped[list["OfferCategoryValue"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    delivery: Mapped["Delivery"] = relationship(back_populates="offer", lazy="noload")


class OfferCategoryValue(Base):
    __tablename__ = "offer_category_value"
    category_value_id = Column(Integer, ForeignKey('category_value.id'), primary_key=True)
    offer_id = Column(Integer, ForeignKey('offer.id', ondelete="CASCADE"), primary_key=True)
    # deliveries: Mapped[List["Delivery"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
