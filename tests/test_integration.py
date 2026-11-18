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
    """Check the full ETL cycle: from reading Excel to writing into PostgreSQL."""

    # Create a temporary Excel file from the test data
    file_path = tmp_path / "test_operations.xlsx"
    raw_transactions_df.to_excel(file_path, index=False)

    # Run the pipeline against the test database
    run_pipeline(file_path, db_engine=test_engine)

    # Check what was loaded into the test database
    with test_engine.connect() as conn:
        # Check the number of loaded transactions
        facts_count = conn.execute(text("SELECT COUNT(*) FROM fact_transactions")).scalar_one()

        assert facts_count == 2

        # Check the total amount of expenses
        total_amount = conn.execute(text("SELECT SUM(amount) FROM fact_transactions")).scalar_one()

        assert total_amount == Decimal("-224.89")

        # Check the number of bank cards
        cards_count = conn.execute(text("SELECT COUNT(*) FROM dim_cards")).scalar_one()

        assert cards_count == 2
