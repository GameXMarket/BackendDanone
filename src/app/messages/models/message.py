from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped

from core.database import Base
from app.users.models import User


class Chat(Base):
    __tablename__ = 'chat'
    
    id = Column(Integer, primary_key=True)
    is_dialog = Column(Boolean, default=True)


class ChatMember(Base):
    __tablename__ = 'chat_member'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    chat_id = Column(Integer, ForeignKey('chat.id', ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'chat_id', name='uq_user_chat'),)


class Message(Base):
    __tablename__ = 'message'

    id = Column(Integer, primary_key=True)
    chat_member_id = Column(Integer, ForeignKey('chat_member.id', ondelete="CASCADE"), nullable=False)
    content = Column(String)


class SystemMessage(Base):
    __tablename__ = 'system_message'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chat.id", ondelete="CASCADE"), nullable=False)
    content = Column(String, nullable=False)
    
