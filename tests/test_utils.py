from typing import Iterable

import pandas as pd

from src.utils import get_data_from_excel


def test_utils_normal_work(mocker, tmp_path, sample_transactions):
    """Тестируем нормальную работу функции."""
    mock_read_excel = mocker.patch("pandas.read_excel")
    file_path = tmp_path / "test.xlsx"
    mock_read_excel.return_value = sample_transactions

    result = get_data_from_excel(file_path)

    assert isinstance(result, Iterable)
    mock_read_excel.assert_called_once_with(file_path)


def test_utils_empty_file(mocker, tmp_path):
    """Тестируем работу с пустым файлом."""
    mock_read_excel = mocker.patch("pandas.read_excel")
    file_path = tmp_path / "test.xlsx"
    mock_read_excel.return_value = pd.DataFrame({})

    result = get_data_from_excel(file_path)

    assert result == []
    mock_read_excel.assert_called_once_with(file_path)


def test_utils_error_raised(mocker, tmp_path):
    """Тестируем работу функции при возбуждении ошибки."""
    mock_read_excel = mocker.patch("pandas.read_excel", side_effect=Exception("Непредвиденная ошибка"))
    file_path = tmp_path / "test.xlsx"

    result = get_data_from_excel(file_path)

    assert result == []
    mock_read_excel.assert_called_once_with(file_path)
