from time import time

from sqlalchemy import Column, Integer, SmallInteger, String, VARCHAR, Boolean, Enum, ForeignKey, CheckConstraint
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
    # Предварительные статусы, жду момента, когда распишут всё
    # process - Покупка только создалась, деньги зарезервировались, ждём подтверждения продавцом о выполнении
    # review - Продавец подтвердил выполнение, ждём подтверждения пользователя
    # completed - Покупатель подтвердил выполнение (или заказ был с автовыдачей или поддержка решила, что заказ готов)
    # dispute - Покупатель открыл спор по заказу, ждём решение администрации
    # refund - Деньги возвращаются покупателю (по желанию продавца или поддержки)
    status = Column(Enum("process", "review", "completed", "dispute", "refund", name="purchase_status"), default="process")
    # Указывает есть ли отзыв, не путать review в статусе и review - отзыв
    is_reviewed = Column(Boolean, nullable=False, default=False)

    parcels: Mapped[list["Parcel"]] = relationship(back_populates="purchase", lazy="selectin")
    review: Mapped["Review"] = relationship(back_populates="purchase", lazy="noload")
    buyer: Mapped["User"] = relationship(lazy="noload")
    offer: Mapped["Offer"] = relationship(lazy="noload")


class Parcel(Base):
    __tablename__ = "parcel"
    
    id = Column(Integer, primary_key=True)
    purchase_id = Column(Integer, ForeignKey('purchase.id', ondelete="CASCADE"))
    value = Column(VARCHAR(500))

    purchase: Mapped["Purchase"] = relationship(back_populates="parcels", lazy="noload")


class Review(Base):
    __tablename__ = "review"
    
    purchase_id = Column(Integer, ForeignKey('purchase.id', ondelete="CASCADE"), primary_key=True)
    offer_id = Column(Integer, ForeignKey('offer.id', ondelete="SET NULL"))
    rating = Column(SmallInteger, CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'), nullable=False)
    value = Column(VARCHAR(4096), nullable=True)

    purchase: Mapped["Purchase"] = relationship(back_populates="review", lazy="noload")
