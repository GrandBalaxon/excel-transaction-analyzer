import logging
from typing import Optional
import datetime
import pandas as pd
from pathlib import Path

from dateutil.relativedelta import relativedelta

from src.decorators import backlogging


logger = logging.getLogger("reports")


def get_transactions_df(file_path: Path) -> Optional[pd.DataFrame]:
    """

    """
    try:
        with open(file_path) as file:
            df = pd.read_excel(file_path)
            return df

    except Exception as e:
        logger.error(f"Не удалось открыть файл по пути {file_path} - ошибка {str(e)}", exc_info=True)
        return None


def spending_by_category(transactions: pd.DataFrame,
                         category: str,
                         date: Optional[str] = None) -> pd.DataFrame:
    """

    """
    if date:
        end_date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    else:
        end_date = datetime.datetime.now()

    start_date = end_date - relativedelta(months=3)

