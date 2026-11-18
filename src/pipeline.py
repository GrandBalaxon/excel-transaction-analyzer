import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.database import engine, init_db

logger = logging.getLogger("pipeline")


def extract(file_path: Path) -> pd.DataFrame | None:
    """
    Extract data from an Excel file.
    """
    logger.info(f"Reading file: {file_path}")
    try:
        df = pd.read_excel(file_path)

        if df.empty:
            logger.warning("The file is empty.")
            return None

        logger.info(f"Read {len(df)} rows.")
        return df
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Failed to read the Excel file: {e}")
        return None


def transform(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Transform raw data into dimension and fact tables."""
    logger.info("Transforming data...")

    # 1. Cleaning: drop FAILED operations and duplicates
    df = df[df["Статус"] == "OK"].copy()
    df = df.drop_duplicates()
    logger.info(f"{len(df)} rows left after filtering (status OK).")

    # 2. Fix data types and fill missing values
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    df["Кэшбэк"] = df["Кэшбэк"].fillna(0.0)
    df["Номер карты"] = df["Номер карты"].fillna("Unknown")
    df["Категория"] = df["Категория"].fillna("Unknown")

    # 3. Build the DimCard dimension
    dim_cards = df[["Номер карты"]].drop_duplicates().rename(columns={"Номер карты": "card_id"})
    dim_cards["last_digits"] = dim_cards["card_id"].apply(
        lambda x: x.replace("*", "") if x != "Unknown" else "0000"
    )

    # 4. Build the DimCategory dimension
    dim_categories = df[["Категория"]].drop_duplicates().rename(columns={"Категория": "name"})

    # 5. Build the DimDate dimension
    df["date_id"] = df["Дата операции"].dt.date
    dim_dates = df[["date_id"]].drop_duplicates()
    dim_dates["year"] = pd.to_datetime(dim_dates["date_id"]).dt.year
    dim_dates["month"] = pd.to_datetime(dim_dates["date_id"]).dt.month
    dim_dates["day"] = pd.to_datetime(dim_dates["date_id"]).dt.day
    dim_dates["weekday"] = pd.to_datetime(dim_dates["date_id"]).dt.weekday

    # 6. Build the FactTransaction fact table
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

    # 7. Calculate the transaction amount in rubles
    operation_amount_rub = facts["amount"].where(facts["currency_code"] == "RUB")
    facts["amount_rub"] = facts["payment_amount"].where(
        facts["payment_currency_code"] == "RUB",
        operation_amount_rub
    )

    logger.info("Transformation finished. Data is ready to load.")

    return {
        "dim_cards": dim_cards,
        "dim_categories": dim_categories,
        "dim_dates": dim_dates,
        "facts": facts
    }


def load(tables: dict[str, pd.DataFrame], db_engine: Engine) -> None:
    """Load the tables into PostgreSQL."""
    logger.info("Loading data into PostgreSQL...")

    with db_engine.begin() as conn:
        conn.execute(
            text("TRUNCATE TABLE fact_transactions, dim_dates, dim_cards, dim_categories RESTART IDENTITY CASCADE;")
        )
    logger.info("Existing data removed from the tables.")

    tables["dim_cards"].to_sql("dim_cards", db_engine, if_exists="append", index=False)
    tables["dim_categories"].to_sql("dim_categories", db_engine, if_exists="append", index=False)
    tables["dim_dates"].to_sql("dim_dates", db_engine, if_exists="append", index=False)
    logger.info("Dimensions (cards, categories, dates) loaded.")

    categories_db = pd.read_sql('SELECT category_id, name FROM dim_categories', db_engine)

    facts = tables["facts"].merge(categories_db, left_on='category_name', right_on='name')
    facts = facts.drop(columns=['category_name', 'name'])

    facts.to_sql("fact_transactions", db_engine, if_exists="append", index=False)
    logger.info(f"Loaded {len(facts)} rows into fact_transactions.")


def run_pipeline(file_path: Path, db_engine: Engine | None = None) -> None:
    """Run the whole ETL process."""
    logger.info("=== ETL PIPELINE STARTED ===")

    # Use the given engine or fall back to the production engine
    target_engine = db_engine if db_engine is not None else engine

    # 0. Create tables if needed
    init_db(target_engine)

    # 1. Extract
    df = extract(file_path)
    if df is None:
        logger.error("Pipeline aborted: failed to extract data.")
        return

    # 2. Transform
    transformed_data = transform(df)

    # 3. Load
    if transformed_data:
        load(transformed_data, target_engine)

    logger.info("=== ETL PIPELINE FINISHED ===")
