import pytest
import pandas as pd


@pytest.fixture
def sample_transactions():
    return pd.DataFrame({
        "Дата операции": [
            "01.01.2023 12:00:00",
            "15.02.2023 14:30:00",
            "20.03.2023 10:15:00",
            "20.03.2024 10:15:00"
        ],
        "Категория": ["Еда", "Транспорт", "Еда", "Транспорт"]
    })
