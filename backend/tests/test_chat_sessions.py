import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..',)))

from backend.app.main import app  # Relative import

client = TestClient(app)

def mock_openai_chat_completion(*args, **kwargs):
    """Mock OpenAI chat completion to pass through the message."""
    class MockChoice:
        def __init__(self, content):
            class MockMessage:
                def __init__(self, content):
                    self.content = content
            self.message = MockMessage(content)
    
    class MockResponse:
        def __init__(self, content):
            self.choices = [MockChoice(content)]
    
    # Extract the user message content for the response
    user_message = kwargs['messages'][-1]['content']
    return MockResponse(f"Response to: {user_message}")

@pytest.fixture
def mock_openai(monkeypatch):
    """Patch OpenAI client to avoid real API calls."""
    # Mock the knowledge processor to return an empty list
    mock_knowledge_processor = MagicMock()
    mock_knowledge_processor.search_knowledge.return_value = []
    monkeypatch.setattr('backend.app.routes.KnowledgeProcessor', lambda: mock_knowledge_processor)

    # Mock the LLM service to return test responses
    def mock_llm_chat(messages, **kwargs):
        user_message = messages[-1]['content'] if messages else "test"
        return {
            'content': f"Response to: {user_message}",
            'usage': {'total_tokens': 10},
            'latency_ms': 50
        }

    # Patch the llm service
    monkeypatch.setattr('backend.app.routes.llm.chat', mock_llm_chat)
    yield

def test_chat_without_session_id(mock_openai):
    """Test that a chat without session_id generates a new session."""
    response = client.post("/api/v1/chat", json={"message": "Hello, how are you?"})
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that a session_id is returned
    assert "session_id" in data
    assert data["session_id"]  # Not an empty string
    assert data["reply"].strip()  # Ensure non-empty reply

def test_multi_turn_conversation(mock_openai):
    """Test that a multi-turn conversation maintains context."""
    # First turn
    first_response = client.post("/api/v1/chat", json={"message": "Tell me a story"})
    first_session_id = first_response.json()["session_id"]
    
    # Second turn with the same session_id
    second_response = client.post("/api/v1/chat", json={
        "message": "Continue the story", 
        "session_id": first_session_id
    })
    
    assert second_response.status_code == 200
    data = second_response.json()
    
    # Verify session_id is consistent
    assert data["session_id"] == first_session_id
    assert data["reply"].strip()  # Ensure non-empty reply

def test_sessions_endpoints(mock_openai):
    """Test sessions listing and deletion."""
    # Create a few conversations
    sessions = []
    for _ in range(3):
        response = client.post("/api/v1/chat", json={"message": f"Test message {_}"})
        # Handle the case where the session_id might not be present
        session_id = response.json().get("session_id")
        assert session_id is not None, f"No session_id found in response: {response.json()}"
        sessions.append(session_id)
    
    # List sessions
    list_response = client.get("/api/v1/sessions")
    assert list_response.status_code == 200
    session_list = list_response.json()
    assert len(session_list) >= 3  # At least the sessions we just created
    
    # Delete a session
    delete_response = client.delete(f"/api/v1/sessions/{sessions[0]}")
    assert delete_response.status_code == 200
    assert delete_response.json()["session_id"] == sessions[0]