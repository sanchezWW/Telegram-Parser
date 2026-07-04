"""Создание таблиц в базе данных через SQLAlchemy (альтернатива sql/init_database.sql)."""

from app.database.models import Channel, Message, MessageReaction, ParseJob  # noqa: F401
from app.database.session import Base, engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы (или уже существуют).")


if __name__ == "__main__":
    init_db()
