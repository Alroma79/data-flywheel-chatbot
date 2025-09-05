import pytest
import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..',)))

def pytest_configure(config):
    """
    Configure test environment before running tests.
    """
    # Use main database for testing to ensure schema consistency
    test_db_path = 'backend/chatbot.db'
    
    # Set environment variable for database URL
    os.environ['DATABASE_URL'] = f'sqlite:///{test_db_path}'
    
    # Import and initialize database after setting environment
    from backend.app.init_db import init_database
    init_database()