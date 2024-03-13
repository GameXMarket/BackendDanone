from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from core.database import Base
from app.users.models import User


class Chat(Base):
    __tablename__ = 'chat'
    
    id = Column(Integer, primary_key=True)


class ChatMember(Base):
    __tablename__ = 'chat_member'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    chat_id = Column(Integer, ForeignKey('chat.id', ondelete="CASCADE"), nullable=False)


class Message(Base):
    __tablename__ = 'message'

    id = Column(Integer, primary_key=True)
    chat_member = Column(Integer, ForeignKey('chat_member.id', ondelete="CASCADE"), nullable=False)
    content = Column(String)
    created_at = Column(Integer)


