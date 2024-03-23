from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from core.database import Base
from app.users.models import User


class Message(Base):
    __tablename__ = 'message'

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    receiver_id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    reply_to = Column(Integer, ForeignKey('message.id', ondelete="SET NULL"), nullable=True)
    content = Column(String)
    created_at = Column(Integer)
    
    sender: Mapped[User] = relationship(lazy="noload", foreign_keys=[sender_id])
    receiver: Mapped[User] = relationship(lazy="noload", foreign_keys=[receiver_id])
