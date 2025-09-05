"""
Database initialization script for the Data Flywheel Chatbot.

This script creates all database tables based on the SQLAlchemy models.
Run this script to set up the database schema.
"""

import sqlite3
from pathlib import Path

from .db import Base, engine
# Import models to register them with SQLAlchemy
from .models import Feedback, ChatHistory, ChatbotConfig, KnowledgeFile  # noqa: F401
from .utils import setup_logging

# Initialize logging
logger = setup_logging()

def apply_migrations(db_path):
    # Import local migration script
    from .migrations.add_session_columns import run_migration
    """
    Apply database schema migrations.
    
    Args:
        db_path: Path to the SQLite database file
    """
    # Run migration from the local migration script
    try:
        from .migrations.add_session_columns import run_migration
        run_migration(db_path)
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

def init_database():
    """
    Initialize the database by creating all tables.

    This function creates all tables defined in the models module
    if they don't already exist.
    """
    try:
        # Determine database path based on connection string
        from sqlalchemy.engine.url import make_url
        db_url = str(make_url(engine.url))
        
        # Extract path for SQLite
        if db_url.startswith('sqlite:///'):
            db_path = db_url[10:]
        else:
            logger.warning(f"Unsupported database type: {db_url}")
            db_path = 'chatbot.db'
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        
        # Apply migrations
        apply_migrations(db_path)
        
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