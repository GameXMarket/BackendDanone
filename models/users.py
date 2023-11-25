from sqlalchemy import Column, Integer, String, Boolean

from core.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, unique=True, nullable=False)
    email = Column(String, index=True, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role_id = Column(Integer, default=0, nullable=False) # 0-user, 1-mod, 2-arbit, 3-admin
    created_at = Column(Integer, nullable=False)  # Unix - time

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}    
