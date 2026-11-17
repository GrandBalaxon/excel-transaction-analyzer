import argparse
import logging
from pathlib import Path

from src.pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(funcName)s - %(lineno)s - %(levelname)s - %(message)s"
)


def main() -> None:
    """Точка входа для CLI."""
    parser = argparse.ArgumentParser(description="Transactions ETL Pipeline")

    # Создаем подкоманды (run, validate и т.д.)
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Команда 'run' для запуска пайплайна
    run_parser = subparsers.add_parser("run", help="Run the ETL pipeline")
    run_parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to the source Excel file (e.g., data/operations.xlsx)"
    )

    args = parser.parse_args()

    if args.command == "run":
        file_path = Path(args.file)
        if not file_path.exists():
            logging.error(f"File not found: {file_path}")
            return
        run_pipeline(file_path)


if __name__ == "__main__":
    main()
