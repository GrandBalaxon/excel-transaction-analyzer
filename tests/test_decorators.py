import json

import pytest

from src.decorators import backlogging


# Тестовая функция с декоратором
@backlogging()
def function_(a, b):
    return a + b


def test_backlogging_first_call_no_cache():
    """Тест первого вызова функции (кэш пуст)"""
    result = function_(1, 2)

    assert result == 3
    # Проверяем что данные были записаны в "кэш"
    pytest.importorskip("src.decorators").json.dump.assert_called_once()


def test_backlogging_second_call_with_cache(mocker):
    """ Проверяем возврат закэшированного значения при повторном вызове."""
    cached_data = {"function_": {"mocked_hash": 3}}
    mocker.patch("src.decorators.json.load", return_value=cached_data)

    result = function_(1, 2)

    assert result == 3
    # Проверяем что запись в файл НЕ производилась
    pytest.importorskip("src.decorators").json.dump.assert_not_called()


def test_backlogging_error_in_key_generation(mocker):
    """Тест обработки ошибки при генерации ключа."""
    mock_sha256 = mocker.patch("src.decorators.hashlib.sha256")
    mock_sha256.side_effect = Exception("Hash error")

    result = function_(1, 2)

    assert result == 3


def test_backlogging_json_decode_error(mocker):
    """ Тест обработки ошибки чтения JSON файла """
    mocker.patch("src.decorators.json.load", side_effect=json.JSONDecodeError("msg", "doc", 0))

    result = function_(1, 2)

    assert result == 3


def test_backlogging_none_result_not_cached():
    """Тестируем, что None результат не сохраняется в кэш."""

    @backlogging()
    def none_function() -> None:
        return None

    result = none_function()

    assert result is None
    pytest.importorskip("src.decorators").json.dump.assert_not_called()
