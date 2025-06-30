import logging
from pathlib import Path

# Проверка на повторный импорт
if not logging.root.handlers:
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    file_handler = logging.FileHandler(filename=log_dir / "tests.log", mode="w", encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(funcName)s - %(lineno)s - %(levelname)s - %(message)s")
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)