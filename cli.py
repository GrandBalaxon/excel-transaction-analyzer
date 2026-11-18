import argparse
import logging
import sys
from pathlib import Path

from src.pipeline import run_pipeline

logger = logging.getLogger(__name__)


def main() -> int:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(funcName)s - %(lineno)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )

    parser = argparse.ArgumentParser(description="Transactions ETL Pipeline")

    # Create subcommands
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # The 'run' command starts the pipeline
    run_parser = subparsers.add_parser("run", help="Run the ETL pipeline")
    run_parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to the source Excel file (e.g., data/operations.xlsx)"
    )

    args = parser.parse_args()

    try:
        if args.command == "run":
            file_path = Path(args.file)
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return 1
            run_pipeline(file_path)
    except Exception:
        logger.exception("Pipeline failed with an unexpected error")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
