# Data Flywheel Chatbot 🤖

A dynamic, configurable chatbot API built with FastAPI that supports multiple AI models, database persistence, and real-time configuration updates.

## 🚀 Features

- **Dynamic AI Model Configuration**: Switch between different OpenAI models and adjust parameters on-the-fly
- **Database Persistence**: Store chat history, user feedback, and configurations in PostgreSQL or SQLite
- **RESTful API**: Clean, well-documented API endpoints with automatic OpenAPI documentation
- **Error Handling & Logging**: Comprehensive error handling with structured logging
- **Input Validation**: Robust input sanitization and validation using Pydantic
- **CORS Support**: Configurable CORS settings for frontend integration
- **Docker Support**: Containerized deployment with Docker Compose

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
- PostgreSQL (optional, SQLite is used by default)
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
   DATABASE_URL=sqlite:///./chatbot.db
   DEBUG=false
   CORS_ORIGINS=*
   DEFAULT_MODEL=gpt-4o
   DEFAULT_TEMPERATURE=0.7
   LOG_LEVEL=INFO
   ```

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

#### Health
- `GET /` - API status and version
- `GET /health` - Health check endpoint

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
