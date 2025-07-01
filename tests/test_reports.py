import datetime
from pathlib import Path

import pandas as pd
import pytest

import src.reports as reports


def test_get_transactions_df(mocker, tmp_path):
    """Успешная загрузка файла."""
    mock_read_excel = mocker.patch("pandas.read_excel")
    file_path = tmp_path / "test.xlsx"
    mock_read_excel.return_value = pd.DataFrame({"Data": [1, 2, 3]})

    result = reports.get_transactions_df(file_path)

    assert isinstance(result, pd.DataFrame)
    mock_read_excel.assert_called_once_with(file_path)


def test_get_transactions_df_file_not_found(mocker, tmp_path):
    """Обработка отсутствующего файла."""
    mock_read_excel = mocker.patch("pandas.read_excel")
    file_path = tmp_path / "test.xlsx"
    mock_read_excel.side_effect = FileNotFoundError("File not found")

    result = reports.get_transactions_df(file_path)

    assert result is None


def test_get_transactions_df_file_is_empty(mocker, tmp_path):
    """Обработка пустого файла."""
    mock_read_excel = mocker.patch("pandas.read_excel")
    file_path = tmp_path / "test.xlsx"
    mock_read_excel.return_value = pd.DataFrame({})

    result = reports.get_transactions_df(file_path)

    assert result is None


def test_spending_by_category_success(sample_transactions):
    """Корректная фильтрация данных."""

    result = reports.spending_by_category(sample_transactions, "Еда", "2023-01-30 12:00:00")

    assert len(result) == 1
    assert result[0]["Дата операции"] == "20.01.2023 12:00:00"


def test_spending_by_category_without_date_param(sample_transactions):
    """Корректная фильтрация данных без указания даты, чтобы взялась текущая дата для покрытия этого случая."""

    result = reports.spending_by_category(sample_transactions, "Еда")

    assert len(result) == 0


def test_spending_by_category_invalid_date_format(mocker, sample_transactions):
    """Неверный формат даты."""
    # Мокаем логгер для проверки ошибки
    mock_logger = mocker.patch.object(reports.logger, "error")

    result = reports.spending_by_category(sample_transactions, "Еда", "2023-03-31")

    assert result is None
    mock_logger.assert_called_once()
