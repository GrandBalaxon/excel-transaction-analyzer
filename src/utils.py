import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

logger = logging.getLogger(__file__)


def get_data_from_excel(file_path: Path) -> Iterable[Optional[Dict[str, Any]]]:
    """ """
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


if __name__ == "__main__":
    path = Path(__file__).parent.parent / "data" / "operations.xlsx"
    transactions = get_data_from_excel(path)
    print(transactions[0])
