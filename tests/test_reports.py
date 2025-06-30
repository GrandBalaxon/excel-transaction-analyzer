from pathlib import Path

import pandas as pd
import pytest

from src.reports import get_transactions_df, spending_by_category


def test_get_transactions_df(mocker, tmp_path):
    """Успешная загрузка файла."""
    mock_read_excel = mocker.patch("pandas.read_excel")
    file_path = tmp_path / "test.xlsx"
    mock_read_excel.return_value = pd.DataFrame({"Data": [1, 2, 3]})

    result = get_transactions_df(file_path)

    assert isinstance(result, pd.DataFrame)
    mock_read_excel.assert_called_once_with(file_path)


def test_get_transactions_df_file_not_found(mocker, tmp_path):
    """Обработка отсутствующего файла."""
    mock_read_excel = mocker.patch("pandas.read_excel")
    file_path = tmp_path / "test.xlsx"
    mock_read_excel.side_effect = FileNotFoundError("File not found")

    result = get_transactions_df(file_path)

    assert result is None
