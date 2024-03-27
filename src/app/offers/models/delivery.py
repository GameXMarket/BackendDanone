from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from core.database import Base

if TYPE_CHECKING:
    from .offers import Offer


# TODO прокинуть связи, маппед и тд
class Delivery(Base):
    __tablename__ = "delivery"
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey('offer.id'))
    value = Column(Integer)
    created_at = Column(Integer)

    offer = relationship("Offer", back_populates="delivery", lazy="noload")
