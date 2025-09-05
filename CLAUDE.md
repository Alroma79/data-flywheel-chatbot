# Claude Code Configuration for Data Flywheel Chatbot

## Project Overview

Data Flywheel Chatbot is a FastAPI-based chatbot API with dynamic AI model configuration, database persistence, and real-time updates. The project uses Python/FastAPI for the backend with PostgreSQL/SQLite for data storage.

## Project Structure

```
data-flywheel-chatbot/
├── backend/
│   └── app/
│       ├── main.py          # FastAPI application setup
│       ├── routes.py        # API endpoints
│       ├── models.py        # SQLAlchemy ORM models
│       ├── schemas.py       # Pydantic validation schemas
│       ├── db.py           # Database configuration
│       ├── config.py       # Application configuration
│       ├── utils.py        # Utility functions
│       └── init_db.py      # Database initialization
├── frontend/               # Static frontend files
├── tests/                  # Test suite
├── docker/                 # Docker configuration
└── scripts/               # Utility scripts
```

## Development Commands

### Local Development
```bash
# Start the backend server (primary development command)
cd backend && uvicorn app.main:app --reload

# Initialize database
cd backend/app && python -c "from init_db import init_database; init_database()"

# Install dependencies
cd backend/app && pip install -r requirements.txt
```

### Docker Development
```bash
# Build and start all services
docker compose up --build

# Run tests in Docker
docker compose run --rm test

# Start in background
docker compose up -d
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_frontend_integration.py -v

# Run tests with coverage
python -m pytest tests/ --cov=app

# Test Docker setup
./scripts/test_docker.sh  # Linux/Mac
./scripts/test_docker.ps1 # Windows
```

### Code Quality
```bash
# Format code
black backend/app/

# Lint code
flake8 backend/app/

# Type checking (if mypy is available)
mypy backend/app/
```

## Environment Configuration

Required environment variables:
- `OPENAI_API_KEY` - OpenAI API key (required)
- `DATABASE_URL` - Database connection string (default: sqlite:///./chatbot.db)
- `DEBUG` - Enable debug mode (default: false)
- `CORS_ORIGINS` - Allowed CORS origins (default: *)

## Key Technologies

- **Backend**: FastAPI, SQLAlchemy, OpenAI API, Pydantic
- **Database**: PostgreSQL (production), SQLite (development)
- **Testing**: pytest, httpx
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions

## API Endpoints

### Core Endpoints
- `GET /` - Frontend and API status
- `GET /health` - Health check
- `POST /api/v1/chat` - Send chat message
- `GET /api/v1/chat-history` - Retrieve chat history
- `POST /api/v1/config` - Update chatbot configuration
- `GET /api/v1/config` - Get current configuration
- `POST /api/v1/feedback` - Submit user feedback

### Development URLs
- Frontend: http://localhost:8000/
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database Models

Key models:
- `ChatSession` - Chat conversation tracking
- `ChatMessage` - Individual messages
- `UserFeedback` - User ratings and feedback
- `Configuration` - Dynamic AI model configurations
- `KnowledgeSource` - Document/knowledge base entries

## Testing Strategy

- **Integration Tests**: Full API workflow testing
- **Frontend Tests**: Static file serving and UI integration
- **Knowledge Tests**: Document upload and retrieval
- **Docker Tests**: Container deployment validation
- **CI/CD**: Automated testing on push/PR

## Development Notes

1. **Virtual Environment**: Backend uses `backend/venv/` for Python dependencies
2. **Database**: SQLite for development, PostgreSQL recommended for production
3. **CORS**: Configured for localhost development (ports 3000, 8000)
4. **Static Files**: Frontend served from `/frontend` directory
5. **Logging**: Structured logging with configurable levels

## Common Tasks

### Adding New API Endpoint
1. Define route in `backend/app/routes.py`
2. Add Pydantic schema in `backend/app/schemas.py` 
3. Update database models if needed in `backend/app/models.py`
4. Add tests in `tests/`

### Database Changes
1. Modify models in `backend/app/models.py`
2. Update initialization in `backend/app/init_db.py`
3. Test with fresh database: `rm chatbot.db && python -c "from init_db import init_database; init_database()"`

### Adding Dependencies
1. Update `requirements.txt` (root level) and `backend/app/requirements.txt`
2. Rebuild Docker containers: `docker compose up --build`
3. Update virtual environment: `pip install -r requirements.txt`

## Troubleshooting

### Common Issues
- **Port conflicts**: Default port 8000, check for conflicts
- **Database locks**: Remove `chatbot.db` and reinitialize if corrupted  
- **CORS issues**: Check origins configuration in `backend/app/main.py`
- **Docker issues**: Use `docker compose logs` for debugging

### Performance Considerations
- OpenAI API rate limits
- Database query optimization for chat history
- Static file caching for frontend assets