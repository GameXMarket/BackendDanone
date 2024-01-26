from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from core.database import Base
from app.users.models import User
from app.messages.models import Chat


class ChatMember(Base):
    __tablename__ = 'chat_member'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chat.id', ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"))

    chat: Mapped[Chat] = relationship(back_populates='members', lazy="noload")
    user: Mapped[User] = relationship(lazy="noload")
