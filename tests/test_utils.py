from typing import Iterable

import pandas as pd
import pytest

from src.utils import get_data_from_excel


def test_utils_normal_work(mocker, tmp_path, sample_transactions):
    mock_read_excel = mocker.patch("pandas.read_excel")
    file_path = tmp_path / "test.xlsx"
    mock_read_excel.return_value = sample_transactions

    result = get_data_from_excel(file_path)

    assert isinstance(result, Iterable)
    mock_read_excel.assert_called_once_with(file_path)


def test_utils_empty_file(mocker, tmp_path):
    mock_read_excel = mocker.patch("pandas.read_excel")
    file_path = tmp_path / "test.xlsx"
    mock_read_excel.return_value = pd.DataFrame({})

    result = get_data_from_excel(file_path)

    assert result == []
    mock_read_excel.assert_called_once_with(file_path)


def test_utils_error_raised(mocker, tmp_path):
    mock_read_excel = mocker.patch("pandas.read_excel")
    file_path = tmp_path / "test.xlsx"
    mock_read_excel.side_effect = Exception("Непредвиденная ошибка")

    result = get_data_from_excel(file_path)

    assert result == []
    mock_read_excel.assert_called_once_with(file_path)