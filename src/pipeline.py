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
    """
    Трансформация (Transform) данных.
    Очистка, разделение на справочники и таблицу фактов.
    """
    logger.info("Начинаем трансформацию данных...")
    pass
    return {}


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
