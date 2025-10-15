"""
Database initialization script for the Data Flywheel Chatbot.

This script creates all database tables based on the SQLAlchemy models.
Run this script to set up the database schema.
"""

from pathlib import Path

from sqlalchemy.engine.url import make_url

from .db import Base, engine
from .models import Feedback, ChatHistory, ChatbotConfig, KnowledgeFile  # noqa: F401
from .utils import setup_logging

# Initialize logging
logger = setup_logging()


def apply_migrations(db_path: str) -> None:
    """Apply SQLite-specific migrations."""
    try:
        from .migrations.add_session_columns import run_migration

        run_migration(db_path)
    except Exception as exc:  # pragma: no cover - migration best-effort
        logger.error(f"Migration failed: {exc}")
        raise


def init_database() -> None:
    """
    Initialize the database by creating all tables.

    This function creates all tables defined in the models module
    if they don't already exist. SQLite migrations are applied only
    when the SQLite backend is detected.
    """
    try:
        url = make_url(engine.url)
        backend = url.get_backend_name()
        logger.info(f"Detected database backend: {backend}")

        db_path = None
        if backend == "sqlite":
            db_path = url.database or "chatbot.db"
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")

        if backend == "sqlite" and db_path:
            apply_migrations(db_path)
        else:
            logger.info("Skipping SQLite-specific migrations for non-SQLite backend.")

        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Created tables: {', '.join(tables)}")

    except Exception as exc:
        logger.error(f"Failed to create database tables: {exc}")
        raise


if __name__ == "__main__":
    init_database()
