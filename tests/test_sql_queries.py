from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.pipeline import load, transform

SQL_DIR = Path(__file__).parent.parent / "sql"


@pytest.fixture
def sql_transactions_df(raw_transactions_df: pd.DataFrame) -> pd.DataFrame:
    """Extend the base test data with operations for testing SQL queries."""

    additional_transactions = pd.DataFrame([
        {
            "Дата операции": "01.12.2021 10:00:00",
            "Номер карты": "*7197",
            "Статус": "OK",
            "Сумма операции": -100.0,
            "Валюта операции": "RUB",
            "Сумма платежа": -100.0,
            "Валюта платежа": "RUB",
            "Кэшбэк": 1.0,
            "Категория": "Супермаркеты",
            "Описание": "Покупка продуктов 100"
        },
        {
            "Дата операции": "02.12.2021 10:00:00",
            "Номер карты": "*7197",
            "Статус": "OK",
            "Сумма операции": -80.0,
            "Валюта операции": "RUB",
            "Сумма платежа": -80.0,
            "Валюта платежа": "RUB",
            "Кэшбэк": 0.8,
            "Категория": "Супермаркеты",
            "Описание": "Покупка продуктов 80"
        },
        {
            "Дата операции": "02.12.2021 11:00:00",
            "Номер карты": "*4556",
            "Статус": "OK",
            "Сумма операции": -60.0,
            "Валюта операции": "RUB",
            "Сумма платежа": -60.0,
            "Валюта платежа": "RUB",
            "Кэшбэк": 0.6,
            "Категория": "Супермаркеты",
            "Описание": "Покупка продуктов 60"
        },
        {
            "Дата операции": "02.12.2021 12:00:00",
            "Номер карты": "*4556",
            "Статус": "OK",
            "Сумма операции": -40.0,
            "Валюта операции": "RUB",
            "Сумма платежа": -40.0,
            "Валюта платежа": "RUB",
            "Кэшбэк": 0.4,
            "Категория": "Супермаркеты",
            "Описание": "Покупка продуктов 40"
        },
        {
            "Дата операции": "03.12.2021 10:00:00",
            "Номер карты": "*7197",
            "Статус": "OK",
            "Сумма операции": 500.0,
            "Валюта операции": "RUB",
            "Сумма платежа": 500.0,
            "Валюта платежа": "RUB",
            "Кэшбэк": 0.0,
            "Категория": "Супермаркеты",
            "Описание": "Зачисление"
        },
        {
            "Дата операции": "01.01.2022 10:00:00",
            "Номер карты": "*7197",
            "Статус": "OK",
            "Сумма операции": -50.0,
            "Валюта операции": "RUB",
            "Сумма платежа": -50.0,
            "Валюта платежа": "RUB",
            "Кэшбэк": 0.5,
            "Категория": "Супермаркеты",
            "Описание": "Покупка продуктов январь"
        },
        {
            "Дата операции": "01.12.2021 12:00:00",
            "Номер карты": "*4556",
            "Статус": "OK",
            "Сумма операции": -30.0,
            "Валюта операции": "RUB",
            "Сумма платежа": -30.0,
            "Валюта платежа": "RUB",
            "Кэшбэк": 0.3,
            "Категория": "Развлечения",
            "Описание": "Билет в кино"
        },
        {
            "Дата операции": "04.12.2021 14:00:00",
            "Номер карты": "*4556",
            "Статус": "OK",
            "Сумма операции": -20.0,
            "Валюта операции": "RUB",
            "Сумма платежа": -20.0,
            "Валюта платежа": "RUB",
            "Кэшбэк": 0.2,
            "Категория": "Развлечения",
            "Описание": "Развлечение 20"
        },
        {
            "Дата операции": "04.12.2021 15:00:00",
            "Номер карты": "*4556",
            "Статус": "OK",
            "Сумма операции": 200.0,
            "Валюта операции": "RUB",
            "Сумма платежа": 200.0,
            "Валюта платежа": "RUB",
            "Кэшбэк": 0.0,
            "Категория": "Развлечения",
            "Описание": "Возврат"
        },
        # Operation in USD, payment in RUB
        {
            "Дата операции": "05.12.2021 10:00:00",
            "Номер карты": "*7197",
            "Статус": "OK",
            "Сумма операции": -50.0,
            "Валюта операции": "USD",
            "Сумма платежа": -45.0,
            "Валюта платежа": "RUB",
            "Кэшбэк": 0.0,
            "Категория": "Супермаркеты",
            "Описание": "Валютная операция USD"
        },
        # Operation in RUB, payment in CNY
        {
            "Дата операции": "05.12.2021 11:00:00",
            "Номер карты": "*7197",
            "Статус": "OK",
            "Сумма операции": -40.0,
            "Валюта операции": "RUB",
            "Сумма платежа": -300.0,
            "Валюта платежа": "CNY",
            "Кэшбэк": 0.0,
            "Категория": "Супермаркеты",
            "Описание": "Валютная операция RUB"
        },
        # Operation and payment in CNY
        {
            "Дата операции": "05.12.2021 12:00:00",
            "Номер карты": "*7197",
            "Статус": "OK",
            "Сумма операции": -35.0,
            "Валюта операции": "CNY",
            "Сумма платежа": -35.0,
            "Валюта платежа": "CNY",
            "Кэшбэк": 0.0,
            "Категория": "Супермаркеты",
            "Описание": "Валютная операция CNY"
        }
    ])

    return pd.concat(
        [raw_transactions_df.copy(), additional_transactions],
        ignore_index=True
    )


@pytest.fixture
def populated_engine(test_engine: Engine, sql_transactions_df: pd.DataFrame) -> Engine:
    """Fill the test database with data for testing SQL queries."""

    # Transform the raw data into the PostgreSQL table structure
    tables = transform(sql_transactions_df)

    # Load the data into the test database only
    load(tables, test_engine)

    return test_engine


def execute_sql_query(db_engine: Engine, filename: str) -> list[tuple]:
    """Run a SQL query from a file and return the result."""

    query = (SQL_DIR / filename).read_text(encoding="utf-8")

    with db_engine.connect() as conn:
        result = conn.execute(text(query))
        return [tuple(row) for row in result.fetchall()]


def test_top_3_expenses_per_category(populated_engine: Engine) -> None:
    """Check the three largest expenses in each category."""

    result = execute_sql_query(
        populated_engine,
        "01_top_3_expenses_per_category.sql",
    )

    expected = [
        ("Развлечения", "Кино", Decimal("64.00")),
        ("Развлечения", "Билет в кино", Decimal("30.00")),
        ("Развлечения", "Развлечение 20", Decimal("20.00")),
        ("Супермаркеты", "Колхоз", Decimal("160.89")),
        ("Супермаркеты", "Покупка продуктов 100", Decimal("100.00")),
        ("Супермаркеты", "Покупка продуктов 80", Decimal("80.00")),
    ]

    assert result == expected


def test_running_total_expenses(populated_engine: Engine) -> None:
    """Check daily expenses and the running total."""

    result = execute_sql_query(
        populated_engine,
        "02_running_total_expenses.sql",
    )

    expected = [
        (date(2021, 12, 1), Decimal("130.00"), Decimal("130.00")),
        (date(2021, 12, 2), Decimal("180.00"), Decimal("310.00")),
        (date(2021, 12, 4), Decimal("20.00"), Decimal("330.00")),
        (date(2021, 12, 5), Decimal("85.00"), Decimal("415.00")),
        (date(2021, 12, 31), Decimal("224.89"), Decimal("639.89")),
        (date(2022, 1, 1), Decimal("50.00"), Decimal("689.89")),
    ]

    assert result == expected


def test_category_share_december_2021(populated_engine: Engine) -> None:
    """Check the share of each category in December 2021 expenses."""

    result = execute_sql_query(
        populated_engine,
        "03_category_share_december_2021.sql",
    )

    expected = [
        ("Супермаркеты", Decimal("525.89"), Decimal("82.18")),
        ("Развлечения", Decimal("114.00"), Decimal("17.82")),
    ]

    assert result == expected
