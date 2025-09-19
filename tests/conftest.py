"""
Test configuration and fixtures for the Data Flywheel Chatbot test suite.

This module provides shared test fixtures and configuration to ensure
tests run in isolation with controlled environments.
"""

import os
import sys
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Add backend app to Python path for imports
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Set up the test environment with controlled settings.

    This fixture runs automatically for all tests and ensures:
    - Demo mode is enabled for predictable responses
    - In-memory database is used for isolation
    - Settings cache is cleared
    """
    # Set environment variables for testing
    test_env = {
        "DEMO_MODE": "true",
        "DATABASE_URL": "sqlite:///:memory:",
        "OPENAI_API_KEY": "test-key-for-testing",
        "DEBUG": "true",
        "DEFAULT_MODEL": "gpt-4o",
        "DEFAULT_TEMPERATURE": "0.7"
    }

    with patch.dict(os.environ, test_env):
        # Clear the settings cache to force reload with test environment
        from app.config import get_settings
        if hasattr(get_settings, 'cache_clear'):
            get_settings.cache_clear()

        yield

        # Clean up after tests
        if hasattr(get_settings, 'cache_clear'):
            get_settings.cache_clear()


@pytest.fixture
def test_client():
    """
    Provide a FastAPI TestClient for making HTTP requests in tests.

    This fixture creates a fresh TestClient instance for each test,
    ensuring test isolation.
    """
    from app.main import app
    return TestClient(app)


@pytest.fixture
def mock_llm():
    """
    Mock the LLM service to return predictable responses in tests.

    This fixture ensures tests don't make actual API calls and
    receive consistent, testable responses.
    """
    def mock_chat(messages, **kwargs):
        user_message = messages[-1]['content'] if messages else "test"
        return {
            'content': f"Test response to: {user_message}",
            'usage': {'total_tokens': 10},
            'latency_ms': 50
        }

    with patch('backend.app.services.llm.chat', side_effect=mock_chat):
        yield mock_chat


@pytest.fixture
def mock_knowledge_processor():
    """
    Mock the KnowledgeProcessor to return controlled results.

    This fixture ensures knowledge-related tests have predictable
    search results without requiring actual file uploads.
    """
    from unittest.mock import MagicMock

    mock_processor = MagicMock()
    mock_processor.search_knowledge.return_value = []

    with patch('backend.app.routes.KnowledgeProcessor', return_value=mock_processor):
        yield mock_processor


@pytest.fixture
def sample_chat_request():
    """Provide a sample chat request for testing."""
    return {
        "message": "Hello, this is a test message",
        "session_id": "test-session-123",
        "user_id": "test-user"
    }


@pytest.fixture
def sample_feedback_request():
    """Provide a sample feedback request for testing."""
    return {
        "message": "Test message for feedback",
        "user_feedback": "thumbs_up",
        "comment": "This is a test comment"
    }


@pytest.fixture(autouse=True)
def isolate_database():
    """
    Ensure each test uses a fresh database.

    This fixture runs automatically and ensures database state
    doesn't leak between tests.
    """
    from app.db import engine, Base

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield

    # Clean up after test
    Base.metadata.drop_all(bind=engine)