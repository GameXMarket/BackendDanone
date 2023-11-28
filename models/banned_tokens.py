from sqlalchemy import Column, Integer, String, Boolean

from core.database import Base


class BannedToken(Base):
    """
    JWT Tokens Blacklist, тут банятся jwt токены
    При БОЛЬШИНСТВЕ запросов сюда будет лететь exist
    """

    __tablename__ = "banned_token"
    id = Column(Integer, primary_key=True, index=True)
    session = Column(String, unique=True, nullable=False, index=True)
    expired_at = Column(Integer, nullable=False, index=True)  # ! need ms

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
