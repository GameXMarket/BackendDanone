from sqlalchemy import Column, Integer, String, Text, Enum

from core.database import Base
from app.users.models import User


class Offer(Base):
    __tablename__ = "offer" ## Добавить ограничения стринга на длину (varchar) относится не только к данной таблице
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # ForeignKey to user_id
    attachment_id = Column(Integer)  # ForeignKey to attachment_id
    category = Column(Integer, nullable=False)  # ForeignKey to category_id in a new table
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    status = Column(String, nullable=False) 
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)
    upped_at = Column(Integer)
    count = Column(Integer, nullable=False)
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
