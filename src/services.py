import datetime
import json
import logging
from math import isnan
from typing import Any, Dict, Iterable, Optional, Union

from src.decorators import backlogging

logger = logging.getLogger("services")


def is_transaction_in_period(transaction_date: str, year: int, month: Union[int, None] = None) -> bool:
    """
    Проверяет, попадает ли транзакция в указанный временной период.

    Args:
        transaction_date: Дата транзакции в формате "dd.mm.YYYY HH:MM:SS"
        year: Год для проверки
        month: Месяц для проверки (если None, проверяется только год)

    Returns:
        bool: True если транзакция попадает в указанный период, иначе False
    """
    t_d = datetime.datetime.strptime(transaction_date, "%d.%m.%Y %H:%M:%S")

    if t_d.year == year and (t_d.month == month if month is not None else True):
        return True
    else:
        return False


@backlogging("services_log.json")
def calculate_category_cashback(
    transactions: Iterable[Dict[str, Any]], year: int, month: Union[int, None] = None
) -> Optional[str]:
    """
    Вычисляет сумму кэшбэка по категориям за указанный период.

    Фильтрует транзакции по дате и наличию кэшбэка, затем суммирует кэшбэк по категориям.

    Args:
        transactions: Итерируемый объект со словарями транзакций
        year: Год для анализа
        month: Месяц для анализа (если None, анализируется весь год)

    Returns:
        str: JSON-строка с категориями и суммами кэшбэка | None при ошибке.
    """
    try:
        filtered_transactions = []
        for x in transactions:
            if is_transaction_in_period(x["Дата операции"], year=year, month=month) and not isnan(x["Кэшбэк"]):
                filtered_transactions.append(x)
        logger.info(f"Отфильтрованы {len(filtered_transactions)} операций подходящих по дате и с наличием кэшбэка.")

        output_dict = {}

        for transaction in filtered_transactions:
            category = transaction["Категория"]
            cashback = transaction["Кэшбэк"]

            if cashback == 0:
                continue

            if category not in output_dict:
                output_dict[category] = round(cashback)
            else:
                output_dict[category] += round(cashback)

        logger.info(f"Итоговый словарь содержит в себе {len(output_dict)} категорий кэшбэка.")
        return json.dumps(output_dict, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {str(e)}", exc_info=True)
        return None
