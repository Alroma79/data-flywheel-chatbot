# Test Suite Documentation

This directory contains the test suite for the Data Flywheel Chatbot project.

## Test Structure

### Unit Tests (backend/tests/)
- `test_chat_sessions.py` - Chat session management and multi-turn conversations
- Uses TestClient with proper mocking for isolated testing
- All tests should pass offline with no external dependencies

### Integration Tests (tests/)
- `test_frontend_integration.py` - Frontend API integration tests
- `test_knowledge_integration.py` - Knowledge file upload and search tests
- Converted from external HTTP calls to TestClient for reliability

## Test Configuration

### Fixtures (conftest.py)
- `setup_test_environment`: Forces DEMO_MODE=true and in-memory database
- `test_client`: FastAPI TestClient for HTTP request testing
- `mock_llm`: Mocks OpenAI API calls to return predictable responses
- `mock_knowledge_processor`: Mocks knowledge search functionality
- `isolate_database`: Ensures fresh database for each test

### Environment
- Tests run with `DEMO_MODE=true` for predictable, fast responses
- Uses `sqlite:///:memory:` database for complete isolation
- No external HTTP calls or API dependencies
- Settings cache cleared between test sessions

## Running Tests

```bash
# Run all tests quietly
pytest -q

# Show skip reasons
pytest -q -rs

# Run specific test file
pytest tests/test_frontend_integration.py -v

# Run with coverage (if available)
coverage run -m pytest -q
coverage report -m
```

## Known Issues / Expected Skips

Currently, some tests may fail due to:
1. Authentication requirements on certain endpoints
2. Missing knowledge processor implementation details
3. File upload endpoint availability

These are expected and tests will be marked as skipped with clear reasons once identified.

## Test Philosophy

- **Hermetic**: All tests run offline without external dependencies
- **Fast**: Uses demo mode and mocks for quick execution
- **Isolated**: Each test gets fresh database and clean state
- **Predictable**: No random data, consistent responses via mocking