import logging
from pathlib import Path

import pandas as pd
from sqlalchemy.engine import Engine

from src.database import engine

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
    facts = df[[
        "date_id", "Номер карты", "Категория",
        "Сумма операции с округлением", "Кэшбэк", "Статус", "Описание"
    ]].copy()

    facts.rename(columns={
        "Номер карты": "card_id",
        "Категория": "category_name",
        "Сумма операции с округлением": "amount",
        "Кэшбэк": "cashback",
        "Статус": "status",
        "Описание": "description"
    }, inplace=True)

    logger.info("Трансформация завершена. Данные готовы к загрузке.")

    return {
        "dim_cards": dim_cards,
        "dim_categories": dim_categories,
        "dim_dates": dim_dates,
        "facts": facts
    }


def load(tables: dict[str, pd.DataFrame], db_engine: Engine) -> None:
    """Загрузка (Load) данных в PostgreSQL."""
    logger.info("Начинаем загрузку данных в базу...")
    pass


def run_pipeline(file_path: Path) -> None:
    """Точка входа для запуска всего ETL-процесса."""
    logger.info("=== ЗАПУСК ETL-ПАЙПЛАЙНА ===")

    # 1. Extract
    df = extract(file_path)
    if df is None:
        logger.error("Пайплайн прерван: не удалось извлечь данные.")
        return

    # 2. Transform
    transformed_data = transform(df)

    # 3. Load
    if transformed_data:
        load(transformed_data, engine)

    logger.info("=== ETL-ПАЙПЛАЙН ЗАВЕРШЕН ===")


if __name__ == "__main__":
    file_path = Path(__file__).parent.parent / "data" / "operations.xlsx"
    run_pipeline(file_path)
