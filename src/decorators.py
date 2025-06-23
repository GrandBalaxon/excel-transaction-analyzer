import json
import logging
from functools import wraps
from pathlib import Path
from typing import Callable, TypeVar, ParamSpec, List, Dict, Any

logger = logging.getLogger("decorators")

T = TypeVar("T")
P = ParamSpec("P")


def backlogging(backlog_file_name: str = "backlogged_data.json") -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Универсальный декоратор для кэширования результатов функций.

    :param backlog_file_name: Имя файла для хранения кэша (по умолчанию "backlogged_data.json")
    """
    def wrapper(function: Callable[P, T]) -> Callable[P, T]:
        @wraps(function)
        def inner_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            logger.info(f"Начат поиск результата для функции {function.__name__} c параметрами {args, kwargs}.")

            backlog_file_path = Path(__file__).parent.parent / "data" / backlog_file_name
            backlog_file_path.touch(exist_ok=True)

            try:
                with open(backlog_file_path) as json_file:
                    backlog_dict: Dict[str, Any] = json.load(json_file)
                logger.info("Данные с бэк-лога успешно получены.")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Ошибка загрузки кэша: {str(e)}")
                backlog_dict = {}

            if function.__name__ not in backlog_dict:
                backlog_dict[function.__name__] = {}

            key = args + tuple(sorted(kwargs.items()))
            cache = backlog_dict[function.__name__]

            if key in cache:
                return cache[key]
            else:
                result = function(*args, **kwargs)
                cache[key] = result

                # запись обратно в файл
                with open(backlog_file_path, "w", encoding="UTF-8") as json_file:
                    json.dump(backlog_dict, json_file, indent=2)
                    logger.info(f"Данные успешно записаны в файл {backlog_file_name}.")

                return result

        return inner_wrapper

    return wrapper
