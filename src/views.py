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
from src.utils import get_data_from_excel

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
    """ """
    t_d = datetime.datetime.strptime(transaction_date, "%d.%m.%Y %H:%M:%S")

    if t_d.year == date_to_look_for.year and t_d.month == date_to_look_for.month and t_d <= date_to_look_for:
        return True
    else:
        return False


@backlogging("views_log.json")
def get_currency_rates(date: datetime.datetime, currency_list: List[str]) -> List[Dict[str, Any]]:
    """ """
    base_url = "https://iss.moex.com/iss/statistics/engines/futures/markets/indicativerates/securities.json"
    simple_date = date.strftime("%Y-%m-%d")

    params = {"date": simple_date}

    response = requests.get(base_url, params=params).json()

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
    """ """
    base_url = "https://financialmodelingprep.com/stable/historical-price-eod/light"
    simple_date = date.strftime("%Y-%m-%d")

    stocks_info = []

    for stock in stocks_list:
        params = {"symbol": stock, "apikey": API_KEY, "from": simple_date, "to": simple_date}
        response = requests.get(base_url, params=params).json()
        # получаем словарь вида: [{'symbol': 'AAPL', 'date': '2021-05-21', 'price': 125.43, 'volume': 79295436}]
        info = {"stock": stock, "price": response[0]["price"]}
        stocks_info.append(info)

    return stocks_info


def get_cards_usage_info(transactions_list) -> List[Dict[str, Any]]:
    """"""

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
    """"""
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
    Функция принимающая на вход строку с датой и временем в формате YYYY-MM-DD HH:MM:SS и возвращающую
    JSON-ответ со следующими данными:

    1) Приветствие в зависимости от текущего времени.
    2) По каждой карте:
        * последние 4 цифры карты;
        * общая сумма расходов;
        * кешбэк (1 рубль на каждые 100 рублей).
    3) Топ-5 транзакций по сумме платежа.
    4) Курс валют.
    5) Стоимость акций из S&P500.
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


if __name__ == "__main__":
    path = Path(__file__).parent.parent / "data" / "operations.xlsx"
    transactions_ = get_data_from_excel(path)
    final_json = get_main_page_data("2020-01-10 22:45:11", transactions=transactions_)
    print(final_json)
