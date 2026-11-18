import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger("database")

load_dotenv()

# Read connection settings
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "transactions_db")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5433")

# Build the connection URL
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def create_db_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine for the given database."""
    try:
        db_engine = create_engine(database_url, echo=False)
        logger.info("SQLAlchemy engine created.")
        return db_engine
    except Exception as e:
        logger.exception(f"Failed to create the database engine: {e}")
        raise


# Create the production engine
engine = create_db_engine(DATABASE_URL)


class Base(DeclarativeBase):
    """Base class for all table models."""
    pass


def init_db(db_engine: Engine) -> None:
    """Create all tables in the database if they do not exist yet."""
    # Local import so that SQLAlchemy registers the models before creating tables
    from src import models  # noqa: F401

    logger.info("Initializing database schema (creating tables)...")
    Base.metadata.create_all(bind=db_engine)
