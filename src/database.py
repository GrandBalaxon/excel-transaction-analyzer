import logging
import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger("database")

load_dotenv()

# Получаем данные для подключения
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "transactions_db")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5433")

# Формируем строку подключения (URL)
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создаем движок (Engine)
try:
    engine = create_engine(DATABASE_URL, echo=False)
    logger.info("Движок SQLAlchemy успешно создан.")
except Exception as e:
    logger.error(f"Ошибка при создании движка: {e}")
    raise

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Базовый класс для будущих моделей (таблиц)."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Вспомогательная функция для получения сессии БД."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Создает все таблицы в базе данных, если они еще не созданы."""
    # Локальный импорт, чтобы SQLAlchemy "увидел" модели перед созданием таблиц
    from src import models # noqa: F401

    logger.info("Инициализация схемы БД (создание таблиц)...")
    Base.metadata.create_all(bind=engine)
