import os
from typing import Generator

import pandas as pd
import pytest
from sqlalchemy.engine import Engine, make_url

from src.database import Base, create_db_engine

TEST_DATABASE_NAME = "transactions_test"


@pytest.fixture
def raw_transactions_df() -> pd.DataFrame:
    """Raw data that mimics the operations.xlsx file."""
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
    """Empty dataframe for testing extract."""
    return pd.DataFrame()


@pytest.fixture
def test_engine() -> Generator[Engine, None, None]:
    """Create an isolated SQLAlchemy engine for tests."""
    database_url = os.getenv("TEST_DATABASE_URL")

    if not database_url:
        pytest.fail(
            "The TEST_DATABASE_URL environment variable is not set.",
            pytrace=False,
        )

    parsed_url = make_url(database_url)

    if parsed_url.get_backend_name() != "postgresql":
        pytest.fail(
            "Tests must run against PostgreSQL.",
            pytrace=False,
        )

    if parsed_url.database != TEST_DATABASE_NAME:
        pytest.fail(
            f"Tests are only allowed to use the database "
            f"'{TEST_DATABASE_NAME}'. Got '{parsed_url.database}'.",
            pytrace=False,
        )

    db_engine = create_db_engine(database_url)

    try:
        # Local import so that SQLAlchemy registers the models before creating tables
        from src import models  # noqa: F401

        # Drop the previous schema and create the tables again
        Base.metadata.drop_all(bind=db_engine)
        Base.metadata.create_all(bind=db_engine)

        yield db_engine

    finally:
        try:
            # Drop the test tables after the test
            Base.metadata.drop_all(bind=db_engine)
        finally:
            # Close all connections of the test engine
            db_engine.dispose()
