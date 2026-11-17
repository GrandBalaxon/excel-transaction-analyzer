from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.database import engine
from src.pipeline import run_pipeline


def test_run_pipeline_end_to_end(tmp_path: Path, raw_transactions_df: pd.DataFrame):
    """Тестирует весь пайплайн: от чтения Excel до записи в Postgres."""
    # 1. Создаем временный Excel-файл, используя данные из фикстуры
    file_path = tmp_path / "test_operations.xlsx"
    raw_transactions_df.to_excel(file_path, index=False)

    # 2. Запускаем пайплайн
    run_pipeline(file_path)

    # 3. Проверяем, что данные действительно появились в БД
    with engine.connect() as conn:
        # Проверяем факты (должно быть 2, так как FAILED отфильтровывается)
        facts_count = conn.execute(text("SELECT COUNT(*) FROM fact_transactions")).scalar()
        assert facts_count == 2

        # Проверяем сумму (должна быть отрицательной: -160.89 + -64.0)
        total_amount = conn.execute(text("SELECT SUM(amount) FROM fact_transactions")).scalar()
        assert float(total_amount) == -224.89

        # Проверяем справочники
        cards_count = conn.execute(text("SELECT COUNT(*) FROM dim_cards")).scalar()
        assert cards_count == 2
