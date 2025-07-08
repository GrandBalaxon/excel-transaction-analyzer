import logging
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import pandas as pd

logger = logging.getLogger("utils")


def get_data_from_excel(file_path: Path) -> Iterable[Optional[Dict[str, Any]]]:
    """
    Читает данные транзакций из Excel-файла и преобразует в список словарей.

    Args:
        file_path: Путь к файлу Excel (.xlsx, .xls)

    Returns:
        Список словарей с данными транзакций (один словарь = одна транзакция),
        либо пустой список если файл пуст или произошла ошибка чтения.
    """
    try:
        df = pd.read_excel(file_path)
        if not df.empty:
            logger.info(f"Успешно прочитано {len(df)} транзакций из Excel")
            return df.to_dict(orient="records")
        else:
            logger.warning("Файл пуст.")
            return []

    except Exception as e:
        logger.error(f"Не удалось открыть файл по пути {file_path} - ошибка {e}")
        return []
