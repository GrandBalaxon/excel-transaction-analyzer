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
        return pd.read_excel(file_path)

    except Exception as e:
        logger.error(f"Не удалось открыть файл по пути {file_path} - ошибка {str(e)}", exc_info=True)
        return None


@backlogging(backlog_file_name="reports_log.json")
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

        df.loc[:, "Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")

        filtered_df = df.loc[
            (df["Категория"] == category) & (start_date <= df["Дата операции"]) & (df["Дата операции"] <= end_date)
        ]
        logger.info(f"отфильтровано операций: {len(filtered_df)}")
        logger.debug(f"Тип данных в столбце 'Дата операции': {filtered_df['Дата операции'].dtype}")

        # Преобразование обратно в строковый формат с проверкой
        if not filtered_df.empty:
            # Явно проверяем тип данных
            if pd.api.types.is_datetime64_any_dtype(filtered_df["Дата операции"]):
                filtered_df.loc[:, "Дата операции"] = filtered_df["Дата операции"].dt.strftime("%d.%m.%Y %H:%M:%S")
            else:
                logger.warning(
                    "Тип данных столбца 'Дата операции' не является datetime. Принудительное преобразование."
                )
                filtered_df.loc[:, "Дата операции"] = pd.to_datetime(
                    filtered_df["Дата операции"], errors="coerce"
                ).dt.strftime("%d.%m.%Y %H:%M:%S")
        else:
            logger.info("Фильтрованный DataFrame пуст, преобразование не требуется")

        return filtered_df.to_dict(orient="records")

    except Exception as e:
        logger.error(f"Возникла непредвиденная ошибка: {str(e)}", exc_info=True)
        return None


if __name__ == "__main__":
    file_name = "operations.xlsx"
    file_path = Path(__file__).parent.parent / "data" / file_name
    data = get_transactions_df(file_path)
    category_ = "Пополнения"

    data_output = spending_by_category(data, category_, "2021-10-31 22:45:11")
    print(data_output)
