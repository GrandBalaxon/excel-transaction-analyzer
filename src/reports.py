import datetime
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

import pandas as pd
from dateutil.relativedelta import relativedelta

from src.decorators import backlogging

logger = logging.getLogger("reports")


def get_transactions_df(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Загружает транзакции из Excel-файла в DataFrame.

    :param file_path: Путь к файлу Excel с транзакциями
    :return: DataFrame с транзакциями или None в случае ошибки
    """
    try:
        df = pd.read_excel(file_path)

        if not df.empty:
            logger.info(f"Успешно прочитано {len(df)} транзакций из Excel")
            return df
        else:
            logger.warning("Файл пуст.")
            return None

    except Exception as e:
        logger.error(f"Не удалось открыть файл по пути {file_path} - ошибка {str(e)}", exc_info=True)
        return None


# @backlogging(backlog_file_name="reports_log.json")
def spending_by_category(
    transactions: pd.DataFrame, category: str, date: Union[datetime.datetime, str] = datetime.datetime.now()
) -> Optional[Dict[str, Any]]:
    """
    Фильтрует транзакции по категории и временному диапазону (последние 3 месяца).

    :param transactions: DataFrame с транзакциями
    :param category: Категория для фильтрации
    :param date: Конечная дата диапазона (по умолчанию текущая дата)
    :return: Список словарей с отфильтрованными транзакциями или None при ошибке
    """
    try:
        if isinstance(date, str):
            end_date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            logger.debug(f"Перевод даты из формата {str} в {datetime.datetime}")
        else:
            end_date = date

        logger.info(f"Конечная дата для отсеивания операций: {end_date}")
        start_date = end_date - relativedelta(months=3)
        logger.info(f"Начальная дата для отсеивания операций: {start_date}")

        df = transactions.copy()
        logger.info(f"Операций в датафрейме: {len(df)}")

        # преобразование дат из строк в datetime
        df.loc[:, "Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")

        # фильтрация по датам и категориям
        filtered_df = df.loc[
            (df["Категория"] == category) & (start_date <= df["Дата операции"]) & (df["Дата операции"] <= end_date)
        ]
        logger.info(f"отфильтровано операций: {len(filtered_df)}")

        # преобразование дат обратно в строки
        filtered_df.loc[:, "Дата операции"] = pd.to_datetime(
            filtered_df["Дата операции"], errors="coerce"
        ).dt.strftime("%d.%m.%Y %H:%M:%S")

        return filtered_df.to_dict(orient="records")

    except Exception as e:
        logger.error(f"Возникла непредвиденная ошибка: {str(e)}", exc_info=True)
        return None
