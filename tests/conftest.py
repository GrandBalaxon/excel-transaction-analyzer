import os
from typing import Generator

import pandas as pd
import pytest
from sqlalchemy.engine import Engine, make_url

from src.database import Base, create_db_engine

TEST_DATABASE_NAME = "transactions_test"


@pytest.fixture
def raw_transactions_df() -> pd.DataFrame:
    """Сырые данные, имитирующие Excel-файл operations.xlsx."""
    return pd.DataFrame({
        "Дата операции": [
            "31.12.2021 16:44:00",
            "31.12.2021 16:42:04",
            "14.11.2021 14:46:24"
        ],
        "Номер карты": ["*7197", "*4556", "*4556"],
        "Статус": ["OK", "OK", "FAILED"],
        "Сумма операции": [-160.89, -64.0, -55.0],
        "Валюта операции": ["RUB", "RUB", "RUB"],
        "Сумма платежа": [-160.89, -64.0, -55.0],
        "Валюта платежа": ["RUB", "RUB", "RUB"],
        "Кэшбэк": [1.0, None, 0.0],
        "Категория": ["Супермаркеты", "Развлечения", "Переводы"],
        "Описание": ["Колхоз", "Кино", "Перевод на карту"]
    })


@pytest.fixture
def empty_dataframe() -> pd.DataFrame:
    """Пустой датафрейм для проверки extract."""
    return pd.DataFrame()


@pytest.fixture
def test_engine() -> Generator[Engine, None, None]:
    """Создаёт изолированный движок SQLAlchemy для тестирования."""
    database_url = os.getenv("TEST_DATABASE_URL")

    if not database_url:
        pytest.fail(
            "Переменная окружения TEST_DATABASE_URL не задана.",
            pytrace=False,
        )

    parsed_url = make_url(database_url)

    if parsed_url.get_backend_name() != "postgresql":
        pytest.fail(
            "Для тестирования необходимо использовать PostgreSQL.",
            pytrace=False,
        )

    if parsed_url.database != TEST_DATABASE_NAME:
        pytest.fail(
            f"Тестирование разрешено только для базы данных "
            f"'{TEST_DATABASE_NAME}'. Указана база '{parsed_url.database}'.",
            pytrace=False,
        )

    db_engine = create_db_engine(database_url)

    try:
        # Локальный импорт, чтобы SQLAlchemy "увидел" модели перед созданием таблиц
        from src import models  # noqa: F401

        # Удаляем предыдущую схему и создаём таблицы заново
        Base.metadata.drop_all(bind=db_engine)
        Base.metadata.create_all(bind=db_engine)

        yield db_engine

    finally:
        try:
            # Удаляем тестовые таблицы после завершения теста
            Base.metadata.drop_all(bind=db_engine)
        finally:
            # Закрываем все соединения тестового движка
            db_engine.dispose()
