from time import time

from sqlalchemy import Column, Integer, String, VARCHAR, Enum, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from core.database import Base
from app.users.models import User
from app.offers.models import Offer

# После нужно будет фиксить из-за того, что
#  сейчас не совсем понятно что полностью удалять, а что
#  хранить в скрытом от пользователей состоянии
class Purchase(Base):
    __tablename__ = "purchase"
    
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    offer_id = Column(Integer, ForeignKey("offer.id", ondelete="SET NULL"))
    name = Column(String)
    description = Column(String)
    price = Column(Integer)
    count = Column(Integer)
    status = Column(Enum("completed", "process", "refund", name="purchase_status"), default="process")
    created_at = Column(Integer, nullable=False, default=int(time()))
    updated_at = Column(Integer, nullable=False, default=int(time()), onupdate=int(time()))

    parcels: Mapped[list["Parcel"]] =  relationship(back_populates="purchase", lazy="selectin")
    buyer: Mapped["User"] = relationship(lazy="noload")
    offer: Mapped["Offer"] = relationship(lazy="noload")


class Parcel(Base):
    __tablename__ = "parcel"
    
    id = Column(Integer, primary_key=True)
    purchase_id = Column(Integer, ForeignKey('purchase.id', ondelete="CASCADE"))
    value = Column(VARCHAR(500))

    purchase: Mapped["Purchase"] = relationship(back_populates="parcels", lazy="noload")