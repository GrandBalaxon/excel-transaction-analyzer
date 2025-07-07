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
                "29.09.1997 12:00:00"
            ],
            "Категория": ["Еда", "Еда", "Еда", "Транспорт", "Медицинские услуги"],
            "Кэшбэк": [0, 4, 50, None, None]
        }
    )


@pytest.fixture(autouse=True)
def setup_mocks(mocker):
    """Автоматически подменяет все внешние зависимости для каждого теста"""
    # Мок для json.load с пустым словарём по умолчанию
    mocker.patch("src.decorators.json.load", return_value={})

    # Мок для json.dump
    mocker.patch("src.decorators.json.dump")

    # Мок для open и Path.touch
    mocker.patch("src.decorators.Path.touch")

    # Мок для hashlib.sha256 (чтобы тесты были детерминированы)
    mock_sha256 = mocker.patch("src.decorators.hashlib.sha256")
    mock_sha256.return_value.hexdigest.return_value = "mocked_hash"
