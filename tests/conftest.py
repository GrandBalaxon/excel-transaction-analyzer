import pandas as pd
import pytest


@pytest.fixture
def sample_transactions():
    return pd.DataFrame(
        {
            "Дата операции": [
                "20.01.2023 12:00:00",
                "20.02.2023 12:00:00",
                "20.03.2023 12:00:00",
                "20.04.2023 12:00:00",
            ],
            "Категория": ["Еда", "Транспорт", "Еда", "Транспорт"],
        }
    )
