from pathlib import Path

import pandas as pd

from src.pipeline import extract, transform


def test_extract_success(mocker, raw_transactions_df, tmp_path: Path):
    """Check that an Excel file is read successfully."""
    mock_read = mocker.patch("pandas.read_excel", return_value=raw_transactions_df)

    result = extract(tmp_path / "dummy.xlsx")

    assert result is not None
    assert len(result) == 3
    mock_read.assert_called_once()


def test_extract_empty_file(mocker, empty_dataframe, tmp_path: Path):
    """Check the case of an empty Excel file."""
    mocker.patch("pandas.read_excel", return_value=empty_dataframe)

    result = extract(tmp_path / "dummy.xlsx")

    assert result is None


def test_transform_logic(raw_transactions_df):
    """Check the transform logic (cleaning and splitting into tables)."""
    tables = transform(raw_transactions_df)

    # Check that all 4 tables are returned
    assert "dim_cards" in tables
    assert "dim_categories" in tables
    assert "dim_dates" in tables
    assert "facts" in tables

    # Check that the fact table is cleaned
    facts = tables["facts"]
    assert len(facts) == 2
    assert all(facts["status"] == "OK")

    # Check that NaN cashback values are filled
    assert facts["cashback"].isna().sum() == 0
    assert facts["cashback"].iloc[1] == 0.0

    # Check that operation and payment amounts and currencies are kept
    assert "amount" in facts.columns
    assert "currency_code" in facts.columns
    assert "payment_amount" in facts.columns
    assert "payment_currency_code" in facts.columns

    assert facts["amount"].tolist() == [-160.89, -64.0]
    assert facts["currency_code"].tolist() == ["RUB", "RUB"]
    assert facts["payment_amount"].tolist() == [-160.89, -64.0]
    assert facts["payment_currency_code"].tolist() == ["RUB", "RUB"]

    # Check the dimensions
    assert len(tables["dim_cards"]) == 2
    assert len(tables["dim_categories"]) == 2


def test_transform_calculates_amount_rub(raw_transactions_df):
    """Check the ruble amount calculation for different operation and payment currencies."""
    df = raw_transactions_df.copy()

    # Operation in USD, payment in RUB
    df.loc[0, "Сумма операции"] = -100.0
    df.loc[0, "Валюта операции"] = "USD"
    df.loc[0, "Сумма платежа"] = -95.0
    df.loc[0, "Валюта платежа"] = "RUB"

    # Operation in RUB, payment in CNY
    df.loc[1, "Сумма операции"] = -64.0
    df.loc[1, "Валюта операции"] = "RUB"
    df.loc[1, "Сумма платежа"] = -420.0
    df.loc[1, "Валюта платежа"] = "CNY"

    # Operation and payment in CNY
    df.loc[2, "Статус"] = "OK"
    df.loc[2, "Сумма операции"] = -55.0
    df.loc[2, "Валюта операции"] = "CNY"
    df.loc[2, "Сумма платежа"] = -55.0
    df.loc[2, "Валюта платежа"] = "CNY"

    result = transform(df)
    facts = result["facts"]

    assert facts["amount_rub"].iloc[:2].tolist() == [-95.0, -64.0]
    assert pd.isna(facts["amount_rub"].iloc[2])
