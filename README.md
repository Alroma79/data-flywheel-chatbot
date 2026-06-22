# Data Flywheel Chatbot 🤖

[![CI](https://github.com/Alroma79/data-flywheel-chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/Alroma79/data-flywheel-chatbot/actions/workflows/ci.yml)

A dynamic, configurable chatbot API built with FastAPI that supports multiple AI models, database persistence, and real-time configuration updates.

## 🚀 Live Demo
The chatbot is deployed on **Railway**:  
[https://flywheel-bot-production.up.railway.app](https://flywheel-bot-production.up.railway.app)

- **Streaming** responses in real time via Server-Sent Events.  
- Backed by **PostgreSQL** for persistent configs and feedback.  
- Includes a `/current_time` endpoint returning current UTC timestamp.  
- Built with **FastAPI**, **LangChain**, and **OpenAI GPT-4o** integration.

## 🧰 Quick Start (Local)
```bash
# Clone and install
git clone https://github.com/Alroma79/data-flywheel-chatbot.git
cd data-flywheel-chatbot
pip install -r backend/app/requirements.txt

# Set env vars
cp .env.example .env
# edit OPENAI_API_KEY and DATABASE_URL (Postgres or SQLite)

# Run locally
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## 🎬 Demo & Resources

- **📹 Demo GIF:** [90-second workflow demo](docs/demo.gif) *(Upload → Chat → Feedback → History)*
- **🔗 API Collection:** [Postman Collection](docs/Flywheel.postman_collection.json) - Import for instant API testing
- **🌱 Demo Seed:** Run `./scripts/seed_demo.sh` to populate with sample data
- **🚀 Deploy to Railway:** [Railway Deployment Guide](docs/DEPLOY_RAILWAY.md)

## 🚀 Features

- **Dynamic AI Model Configuration**: Switch between different OpenAI models and adjust parameters on-the-fly
- **PostgreSQL Persistence**: Store chat history, user feedback, and configurations in a Railway-ready PostgreSQL instance (SQLite remains an optional local fallback)
- **Feedback Attribution**: Link each rating to the exact assistant response, model, and chatbot configuration that produced it
- **Flywheel Analytics**: Compare approval rate, feedback coverage, response volume, and latency by configuration
- **Internal Dashboard**: Review configuration metrics and negative feedback examples directly in the web interface
- **Time Utility Endpoint**: Quickly fetch the current UTC timestamp via the lightweight `/current_time` endpoint
- **RESTful API**: Clean, well-documented API endpoints with automatic OpenAPI documentation
- **Error Handling & Logging**: Comprehensive error handling with structured logging
- **Input Validation**: Robust input sanitization and validation using Pydantic
- **CORS Support**: Configurable CORS settings for frontend integration
- **Docker Support**: Containerized deployment with Docker Compose

## 🎯 Why These Choices?

**Keyword/FTS Retrieval for Explainability:** Simple keyword matching provides transparent, debuggable knowledge retrieval with clear relevance scoring. Users can see exactly why specific sources were selected.

**Framework-Free UI for Determinism:** Vanilla HTML/CSS/JavaScript eliminates framework complexity, ensures predictable behavior, and makes the codebase accessible to any developer regardless of framework preferences.

**Docker for Reproducibility:** Containerization guarantees consistent deployment across environments, from local development to cloud production, with identical runtime behavior.

**SQLite for Demo Speed:** File-based database enables instant setup without external dependencies, perfect for demos and development. Production deployments can easily switch to PostgreSQL.

## 🔒 Security Notes

- **Protected Endpoints:** `/api/v1/config` (POST) and `/api/v1/chat-history` (GET) require `Authorization: Bearer <APP_TOKEN>` header
- **Knowledge Caps:** Maximum 3 knowledge sources per response, ~2.5k character context limit for safety
- **CORS Configuration:** Restrict origins in production: `CORS_ORIGINS=["https://yourdomain.com"]`
- **Input Validation:** All inputs sanitized and validated using Pydantic schemas
- **Rate Limiting:** Configurable (not enforced by default)

## 🏗️ Architecture

```
data-flywheel-chatbot/
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── main.py          # FastAPI application setup
│       ├── routes.py        # API endpoints
│       ├── models.py        # SQLAlchemy ORM models
│       ├── schemas.py       # Pydantic validation schemas
│       ├── db.py           # Database configuration
│       ├── config.py       # Application configuration
│       ├── utils.py        # Utility functions
│       ├── init_db.py      # Database initialization
│       └── requirements.txt
├── docker/
│   ├── backend.Dockerfile
│   └── docker-compose.yml
├── frontend/               # Frontend application (if applicable)
├── .env                   # Environment variables
├── .gitignore
└── README.md
```

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- PostgreSQL (Railway managed instance or local server)
- OpenAI API Key

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Alroma79/data-flywheel-chatbot.git
   cd data-flywheel-chatbot
   ```

2. **Set up Python virtual environment**
   ```bash
   cd backend
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   cd app
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   # Required
   OPENAI_API_KEY=your_openai_api_key_here
   
# Optional (defaults provided)
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/chatbot
# To experiment with SQLite locally (not recommended for production), use:
# DATABASE_URL=sqlite:///./chatbot.db
   DEBUG=false
   CORS_ORIGINS=*
   DEFAULT_MODEL=gpt-4o
   DEFAULT_TEMPERATURE=0.7
   LOG_LEVEL=INFO
   ```

   The backend expects a PostgreSQL database by default; point `DATABASE_URL` to your Railway connection string or a local Postgres instance before starting the server.

5. **Initialize the database**
   ```bash
   python -c "from init_db import init_database; init_database()"
   ```

6. **Run the application**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

The API will be available at `http://localhost:8000`

### Docker Deployment

1. **Using Docker Compose**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

## 📚 API Documentation

Once the application is running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

### Key Endpoints

#### Chat
- `POST /api/v1/chat` - Send a message to the chatbot
- `GET /api/v1/chat-history` - Retrieve chat history

#### Configuration
- `GET /api/v1/config` - Get current chatbot configuration
- `POST /api/v1/config` - Update chatbot configuration

#### Feedback
- `POST /api/v1/feedback` - Submit user feedback
- `GET /api/v1/feedback` - Retrieve feedback entries

Feedback requests can include `response_id`, the `assistant_message_id` returned
by the chat endpoint. The backend derives the associated configuration
automatically.

#### Flywheel Analytics
- `GET /api/v1/analytics/configurations` - Configuration-level response and feedback metrics
- `GET /api/v1/analytics/negative-feedback` - Recent negative examples with prompt, response, model, and configuration

Analytics endpoints require `Authorization: Bearer <APP_TOKEN>` when
`APP_TOKEN` is configured.

Open the application and select **Flywheel Analytics** in the sidebar to view
the dashboard. If production analytics are protected, enter `APP_TOKEN`; it is
kept in browser session storage and cleared when the browser session ends.

#### Health
- `GET /` - API status and version
- `GET /health` - Health check endpoint

#### Utility
- `GET /current_time` - Current UTC time in ISO 8601 format

### Example Usage

**Send a chat message:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello, how can you help me?"}'
```

**Update chatbot configuration:**
```bash
curl -X POST "http://localhost:8000/api/v1/config" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "custom_config",
       "config_json": {
         "system_prompt": "You are a helpful assistant specialized in data analysis.",
         "model": "gpt-4o",
         "temperature": 0.5,
         "max_tokens": 1000
       }
     }'
```

## 🔧 Configuration

The application supports various configuration options through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `DATABASE_URL` | Database connection string | `sqlite:///./chatbot.db` |
| `DEBUG` | Enable debug mode | `false` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `DEFAULT_MODEL` | Default OpenAI model | `gpt-4o` |
| `DEFAULT_TEMPERATURE` | Default temperature setting | `0.7` |
| `LOG_LEVEL` | Logging level | `INFO` |

## 🧪 Testing

Run tests using pytest:
```bash
pytest tests/
```

## 💬 Multi-turn Validation + Troubleshooting

### Overview
The chatbot supports multi-turn conversations using session-based chat history. Each conversation maintains context across multiple messages through a unique session ID.

### Database Schema
The chat_history table uses the following schema:
- `id`: Primary key identifier
- `session_id`: Unique session identifier (UUID)
- `role`: Message role ('user' or 'assistant')
- `content`: Message content
- `created_at`: Timestamp of message creation
- `user_id`: Optional user identifier

### Validation Tests
Test coverage includes:
1. **Session Generation**: First `/api/v1/chat` call without session_id returns new session_id
2. **Context Preservation**: Subsequent calls with same session_id maintain conversation context
3. **Session Management**: `/api/v1/sessions` endpoints for listing and deleting sessions

### Troubleshooting

#### Common Issues

**Issue: "No session_id returned"**
- **Cause**: Database migration not applied or OpenAI mock failing
- **Solution**: Run `python -c "from app.migrations.add_session_columns import run_migration; run_migration('backend/chatbot.db')"`

**Issue: "Context not maintained across turns"**
- **Cause**: Session ID not properly stored or retrieved
- **Solution**: Check database contains messages with matching session_id: `sqlite3 backend/chatbot.db "SELECT * FROM chat_history WHERE session_id='<your_session_id>';"`

**Issue: "Tests failing with import errors"**
- **Cause**: Incorrect Python path or module imports
- **Solution**: Ensure tests run from backend directory: `cd backend && python -m pytest tests/test_chat_sessions.py -v`

#### Database Validation
Check chat_history schema:
```bash
sqlite3 backend/chatbot.db "PRAGMA table_info(chat_history);"
```

Expected output should include columns: id, session_id, role, content, created_at, user_id

#### End-to-End Test
1. Send first message: `curl -X POST "http://localhost:8000/api/v1/chat" -H "Content-Type: application/json" -d '{"message": "Hello"}'`
2. Extract session_id from response
3. Send follow-up: `curl -X POST "http://localhost:8000/api/v1/chat" -H "Content-Type: application/json" -d '{"message": "What did I just say?", "session_id": "<session_id>"}'`
4. Verify response acknowledges previous message

## 📝 Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints where applicable
- Add docstrings to all functions and classes
- Maintain test coverage above 80%

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 🚀 Deployment

### Production Considerations
- Use PostgreSQL for production databases
- Set up proper logging and monitoring
- Configure rate limiting
- Use environment-specific configuration files
- Set up SSL/TLS certificates
- Implement proper backup strategies

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

For support and questions:
- Create an issue on GitHub
- Contact: alroma79@gmail.com

## 🔄 Changelog

### v1.0.0
- Initial release with dynamic configuration support
- Database persistence for chat history and feedback
- Comprehensive error handling and logging
- Docker support for easy deployment
