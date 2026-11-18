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
    """Расширяет исходные тестовые данные операциями для проверки SQL-запросов."""

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
        }
    ])

    return pd.concat(
        [raw_transactions_df.copy(), additional_transactions],
        ignore_index=True
    )


@pytest.fixture
def populated_engine(test_engine: Engine, sql_transactions_df: pd.DataFrame) -> Engine:
    """Заполняет тестовую базу данными для проверки SQL-запросов."""

    # Преобразуем исходные данные в структуру таблиц PostgreSQL
    tables = transform(sql_transactions_df)

    # Загружаем данные исключительно в тестовую базу
    load(tables, test_engine)

    return test_engine


def execute_sql_query(db_engine: Engine, filename: str) -> list[tuple]:
    """Выполняет SQL-запрос из файла и возвращает результат."""

    query = (SQL_DIR / filename).read_text(encoding="utf-8")

    with db_engine.connect() as conn:
        result = conn.execute(text(query))
        return [tuple(row) for row in result.fetchall()]


def test_top_3_expenses_per_category(populated_engine: Engine) -> None:
    """Проверяет получение трех крупнейших расходов в каждой категории."""

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
    """Проверяет расчет ежедневных расходов и накопительного итога."""

    result = execute_sql_query(
        populated_engine,
        "02_running_total_expenses.sql",
    )

    expected = [
        (date(2021, 12, 1), Decimal("130.00"), Decimal("130.00")),
        (date(2021, 12, 2), Decimal("180.00"), Decimal("310.00")),
        (date(2021, 12, 4), Decimal("20.00"), Decimal("330.00")),
        (date(2021, 12, 31), Decimal("224.89"), Decimal("554.89")),
        (date(2022, 1, 1), Decimal("50.00"), Decimal("604.89")),
    ]

    assert result == expected


def test_category_share_december_2021(populated_engine: Engine) -> None:
    """Проверяет расчет доли категорий в расходах декабря 2021 года."""

    result = execute_sql_query(
        populated_engine,
        "03_category_share_december_2021.sql",
    )

    expected = [
        ("Супермаркеты", Decimal("440.89"), Decimal("79.46")),
        ("Развлечения", Decimal("114.00"), Decimal("20.54")),
    ]

    assert result == expected
