from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from core.database import Base
from app.users.models import User


## Добавить ограничения стринга на длину (varchar) относится не только к данной таблице


class Offer(Base):
    __tablename__ = "offer"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))  # ForeignKey to user_id
    attachment_id = Column(Integer)  # ForeignKey to attachment_id
    category_id = Column(Integer)  # ForeignKey to category_id in a new table
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    count = Column(Integer, nullable=False)
    status = Column(Enum('active', 'hidden', 'deleted', name="offer_statuses"), nullable=False)
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)
    upped_at = Column(Integer, nullable=False)
    
    user: Mapped["User"] = relationship("User", back_populates="offers", lazy="noload")
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
