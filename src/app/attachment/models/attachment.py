from sqlalchemy import text, event, Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship, Mapped
import sqlalchemy

from core.database import Base
from app.users.models import User


"""
https://ru.stackoverflow.com/questions/1430715/Наследование-и-Полиморфизм-в-реляционных-БД-sql

1.1. TPC: Table-Per-Concrete
Каждый класс-наследник имеет собственную независимую таблицу, в которой продублированы все поля классов-родителей.


1.2. TPT: Table-Per-Type
Наследование через композицию (в духе Composition over inheritance), 
где дети ссылаются на родителя, и в идеале имеют одинаковый Primary Key. 
В этом случае данные одного экземпляра класса будут физически разделены 
в разных таблицах, и извлечение всех полей объекта потребует JOIN-запроса.


1.3. TPH: Table-Per-Hierarchy
Таблица на всю иерархию, т.е, одна таблица на все классы A, B и
прочих возможных наследников. При этом, поля, не релевантные для типа 
текущей строчки/объекта, будут иметь значения NULL, а общие поля верхнего 
родителя можно пометить как NOT NULL. Этот вариант уместен, когда классов 
в иерархии или их уникальных полей не много. Опционально можно завести
таблицу с описанием подтипов чтобы обеспечить их валидность.
"""


# base class of Joined Table Inheritance
# https://docs.sqlalchemy.org/en/14/orm/inheritance.html#joined-table-inheritance
class Attachment(Base):
    """
    id - первичный ключ, в наследниках является одновременно
     первичным и вторичным.
    entity_type - перечисление для идентификации таблиц-наследников
    """

    __tablename__ = "base_attachment"
    id = Column(Integer, primary_key=True)
    entity_type = Column(
        Enum(
            "base_attachment",
            "user_attacment",
            "message_attacment",
            "offer_attacment",
            "conflict_attacment",
            name="attachment_types",
        )
    )

    files: Mapped[list["File"]] = relationship(lazy="selectin")

    __mapper_args__ = {
        "polymorphic_identity": "base_attachment",
        "polymorphic_on": entity_type,
    }


class UserAttachment(Attachment):
    __tablename__ = "user_attacment"
    id = Column(Integer, ForeignKey("base_attachment.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), unique=True)

    __mapper_args__ = {
        "polymorphic_identity": "user_attacment",
    }


class MessageAttachment(Attachment):
    __tablename__ = "message_attacment"
    id = Column(Integer, ForeignKey("base_attachment.id"), primary_key=True)
    message_id = Column(
        Integer, ForeignKey("message.id", ondelete="CASCADE"), unique=True
    )

    __mapper_args__ = {
        "polymorphic_identity": "message_attacment",
    }


class OfferAttachment(Attachment):
    __tablename__ = "offer_attacment"
    id = Column(Integer, ForeignKey("base_attachment.id"), primary_key=True)
    offer = Column(Integer, ForeignKey("offer.id", ondelete="CASCADE"), unique=True)

    __mapper_args__ = {
        "polymorphic_identity": "offer_attacment",
    }


"""
class ConflictAttachment(Attachment):
    __tablename__ = "conflict_attacment"
    id = Column(Integer, ForeignKey("attachment.id"), primary_key=True)
    conflict_id = Column(Integer, ForeignKey("conflict.id", ondelete="CASCADE"), unique=True)

    __mapper_args__ = {
        "polymorphic_identity": "conflict_attacment",
    }
"""


class File(Base):
    __tablename__ = "file"
    id = Column(Integer, primary_key=True)
    attachment_id = Column(Integer, ForeignKey("base_attachment.id", ondelete="CASCADE"))
    file_name = Column(String)
    file_type = Column(String)
    created_at = Column(Integer)


@event.listens_for(Attachment.__table__, "after_create")
def create_trigger(
    target: Attachment.__table__, connection: sqlalchemy.engine.base.Connection, **kw
):
    pass
