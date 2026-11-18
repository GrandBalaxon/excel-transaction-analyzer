import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.database import engine, init_db

logger = logging.getLogger("pipeline")


def extract(file_path: Path) -> pd.DataFrame | None:
    """
    Извлечение (Extract) данных из Excel-файла.
    """
    logger.info(f"Начинаем чтение файла: {file_path}")
    try:
        df = pd.read_excel(file_path)

        if df.empty:
            logger.warning("Файл пуст.")
            return None

        logger.info(f"Успешно прочитано {len(df)} строк.")
        return df
    except FileNotFoundError:
        logger.error(f"Файл не найден: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при чтении Excel: {e}")
        return None


def transform(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Трансформация (Transform) данных."""
    logger.info("Начинаем трансформацию данных...")

    # 1. Очистка: убираем FAILED и дубликаты
    df = df[df["Статус"] == "OK"].copy()
    df = df.drop_duplicates()
    logger.info(f"Осталось {len(df)} строк после фильтрации (OK).")

    # 2. Очистка типов данных
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    df["Кэшбэк"] = df["Кэшбэк"].fillna(0.0)
    df["Номер карты"] = df["Номер карты"].fillna("Unknown")
    df["Категория"] = df["Категория"].fillna("Unknown")

    # 3. Создаем справочник DimCard
    dim_cards = df[["Номер карты"]].drop_duplicates().rename(columns={"Номер карты": "card_id"})
    dim_cards["last_digits"] = dim_cards["card_id"].apply(
        lambda x: x.replace("*", "") if x != "Unknown" else "0000"
    )

    # 4. Создаем справочник DimCategory
    dim_categories = df[["Категория"]].drop_duplicates().rename(columns={"Категория": "name"})

    # 5. Создаем справочник DimDate
    df["date_id"] = df["Дата операции"].dt.date
    dim_dates = df[["date_id"]].drop_duplicates()
    dim_dates["year"] = pd.to_datetime(dim_dates["date_id"]).dt.year
    dim_dates["month"] = pd.to_datetime(dim_dates["date_id"]).dt.month
    dim_dates["day"] = pd.to_datetime(dim_dates["date_id"]).dt.day
    dim_dates["weekday"] = pd.to_datetime(dim_dates["date_id"]).dt.weekday

    # 6. Создаем таблицу фактов FactTransaction
    facts = df[
        [
            "date_id",
            "Номер карты",
            "Категория",
            "Сумма операции",
            "Валюта операции",
            "Сумма платежа",
            "Валюта платежа",
            "Кэшбэк",
            "Статус",
            "Описание",
        ]
    ].copy()

    facts.rename(
        columns={
            "Номер карты": "card_id",
            "Категория": "category_name",
            "Сумма операции": "amount",
            "Валюта операции": "currency_code",
            "Сумма платежа": "payment_amount",
            "Валюта платежа": "payment_currency_code",
            "Кэшбэк": "cashback",
            "Статус": "status",
            "Описание": "description",
        },
        inplace=True,
    )

    # 7. Рассчитываем сумму операции в рублях
    facts["amount_rub"] = None

    payment_rub_mask = facts["payment_currency_code"] == "RUB"
    operation_rub_mask = (
        (facts["currency_code"] == "RUB") & ~payment_rub_mask
    )
    facts.loc[payment_rub_mask, "amount_rub"] = facts.loc[
        payment_rub_mask, "payment_amount"
    ]
    facts.loc[operation_rub_mask, "amount_rub"] = facts.loc[
        operation_rub_mask, "amount"
    ]

    logger.info("Трансформация завершена. Данные готовы к загрузке.")

    return {
        "dim_cards": dim_cards,
        "dim_categories": dim_categories,
        "dim_dates": dim_dates,
        "facts": facts
    }


def load(tables: dict[str, pd.DataFrame], db_engine: Engine) -> None:
    """Загрузка (Load) данных в PostgreSQL."""
    logger.info("Начинаем загрузку в PostgreSQL...")

    with db_engine.begin() as conn:
        conn.execute(
            text("TRUNCATE TABLE fact_transactions, dim_dates, dim_cards, dim_categories RESTART IDENTITY CASCADE;")
        )
    logger.info("Старые данные в таблицах очищены.")

    tables["dim_cards"].to_sql("dim_cards", db_engine, if_exists="append", index=False)
    tables["dim_categories"].to_sql("dim_categories", db_engine, if_exists="append", index=False)
    tables["dim_dates"].to_sql("dim_dates", db_engine, if_exists="append", index=False)
    logger.info("Справочники (карты, категории, даты) успешно загружены.")

    categories_db = pd.read_sql('SELECT category_id, name FROM dim_categories', db_engine)

    facts = tables["facts"].merge(categories_db, left_on='category_name', right_on='name')
    facts = facts.drop(columns=['category_name', 'name'])

    facts.to_sql("fact_transactions", db_engine, if_exists="append", index=False)
    logger.info(f"Успешно загружено {len(facts)} строк в fact_transactions.")


def run_pipeline(file_path: Path, db_engine: Engine | None = None) -> None:
    """Точка входа для запуска всего ETL-процесса."""
    logger.info("=== ЗАПУСК ETL-ПАЙПЛАЙНА ===")

    # Используем переданный Engine или production Engine по умолчанию
    target_engine = db_engine if db_engine is not None else engine

    # 0. Начальное создание таблиц
    init_db(target_engine)

    # 1. Extract
    df = extract(file_path)
    if df is None:
        logger.error("Пайплайн прерван: не удалось извлечь данные.")
        return

    # 2. Transform
    transformed_data = transform(df)

    # 3. Load
    if transformed_data:
        load(transformed_data, target_engine)

    logger.info("=== ETL-ПАЙПЛАЙН ЗАВЕРШЕН ===")
