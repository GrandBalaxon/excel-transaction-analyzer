from decimal import Decimal
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.pipeline import run_pipeline


def test_run_pipeline_end_to_end(
        test_engine: Engine,
        tmp_path: Path,
        raw_transactions_df: pd.DataFrame,
) -> None:
    """Проверяет полный цикл ETL: от чтения Excel до записи в PostgreSQL."""

    # Создаем временный Excel-файл на основе тестовых данных
    file_path = tmp_path / "test_operations.xlsx"
    raw_transactions_df.to_excel(file_path, index=False)

    # Запускаем пайплайн с использованием тестовой базы данных
    run_pipeline(file_path, db_engine=test_engine)

    # Проверяем результаты загрузки в тестовую базу данных
    with test_engine.connect() as conn:
        # Проверяем количество загруженных транзакций
        facts_count = conn.execute(text("SELECT COUNT(*) FROM fact_transactions")).scalar_one()

        assert facts_count == 2

        # Проверяем общую сумму расходов
        total_amount = conn.execute(text("SELECT SUM(amount) FROM fact_transactions")).scalar_one()

        assert total_amount == Decimal("-224.89")

        # Проверяем количество банковских карт
        cards_count = conn.execute(text("SELECT COUNT(*) FROM dim_cards")).scalar_one()

        assert cards_count == 2
