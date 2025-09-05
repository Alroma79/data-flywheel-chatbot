import sqlite3
import os
from typing import List, Optional

def run_migration(db_path: Optional[str] = None) -> List[str]:
    """
    Applies database schema migrations with robust error handling.
    
    Args:
        db_path: Path to the SQLite database file
    
    Returns:
        List of applied migration steps.
    """
    applied_migrations = []
    
    # Use default path if not provided
    if not db_path:
        db_path = 'chatbot.db'
    
    # Ensure the directory exists, handling empty paths
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing table info
        cursor.execute("PRAGMA table_info(chat_history)")
        columns = {col[1] for col in cursor.fetchall()}
        
        migration_needed = False
        columns_to_add = {
            'session_id': "TEXT DEFAULT ''",
            'role': "TEXT NOT NULL DEFAULT 'user'",
            'content': "TEXT",
            'user_id': "TEXT"
        }
        
        # Check which columns are missing
        for column, definition in columns_to_add.items():
            if column not in columns:
                try:
                    alter_sql = f"ALTER TABLE chat_history ADD COLUMN {column} {definition}"
                    cursor.execute(alter_sql)
                    migration_needed = True
                    applied_migrations.append(f"Added column {column}")
                except sqlite3.OperationalError as e:
                    print(f"Could not add column {column}: {e}")
        
        # Migrate existing data if needed
        if migration_needed:
            # Backup and transform existing data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history_backup AS 
                SELECT id, user_message, bot_reply, timestamp 
                FROM chat_history
            """)
            
            # Populate new columns with default/transformed data
            cursor.execute("""
                UPDATE chat_history 
                SET 
                    session_id = IFNULL(session_id, ''),
                    role = CASE 
                        WHEN user_message IS NOT NULL THEN 'user'
                        WHEN bot_reply IS NOT NULL THEN 'assistant'
                        ELSE 'unknown'
                    END,
                    content = COALESCE(user_message, bot_reply, '')
            """)
            
            conn.commit()
            print("Database migration completed successfully.")
        
    except sqlite3.Error as e:
        print(f"Migration error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
    
    return applied_migrations

def migration_summary() -> dict:
    """
    Provides a summary of the migration.
    
    Returns:
        Dict with migration details.
    """
    return {
        "version": 1,
        "description": "Add session tracking columns to chat history",
        "columns_added": ["session_id", "role", "content", "user_id"]
    }

if __name__ == '__main__':
    run_migration()