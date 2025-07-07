import datetime
import json
import logging
import os
from collections import defaultdict
from math import isnan
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import requests
from dotenv import load_dotenv

from src.decorators import backlogging

logger = logging.getLogger("views")

load_dotenv()
API_KEY = os.getenv("API_KEY")


def get_greeting(date_time: datetime.datetime) -> str:
    """Функция возвращает сообщение-приветствие в зависимости от текущего времени."""
    cur_hour = date_time.hour

    if 6 <= cur_hour <= 11:
        return "Доброе утро"
    elif 12 <= cur_hour <= 17:
        return "Добрый день"
    elif 18 <= cur_hour <= 20:
        return "Добрый вечер"
    else:  # 21-5 (включительно)
        return "Доброй ночи"


def is_in_time_period(transaction_date, date_to_look_for) -> bool:
    """
    Проверяет, попадает ли транзакция в указанный временной период.

    Args:
        transaction_date: Дата транзакции в формате "дд.мм.ГГГГ ЧЧ:ММ:СС"
        date_to_look_for: Дата, с которой сравнивается транзакция (включая время)

    Returns:
        True - если транзакция произошла в том же году и месяце, что и date_to_look_for,
        и не позднее указанной даты (включительно). Иначе False.
    """
    t_d = datetime.datetime.strptime(transaction_date, "%d.%m.%Y %H:%M:%S")

    if t_d.year == date_to_look_for.year and t_d.month == date_to_look_for.month and t_d <= date_to_look_for:
        return True
    else:
        return False


@backlogging("views_log.json")
def get_currency_rates(date: datetime.datetime, currency_list: List[str]) -> List[Dict[str, Any]]:
    """
    Получает курсы валют с Московской Биржи на указанную дату и фильтрует по заданному списку валют.

    Args:
        date: Дата для получения курсов
        currency_list: Список валютных пар (например, ["USD", "EUR"]), где валюта конвертируется в RUB

    Returns:
        Список словарей с курсами валют формата:
        [{"currency": "USD", "rate": 75.50}, ...]
        где rate округлен до 2 знаков после запятой.
    """
    base_url = "https://iss.moex.com/iss/statistics/engines/futures/markets/indicativerates/securities.json"
    simple_date = date.strftime("%Y-%m-%d")

    params = {"date": simple_date}

    response = requests.get(base_url, params=params).json()

    # получаем ответ формата ->
    # {"securities": {
    #     "metadata": {...},
    #     "columns": ["tradedate", "tradetime", "secid", "rate", "clearing"],
    #     "data": [
    #         ["2021-03-19", "13:45:00", "CAD\/RUB", 59.14380, "pk"],
    #         ["2021-03-19", "18:30:00", "CAD\/RUB", 59.26380, "vk"],
    #         ...
    #     ]
    # },...}

    # преобразовываем полученный ответ в удобный DataFrame
    data = response["securities"]["data"]
    columns = response["securities"]["columns"]
    df = pd.DataFrame(data, columns=columns)

    df[["from", "to"]] = df["secid"].str.split("/", expand=True, n=1)
    df = df.drop(columns=["secid"])

    data_dict = df.to_dict(orient="records")
    filtered_data = [x for x in data_dict if x["clearing"] == "pk" and x["to"] == "RUB" and x["from"] in currency_list]
    currency_rates = [{"currency": x["from"], "rate": round(x["rate"], 2)} for x in filtered_data]

    return currency_rates


@backlogging("views_log.json")
def get_sp500_index(date: datetime.datetime, stocks_list: List[str]) -> List[Dict[str, Any]]:
    """
    Получает информацию о цене закрытия акций из списка S&P 500 на заданную дату.

    Использует API financialmodelingprep.com для получения исторических данных о ценах акций.

    Args:
        date: Дата, за которую нужно получить данные.
        stocks_list: Список тикеров акций (например, ['AAPL', 'MSFT']).

    Returns:
        List[Dict[str, Any]]: Список словарей, где каждый словарь содержит информацию о цене закрытия
                                акции (тикер и цену). Например, [{'stock': 'AAPL', 'price': 125.43}, ...].
    """
    base_url = "https://financialmodelingprep.com/stable/historical-price-eod/light"
    simple_date = date.strftime("%Y-%m-%d")

    stocks_info = []

    for stock in stocks_list:
        logger.info(f"Работа со стоком: {stock}")
        params = {"symbol": stock, "apikey": API_KEY, "from": simple_date, "to": simple_date}
        response = requests.get(base_url, params=params).json()
        logger.info(f"Полученный ответ: {response}")
        # получаем словарь вида: [{'symbol': 'AAPL', 'date': '2021-05-21', 'price': 125.43, 'volume': 79295436}]
        info = {"stock": stock, "price": response[0]["price"]}
        stocks_info.append(info)

    return stocks_info


def get_cards_usage_info(transactions_list) -> List[Dict[str, Any]]:
    """
    Агрегирует информацию по использованию карт: общая сумма трат и кэшбэк.

    Args:
        transactions_list: Список транзакций. Каждая транзакция - словарь с полями:
            "Статус" (str), "Номер карты" (str),
            "Сумма операции с округлением" (float), "Кэшбэк" (float)

    Returns:
        List[Dict[str, Any]]: Список словарей с информацией по картам:
            last_digits (str): последние цифры карты,
            total_spent (float): суммарные траты (округлено до 2 знаков),
            cashback (float): суммарный кэшбэк (округлено до 2 знаков)
    """

    def default_value():
        return {"total_spent": 0.0, "cashback": 0.0}

    cards_info = defaultdict(default_value)
    cards = []

    for transaction in transactions_list:
        if transaction["Статус"] == "OK":
            card_number = transaction.get("Номер карты")

            if isinstance(card_number, str):
                cards_info[card_number]["total_spent"] += transaction["Сумма операции с округлением"]

                if not isnan(transaction["Кэшбэк"]):
                    cards_info[card_number]["cashback"] += transaction["Кэшбэк"]

    for card_num, values in cards_info.items():
        if isinstance(card_num, str):
            info = {
                "last_digits": card_num,
                "total_spent": round(values["total_spent"], 2),
                "cashback": round(values["cashback"], 2),
            }
            cards.append(info)

    return cards


def get_top_n_transactions(transactions_list, n: int) -> List[Dict[str, Any]]:
    """
    Возвращает топ-N транзакций со статусом 'OK', отсортированных по убыванию суммы.

    Args:
        transactions_list: Список транзакций (каждая — словарь с полями "Статус", "Дата платежа" и др.).
        n: Количество транзакций для возврата. Если n > длины списка, вернёт все подходящие.

    Returns:
        List[Dict[str, Any]]: Топ-N транзакций, где каждая имеет формат:
        date (str), amount (float), category (str), description (str).
        Сумма округляется до 2 знаков после запятой.
    """
    top_transactions = []

    for transaction in transactions_list:
        if transaction["Статус"] == "OK":
            info = {
                "date": transaction["Дата платежа"],
                "amount": round(transaction["Сумма операции с округлением"], 2),
                "category": transaction["Категория"],
                "description": transaction["Описание"],
            }
            top_transactions.append(info)

    return sorted(top_transactions, key=lambda x: x["amount"], reverse=True)[:n]


def get_main_page_data(date_time: str, transactions: Iterable[Optional[Dict[str, Any]]]) -> str:
    """
    Формирует сводные данные для главной страницы в формате JSON.

    Для работы требуется файл "user_settings.json" лежащий в папке data в корне проекта.

    Пример его структуры:
        {
        "user_currencies": ["USD", "EUR", ...],
        "user_stocks": ["AAPL", "AMZN", ...]
        }

    Args:
        date_time: Дата и время в формате "YYYY-MM-DD HH:MM:SS"
        transactions: Итерируемый объект с транзакциями (может содержать None)

    Returns:
        str: JSON-строка с:
            1. Приветствием (в зависимости от времени суток)
            2. Информацией по картам: последние цифры, сумма расходов, кэшбэк (1% от суммы)
            3. Топ-5 транзакций по сумме
            4. Курсами валют (из user_settings.json)
            5. Стоимостью акций S&P500 (из user_settings.json)
    """
    try:
        date = datetime.datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")

        filtered_transactions = [x for x in transactions if is_in_time_period(x["Дата операции"], date)]
        logger.info(f"Отфильтрованы {len(filtered_transactions)} операций подходящих по дате.")

        cards = get_cards_usage_info(filtered_transactions)
        top_transactions = get_top_n_transactions(filtered_transactions, 5)

        file_path = Path(__file__).parent.parent / "data" / "user_settings.json"
        with open(file_path) as json_file:
            user_settings_dict = json.load(json_file)
            logger.info("Данные настроек пользователя успешно получены.")

        user_currency_list = user_settings_dict["user_currencies"]
        currency_rates_list = get_currency_rates(date, user_currency_list)

        user_stocks_list = user_settings_dict["user_stocks"]
        stock_prices_list = get_sp500_index(date, user_stocks_list)

        final_output = {
            "greeting": get_greeting(date),
            "cards": cards,
            "top_transactions": top_transactions,
            "currency_rates": currency_rates_list,
            "stock_prices": stock_prices_list,
        }

        return json.dumps(final_output, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {str(e)}", exc_info=True)
        final_output = {"error": "Не удалось сформировать данные", "details": str(e)}
        return json.dumps(final_output, indent=2, ensure_ascii=False)
