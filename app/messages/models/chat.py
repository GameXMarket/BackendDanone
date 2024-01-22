from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from datetime import datetime

from core.database import Base
from app.users.models import User


class Chat(Base):
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True)
    created_at = Column(Integer)
    
    members: Mapped[list["ChatMember"]] = relationship(back_populates="chat", lazy="noload")


class ChatMember(Base):
    __tablename__ = 'chat_member'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chat.id', ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"))

    chat: Mapped[Chat] = relationship(back_populates='members', lazy="noload")
    user: Mapped[User] = relationship(lazy="noload")
