import json

from src.services import calculate_category_cashback


def test_calculate_category_cashback_normal_work(mocker, sample_transactions):
    """Тестирование нормальной работы функции."""
    transactions = sample_transactions.to_dict(orient="records")

    mocker.patch("src.decorators.json.dump")

    result_str = calculate_category_cashback(transactions, 2023)
    result_dict = json.loads(result_str)

    assert len(result_dict) == 1
    assert result_dict["Еда"] == 54


def test_calculate_category_error_raised(mocker):
    """Тестирования функции при возбуждении ошибки."""
    invalid_transactions = [{"Некорректное": "поле"}]
    mock_error = mocker.patch("src.services.logger.error")

    result = calculate_category_cashback(invalid_transactions, 2023)

    assert result is None
    mock_error.assert_called_once()
