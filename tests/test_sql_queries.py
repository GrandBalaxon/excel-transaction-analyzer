from pathlib import Path

import pytest
from sqlalchemy import text

from src.database import engine

SQL_DIR = Path(__file__).parent.parent / "sql"
SQL_FILES = list(SQL_DIR.glob("*.sql"))


@pytest.mark.parametrize("sql_file", SQL_FILES, ids=lambda p: p.name)
def test_sql_queries_are_valid(sql_file: Path):
    """Проверяет, что каждый SQL файл синтаксически валиден и выполняется без ошибок."""
    query = sql_file.read_text(encoding="utf-8")

    with engine.connect() as conn:
        # Выполняем запрос. Если в нем синтаксическая ошибка или неверное имя колонки, тест упадет.
        result = conn.execute(text(query))
        result.fetchall()
