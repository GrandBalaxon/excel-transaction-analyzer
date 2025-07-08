import hashlib
import json
import logging
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, ParamSpec, TypeVar, cast

logger = logging.getLogger("decorators")

T = TypeVar("T")
P = ParamSpec("P")


def backlogging(backlog_file_name: str = "application_log.json") -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Универсальный декоратор для кэширования результатов функций.

    :param backlog_file_name: Имя файла для хранения кэша (по умолчанию "backlogged_data.json")
    """

    def wrapper(function: Callable[P, T]) -> Callable[P, T]:
        @wraps(function)
        def inner_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Генерируем уникальный ключ на основе аргументов
            try:
                # Создаем стабильное представление аргументов
                args_repr = repr((args, kwargs))
                key = hashlib.sha256(args_repr.encode()).hexdigest()
            except Exception as e:
                logger.error(f"Ошибка создания ключа кэша: {str(e)}")
                return function(*args, **kwargs)

            logger.info(f"Поиск кэша для функции {function.__name__} c ключом {key[:8]}...")

            backlog_file_path = Path(__file__).parent.parent / "logs" / backlog_file_name
            backlog_file_path.touch(exist_ok=True)

            try:
                with open(backlog_file_path, encoding="UTF-8") as json_file:
                    backlog_dict: Dict[str, Any] = json.load(json_file)
                logger.info("Данные с бэк-лога успешно получены.")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Ошибка загрузки кэша: {str(e)}")
                backlog_dict = {}

            if function.__name__ not in backlog_dict:
                backlog_dict[function.__name__] = {}

            cache = backlog_dict[function.__name__]

            if key in cache and cache[key]:
                return cast(T, cache[key])
            else:
                result = function(*args, **kwargs)

                if result is not None:
                    cache[key] = result

                    with open(backlog_file_path, "w", encoding="UTF-8") as json_file:
                        json.dump(backlog_dict, json_file, indent=2, ensure_ascii=False)
                    logger.info(f"Данные успешно записаны в файл {backlog_file_name}.")

                return result

        return inner_wrapper

    return wrapper
