from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, VARCHAR
from sqlalchemy.orm import relationship, Mapped
from core.database import Base

if TYPE_CHECKING:
    from .offers import Offer


class Delivery(Base):
    __tablename__ = "delivery"
    
    id = Column(Integer, primary_key=True)
    offer_id = Column(Integer, ForeignKey('offer.id', ondelete="CASCADE"))
    value = Column(VARCHAR(500))

    offer: Mapped["Offer"] = relationship(back_populates="deliveries", lazy="noload")