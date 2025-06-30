import logging
from typing import Optional, Union, Dict, Any
import datetime
import pandas as pd
from pathlib import Path

from dateutil.relativedelta import relativedelta

from src.decorators import backlogging


logger = logging.getLogger("reports")


def get_transactions_df(file_path: Path) -> Optional[pd.DataFrame]:
    """ """
    try:
        with open(file_path) as file:
            df = pd.read_excel(file_path)
            return df

    except Exception as e:
        logger.error(f"Не удалось открыть файл по пути {file_path} - ошибка {str(e)}", exc_info=True)
        return None


@backlogging(backlog_file_name="spelling_by_category_log.json")
def spending_by_category(
    transactions: pd.DataFrame, category: str, date: Union[datetime.datetime, str] = datetime.datetime.now()
) -> Optional[Dict[str, Any]]:
    """ """
    try:
        if isinstance(date, str):
            end_date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            logger.debug(f"Перевод даты из формата {str} в {datetime.datetime}")
            logger.info(f"Конечная дата для отсеивания операций: {end_date}")
        else:
            end_date = date
            logger.info(f"Конечная дата для отсеивания операций: {end_date}")

        start_date = end_date - relativedelta(months=3)
        logger.info(f"Начальная дата для отсеивания операций: {start_date}")

        df = transactions.copy()
        original_count = len(df)
        logger.info(f"Операций в датафрейме: {original_count}")

        df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")

        filtered_df = df[
            (start_date <= df["Дата операции"])
            & (df["Дата операции"] <= end_date)
        ]
        logger.info(f"Операций в нужном временном промежутке: {len(filtered_df)}")

        filtered_by_category = filtered_df[filtered_df["Категория"] == category]
        result_df = filtered_by_category["Дата операции"].dt.strftime("%d.%m.%Y %H:%M:%S")
        logger.info(f"Операций с указанной категорией: {len(result_df)}")

        return filtered_by_category.to_dict(orient="records")

    except Exception as e:
        logger.error(f"Возникла непредвиденная ошибка: {str(e)}", exc_info=True)
        return None


if __name__ == "__main__":
    file_name = "operations.xlsx"
    file_path = Path(__file__).parent.parent / "data" / file_name
    data = get_transactions_df(file_path)
    category_ = "Пополнения"

    data_output = spending_by_category(data, category_, "2021-12-31 22:45:11")
    print(data_output)
