from typing import TYPE_CHECKING, List

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship, Mapped

from core.database import Base

if TYPE_CHECKING:
    from app.offers.models import Offer


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True, unique=True, nullable=False)
    email = Column(String(75), index=True, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role_id = Column(
        Integer, default=0, nullable=False
    )  # 0-user, 1-mod, 2-arbit, 3-admin
    last_online = Column(Integer)  # Unix - time # ! need ms

    # Read about lazy arg more here:
    #  https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html
    offers: Mapped[List["Offer"]] = relationship(back_populates="user", lazy="noload")
    
    def is_admin(self) -> bool:
        if self.role_id == 3:
            return True
