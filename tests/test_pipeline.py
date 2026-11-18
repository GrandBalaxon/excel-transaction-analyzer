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


def test_transform_calculates_amount_rub(raw_transactions_df):
    """Проверяет расчет рублевой суммы с учетом валют операции и платежа."""
    df = raw_transactions_df.copy()

    # Операция в USD, платеж в RUB
    df.loc[0, "Сумма операции"] = -100.0
    df.loc[0, "Валюта операции"] = "USD"
    df.loc[0, "Сумма платежа"] = -95.0
    df.loc[0, "Валюта платежа"] = "RUB"

    # Операция в RUB, платеж в CNY
    df.loc[1, "Сумма операции"] = -64.0
    df.loc[1, "Валюта операции"] = "RUB"
    df.loc[1, "Сумма платежа"] = -420.0
    df.loc[1, "Валюта платежа"] = "CNY"

    # Операция и платеж в CNY
    df.loc[2, "Статус"] = "OK"
    df.loc[2, "Сумма операции"] = -55.0
    df.loc[2, "Валюта операции"] = "CNY"
    df.loc[2, "Сумма платежа"] = -55.0
    df.loc[2, "Валюта платежа"] = "CNY"

    result = transform(df)
    facts = result["facts"]

    assert facts["amount_rub"].tolist() == [-95.0, -64.0, None]
