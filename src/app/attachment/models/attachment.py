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
# https://docs.sqlalchemy.org/en/14/orm/inheritance.html#joined-table-inheritance


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
    author_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))

    files: Mapped[list["File"]] = relationship(lazy="selectin")


class File(Base):
    """
    Путь файла находится через created_at параметр + hash
    """
    __tablename__ = "file"
    id = Column(Integer, primary_key=True)
    attachment_id = Column(
        Integer, ForeignKey("base_attachment.id", ondelete="CASCADE")
    )
    hash = Column(String)
    name = Column(String)
    type = Column(String)


class DeletedFile(Base):
    """
    Хранит записи файлов, которые требуется удалить
    """
    __tablename__ = "deleted_file"
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    created_at = Column(Integer)


delete_from_base_attachment_sql_func = """
CREATE OR REPLACE FUNCTION delete_from_base_attachment()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM base_attachment WHERE id = OLD.id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""


create_deleted_file_sql_func = """
CREATE OR REPLACE FUNCTION create_deleted_file()
RETURNS TRIGGER AS $$
DECLARE
    payload TEXT;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM file WHERE hash = OLD.hash) THEN
        INSERT INTO deleted_file (id, hash, created_at, updated_at)
        VALUES (OLD.id, OLD.hash, OLD.created_at, -1);
		payload := json_build_object('unix', OLD.created_at, 'hash', OLD.hash, 'type', OLD.type);
        PERFORM pg_notify('new_deleted_file', payload);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""


def __create_trigger(
    connection: sqlalchemy.engine.base.Connection, trigger_name: str, table_name: str, function_name: str
):
    trigger_sql = f"""
    CREATE OR REPLACE TRIGGER {trigger_name}_trigger
    AFTER DELETE ON {table_name}
    FOR EACH ROW EXECUTE FUNCTION {function_name}();
    """
    connection.execute(text(trigger_sql))


@event.listens_for(Attachment.__table__, "after_create")
def create_attachment_trigger(
    target: Attachment.__table__, connection: sqlalchemy.engine.base.Connection, **kw
):
    connection.execute(text(delete_from_base_attachment_sql_func))


@event.listens_for(DeletedFile.__table__, "after_create")
def create_attachment_trigger(
    target: Attachment.__table__, connection: sqlalchemy.engine.base.Connection, **kw
):
    connection.execute(text(create_deleted_file_sql_func))


@event.listens_for(File.__table__, "after_create")
def create_message_attachment_trigger(
    target: File.__table__,
    connection: sqlalchemy.engine.base.Connection,
    **kw,
):
    __create_trigger(connection, "file_after_delete", "file", "create_deleted_file")
