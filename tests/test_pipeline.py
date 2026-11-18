from pathlib import Path

from src.pipeline import extract, transform


def test_extract_success(mocker, raw_transactions_df, tmp_path: Path):
    """Тестируем успешное чтение Excel."""
    mock_read = mocker.patch("pandas.read_excel", return_value=raw_transactions_df)

    result = extract(tmp_path / "dummy.xlsx")

    assert result is not None
    assert len(result) == 3
    mock_read.assert_called_once()


def test_extract_empty_file(mocker, empty_dataframe, tmp_path: Path):
    """Тестируем случай, если Excel-файл пуст."""
    mocker.patch("pandas.read_excel", return_value=empty_dataframe)

    result = extract(tmp_path / "dummy.xlsx")

    assert result is None


def test_transform_logic(raw_transactions_df):
    """Тестируем логику трансформации (очистка и разбиение)."""
    tables = transform(raw_transactions_df)

    # Проверяем, что вернулись все 4 таблицы
    assert "dim_cards" in tables
    assert "dim_categories" in tables
    assert "dim_dates" in tables
    assert "facts" in tables

    # Проверяем очистку таблицы фактов
    facts = tables["facts"]
    assert len(facts) == 2
    assert all(facts["status"] == "OK")

    # Проверяем заполнение NaN в кэшбэке
    assert facts["cashback"].isna().sum() == 0
    assert facts["cashback"].iloc[1] == 0.0

    # Проверяем сохранение сумм и валют операции и платежа
    assert "amount" in facts.columns
    assert "currency_code" in facts.columns
    assert "payment_amount" in facts.columns
    assert "payment_currency_code" in facts.columns

    assert facts["amount"].tolist() == [-160.89, -64.0]
    assert facts["currency_code"].tolist() == ["RUB", "RUB"]
    assert facts["payment_amount"].tolist() == [-160.89, -64.0]
    assert facts["payment_currency_code"].tolist() == ["RUB", "RUB"]

    # Проверяем справочники
    assert len(tables["dim_cards"]) == 2
    assert len(tables["dim_categories"]) == 2
