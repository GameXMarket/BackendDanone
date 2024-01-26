from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship, Mapped

from core.database import Base

if TYPE_CHECKING:
    from app.messages.models import ChatMember


class Chat(Base):
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True)
    created_at = Column(Integer)
    
    members: Mapped[list["ChatMember"]] = relationship(back_populates="chat", lazy="noload")
