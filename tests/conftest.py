import pandas as pd
import pytest


@pytest.fixture
def raw_transactions_df() -> pd.DataFrame:
    """Сырые данные, имитирующие Excel-файл operations.xlsx."""
    return pd.DataFrame({
        "Дата операции": ["31.12.2021 16:44:00", "31.12.2021 16:42:04", "14.11.2021 14:46:24"],
        "Номер карты": ["*7197", "*4556", "*4556"],
        "Статус": ["OK", "OK", "FAILED"],
        "Сумма операции": [-160.89, -64.0, -55.0],
        "Кэшбэк": [1.0, None, 0.0],
        "Категория": ["Супермаркеты", "Развлечения", "Переводы"],
        "Описание": ["Колхоз", "Кино", "Перевод на карту"]
    })


@pytest.fixture
def empty_dataframe() -> pd.DataFrame:
    """Пустой датафрейм для проверки extract."""
    return pd.DataFrame()
