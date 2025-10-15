"""
Test configuration and fixtures for the Data Flywheel Chatbot test suite.

This module provides shared test fixtures and configuration to ensure
tests run in isolation with controlled environments.
"""

import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


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
        "DEMO_MODE": "1",  # Explicitly set to 1 for stub mode
        "DATABASE_URL": "sqlite:///:memory:",
        "OPENAI_API_KEY": "sk-test1234",
        "DEBUG": "true",
        "DEFAULT_MODEL": "gpt-4o",
        "DEFAULT_TEMPERATURE": "0.7"
    }

    with patch.dict(os.environ, test_env):
        # Patch OpenAI client to use stub mode
        from unittest.mock import MagicMock
        from app.services import llm

        # Force stub mode in llm service
        def _use_stub():
            return True
        llm._use_stub = _use_stub

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
def mock_llm(monkeypatch):
    """
    Mock the LLM service to return predictable responses in tests.

    This fixture ensures tests don't make actual API calls and
    receive consistent, testable responses.
    """
    def mock_chat(messages, stream=False, **kwargs):
        user_message = messages[-1]['content'] if messages else "test"
        mock_tokens = ["Test", " response", " to:", f" {user_message}"]

        # Streaming logic
        if stream:
            async def token_generator():
                for token in mock_tokens:
                    yield token

                # Simulate end of stream metadata
                yield {
                    'content': f"Test response to: {user_message}",
                    'usage': {'total_tokens': len(mock_tokens)},
                    'latency_ms': 50
                }
            return token_generator()

        # Non-streaming response
        return {
            'content': f"Test response to: {user_message}",
            'usage': {'total_tokens': 10},
            'latency_ms': 50
        }

    # Patch in the specific routes where streaming is used
    from app import services
    with patch.object(services.llm, 'chat', side_effect=mock_chat):
        with patch('app.routes.chat', side_effect=mock_chat):
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
    mock_processor.search_knowledge.return_value = [
        {
            'filename': 'test_doc.txt',
            'file_id': 1,
            'content': 'Sample knowledge content for streaming tests',
            'score': 0.85
        }
    ]

    with patch('app.routes.KnowledgeProcessor', return_value=mock_processor):
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
    from sqlalchemy.orm import sessionmaker
    from app.models import ChatbotConfig, KnowledgeFile

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create a session
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Insert default configurations if not exist
    try:
        # Default chatbot config
        if not db.query(ChatbotConfig).first():
            default_config = ChatbotConfig(
                name="Default Configuration",
                config_json={
                    "system_prompt": "You are a helpful and adaptive assistant.",
                    "model": "gpt-4o",
                    "temperature": 0.7
                },
                is_active=True
            )
            db.add(default_config)

        # Add a dummy knowledge file for testing
        if not db.query(KnowledgeFile).first():
            dummy_file = KnowledgeFile(
                filename="test_doc.txt",
                content_type="text/plain",
                size=100,
                sha256="dummy_sha256"
            )
            db.add(dummy_file)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error setting up test database: {e}")
    finally:
        db.close()

    yield

    # Clean up after test
    Base.metadata.drop_all(bind=engine)