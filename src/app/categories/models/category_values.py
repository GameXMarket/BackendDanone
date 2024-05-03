from typing import List, TYPE_CHECKING

from sqlalchemy import Column, Integer, Boolean, VARCHAR, ForeignKey
from sqlalchemy.orm import validates, relationship, Mapped

from core.database import Base
from app.users.models import User

if TYPE_CHECKING:
    from .category_carcasses import CategoryCarcass


class CategoryValue(Base):
    """
    Значения, привязанные к каркассу категории
    """

    __tablename__ = "category_value"
    id = Column(Integer, primary_key=True, index=True)
    carcass_id = Column(
        Integer, ForeignKey("category_carcass.id", ondelete="CASCADE"), nullable=False
    )
    next_carcass_id = Column(
        Integer, ForeignKey("category_carcass.id", ondelete="SET NULL"), nullable=True
    )
    author_id = Column(
        Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    value = Column(VARCHAR(length=17), nullable=False)
    is_offer_with_delivery = Column(Boolean, nullable=False, default=False)

    carcass: Mapped["CategoryCarcass"] = relationship(
        lazy="noload", back_populates="values", foreign_keys=[carcass_id]
    )
    next_carcass: Mapped["CategoryCarcass"] = relationship(
        lazy="noload", foreign_keys=[next_carcass_id]
    )
    author: Mapped[User] = relationship(lazy="noload")

    def to_dict(self, *args):
        base_dict = {}
        lazy_load_v = ["carcass", "next_carcass", "author"]
        for var_name in args:
            if var_name is None:
                continue

            var_value = getattr(self, var_name)
            base_dict[var_name] = (
                var_value.to_dict() if var_name in lazy_load_v else var_value
            )

        return super().to_dict(base_dict)
