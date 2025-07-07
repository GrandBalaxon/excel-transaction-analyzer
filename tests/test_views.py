import datetime
import json
from pathlib import Path

from src.views import get_main_page_data, get_greeting, get_currency_rates


def test_get_greeting():
    morning = datetime.datetime(2023, 1, 1, 8, 0, 0)
    assert get_greeting(morning) == "Доброе утро"

    day = datetime.datetime(2023, 1, 1, 13, 0, 0)
    assert get_greeting(day) == "Добрый день"

    day = datetime.datetime(2023, 1, 1, 19, 0, 0)
    assert get_greeting(day) == "Добрый вечер"


def test_get_main_page_data_normal_work(mocker, more_complex_transactions):
    """ Тестируем нормальную работу функции с мокировкой работы с API. """
    mock_currency_rates = mocker.patch(
        "src.views.get_currency_rates", return_value=[{"currency": "USD", "rate": 61.3}]
    )
    mock_stock_prices = mocker.patch("src.views.get_sp500_index", return_value=[{"stock": "AAPL", "price": 77.58}])

    result = get_main_page_data("2020-01-10 22:45:11", more_complex_transactions)
    data = json.loads(result)

    assert data["greeting"] == "Доброй ночи"
    assert len(data["cards"]) == 2
    assert len(data["top_transactions"]) == 2
    assert data["currency_rates"][0]["currency"] == "USD"
    assert data["stock_prices"][0]["stock"] == "AAPL"

    mock_currency_rates.assert_called_once()
    mock_stock_prices.assert_called_once()


def test_get_main_page_data_error(mocker, more_complex_transactions):
    """ Тестируем работу функции при возбуждении ошибки. """
    mocker.patch("src.views.json.load", return_value={})

    result = get_main_page_data("2020-01-10 22:45:11", more_complex_transactions)
    data = json.loads(result)

    assert data["error"] == "Не удалось сформировать данные"


def test_get_currency_rates_normal_work(mocker):
    """ Тестируем нормальную работу. """
    mock_response = {
        "securities": {
            "columns": ["secid", "rate", "clearing"],
            "data": [
                ["USD/RUB", 75.1234, "pk"],
                ["EUR/RUB", 85.5678, "pk"],
                ["GBP/RUB", 95.4321, "vk"],
                ["CNY/RUB", 12.3456, "pk"]
            ]
        }
    }
    mocker.patch("requests.get").return_value.json.return_value = mock_response

    # предотвращаем сохранение результатов декоратором в лог
    mocker.patch("src.decorators.json.dump")

    date = datetime.datetime(2023, 1, 1)
    currencies = ["USD", "EUR"]
    result = get_currency_rates(date, currencies)

    assert len(result) == 2
    assert {"currency": "USD", "rate": 75.12} in result
    assert {"currency": "EUR", "rate": 85.57} in result
    assert all(x["currency"] in currencies for x in result)
