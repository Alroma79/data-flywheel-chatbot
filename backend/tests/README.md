# Testing Multi-Turn Conversation Support

## Running Tests

```bash
# From the backend directory
pytest tests/
```

## Test Coverage

- `test_chat_without_session_id`: Ensures a new session is created when no session ID is provided
- `test_multi_turn_conversation`: Verifies that conversation context is maintained across multiple turns
- `test_sessions_endpoints`: Checks listing and deletion of conversation sessions

## Mocking

Tests use a mock for the OpenAI API to avoid making real API calls during testing.