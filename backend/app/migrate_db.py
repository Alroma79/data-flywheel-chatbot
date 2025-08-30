"""
Database migration script for the Data Flywheel Chatbot.

This script handles database schema migrations to add missing columns
to existing tables.
"""

import sqlite3
import sys
from datetime import datetime
from .utils import setup_logging

# Initialize logging
logger = setup_logging()


def migrate_chatbot_config_table(db_path: str = "backend/chatbot.db"):
    """
    Migrate the chatbot_config table to add missing columns.
    
    Args:
        db_path: Path to the SQLite database file
    """
    try:
        logger.info("Starting chatbot_config table migration...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(chatbot_config)")
        columns = cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        
        logger.info(f"Current columns: {existing_columns}")
        
        # Add missing columns
        migrations_needed = []
        
        if 'is_active' not in existing_columns:
            migrations_needed.append(
                "ALTER TABLE chatbot_config ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL"
            )
            
        if 'tags' not in existing_columns:
            migrations_needed.append(
                "ALTER TABLE chatbot_config ADD COLUMN tags JSON"
            )
            
        if 'created_at' not in existing_columns:
            migrations_needed.append(
                "ALTER TABLE chatbot_config ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
            )
        
        # Execute migrations
        for migration in migrations_needed:
            logger.info(f"Executing: {migration}")
            cursor.execute(migration)
            
        # Update existing records to have proper created_at if it was just added
        if 'created_at' not in existing_columns:
            cursor.execute("""
                UPDATE chatbot_config 
                SET created_at = COALESCE(updated_at, CURRENT_TIMESTAMP)
                WHERE created_at IS NULL
            """)
        
        conn.commit()
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(chatbot_config)")
        new_columns = cursor.fetchall()
        logger.info("Migration completed. New schema:")
        for col in new_columns:
            logger.info(f"  {col[1]} ({col[2]}) - nullable: {not col[3]}, default: {col[4]}")
            
        conn.close()
        logger.info("✅ chatbot_config table migration completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        raise


def main():
    """Main migration function."""
    try:
        migrate_chatbot_config_table()
        print("✅ Database migration completed successfully")
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
