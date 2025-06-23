import datetime
import json
import logging
import os
from collections import defaultdict
from math import isnan
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests
from dotenv import load_dotenv

from src.utils import get_data_from_excel

logger = logging.getLogger(__file__)

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


def get_sp500_index(date: datetime.datetime) -> List[Dict[str, Any]]:
    """  """
    base_url = "https://financialmodelingprep.com/stable/historical-price-eod/light"
    simple_date = date.strftime("%Y-%m-%d")

    file_path = Path(__file__).parent.parent / "data" / "user_settings.json"
    with open(file_path) as json_file:
        user_settings_dict = json.load(json_file)
        logger.info("Данные настроек пользователя успешно получены.")

    backlog_file_path = Path(__file__).parent.parent / "data" / "backlogged_data.json"
    try:
        with open(backlog_file_path) as json_file:
            backlog_dict: Dict = json.load(json_file)
            logger.info("Данные с бэк-лога успешно получены.")

    except json.decoder.JSONDecodeError:
        logger.warning("Файл бэк-логов пока пуст.")
        backlog_dict = {}

    if not backlog_dict.get(simple_date):
        backlog_dict[simple_date] = {
            "currency_rates": [],
            "stock_prices": []
        }
        logger.info(f"Был создан словарь для бэк-лога с данными за {simple_date}.")

    for stock in user_settings_dict["user_stocks"]:
        # если в бэк-логе еще нет данных за указанную дату
        if len(backlog_dict[simple_date]["stock_prices"]) < len(user_settings_dict["user_stocks"]):
            params = {
                "symbol": stock,
                "apikey": API_KEY,
                "from": simple_date,
                "to": simple_date
            }
            response = requests.get(base_url, params=params).json()
            info = {
                "stock": response[0]["symbol"],
                "price": response[0]["price"]
            }
            backlog_dict[simple_date]["stock_prices"].append(info)
            break






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

    def default_value():
        return {"total_spent": 0.0, "cashback": 0.0}

    cards_info = defaultdict(default_value)
    cards = []
    top_transactions = []

    try:
        date = datetime.datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")

        filtered_transactions = [x for x in transactions if is_in_time_period(x["Дата операции"], date)]
        logger.info(f"Отфильтрованы {len(filtered_transactions)} операций подходящих по дате.")

        for transaction in filtered_transactions:
            if transaction["Статус"] == "OK":
                # запись информации по картам
                card_number = transaction.get("Номер карты")

                if isinstance(card_number, str):
                    cards_info[card_number]["total_spent"] += transaction["Сумма операции с округлением"]

                    if not isnan(transaction["Кэшбэк"]):
                        cards_info[card_number]["cashback"] += transaction["Кэшбэк"]

                # запись информации по топ транзакциям
                info = {
                    "date": transaction["Дата платежа"],
                    "amount": round(transaction["Сумма операции с округлением"], 2),
                    "category": transaction["Категория"],
                    "description": transaction["Описание"],
                }
                top_transactions.append(info)

        top_transactions = sorted(top_transactions, key=lambda x: x["amount"], reverse=True)[:5]

        for card_num, values in cards_info.items():
            if isinstance(card_num, str):
                info = {
                    "last_digits": card_num,
                    "total_spent": round(values["total_spent"], 2),
                    "cashback": round(values["cashback"], 2),
                }
                cards.append(info)

        final_output = {"greeting": get_greeting(date), "cards": cards, "top_transactions": top_transactions}

        return json.dumps(final_output, indent=4, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {str(e)}", exc_info=True)
        final_output = {"error": "Не удалось сформировать данные", "details": str(e)}
        return json.dumps(final_output, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    path = Path(__file__).parent.parent / "data" / "operations.xlsx"
    transactions_ = get_data_from_excel(path)
    final_json = get_main_page_data("2021-05-21 15:45:00", transactions=transactions_)

    date_ = "2021-05-21 15:45:00"
    date = datetime.datetime.strptime(date_, "%Y-%m-%d %H:%M:%S")

    print(get_sp500_index(date)) # [{'symbol': 'AAPL', 'date': '2021-05-21', 'price': 125.43, 'volume': 79295436}]
