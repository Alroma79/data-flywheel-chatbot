"""
Database initialization script for the Data Flywheel Chatbot.

This script creates all database tables based on the SQLAlchemy models.
Run this script to set up the database schema.
"""

from .db import Base, engine
# Import models to register them with SQLAlchemy
from .models import Feedback, ChatHistory, ChatbotConfig  # noqa: F401
from .utils import setup_logging

# Initialize logging
logger = setup_logging()


def init_database():
    """
    Initialize the database by creating all tables.

    This function creates all tables defined in the models module
    if they don't already exist.
    """
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")

        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Created tables: {', '.join(tables)}")

    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


if __name__ == "__main__":
    init_database()

