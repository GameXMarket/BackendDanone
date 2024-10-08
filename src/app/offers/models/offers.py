import time
from typing import List

from sqlalchemy import func, select, Column, Integer, String, Text, Enum, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, Mapped

from core.database import Base
from app.users.models import User
from .delivery import Delivery


# Попытки в автоматическую замену count через hybrid
# Оставил на будущее, чтоб не забыть направление в котором
# Можно искать инфу
# from sqlalchemy.ext.hybrid import hybrid_property


class Offer(Base):
    __tablename__ = "offer"
    id = Column(Integer, primary_key=True, index=True)
    # About ondelete arg:
    # https://docs.sqlalchemy.org/en/20/core/constraints.html#sqlalchemy.schema.ForeignKey.params.ondelete
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))  # ForeignKey to user_id
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Integer, CheckConstraint('price >= 1 and price <=1000000', name='check_price'), nullable=False)
    count = Column(Integer, CheckConstraint('count >= 0 AND count <= 1000000', name='check_count'), nullable=False)
    status = Column(
        Enum("active", "hidden", "deleted", name="offer_statuses"),
        nullable=False,
        default="hidden",
    )
    is_autogive_enabled = Column(Boolean, nullable=True, default=None)
    is_autoup_enabled = Column(Boolean, nullable=True, default=False)
    upped_at = Column(Integer, nullable=False, default=int(time.time()))

    user: Mapped["User"] = relationship(back_populates="offers", lazy="noload")
    category_values: Mapped[list["OfferCategoryValue"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    deliveries: Mapped[List["Delivery"]] = relationship(
        back_populates="offer", lazy="noload"
    )

    async def get_real_count(self, db_session: AsyncSession):
        if not self.is_autogive_enabled:
            return self.count
        
        value_count_stmt = select(func.count(Delivery.id)).where(
            Delivery.offer_id == self.id
        )
        result = await db_session.execute(value_count_stmt)

        return result.scalar_one()


class OfferCategoryValue(Base):
    __tablename__ = "offer_category_value"
    category_value_id = Column(
        Integer, ForeignKey("category_value.id"), primary_key=True
    )
    offer_id = Column(
        Integer, ForeignKey("offer.id", ondelete="CASCADE"), primary_key=True
    )
