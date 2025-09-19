# Docker Deployment Guide

## Recent Changes
**Updated September 2024**: Consolidated multiple docker-compose.yml files into a single configuration at repository root. The new compose file includes:
- Main backend service with health checks
- Optional PostgreSQL database service (using profiles)
- Test service for automated testing
- Improved volume mappings and environment variable handling

## Overview

This guide covers containerizing and deploying the Data Flywheel Chatbot using Docker and Docker Compose. The containerized application maintains all functionality while providing consistent deployment across environments.

## Docker Image Specifications

### Base Image & Size
- **Base:** `python:3.11-slim` (lightweight Python runtime)
- **Final Size:** ~280MB (optimized for production)
- **Architecture:** Multi-platform (linux/amd64, linux/arm64)

### System Dependencies
The image includes minimal system packages:
- `curl` - Required for health checks
- Standard Python 3.11 runtime libraries

**Justification:** Only essential packages are included to maintain a lean image. PDF processing libraries (PyPDF2, python-docx) are optional Python packages that don't require system dependencies.

### Security Features
- Non-root user execution (implicit in python:slim)
- Minimal attack surface with slim base image
- Health check endpoint for monitoring
- Environment variable configuration (no secrets in image)

## Quick Start Commands

### Using Docker Compose (Recommended)
```bash
# Build and start the application
docker compose up --build

# Run in background
docker compose up -d

# View logs
docker compose logs -f

# Stop the application
docker compose down
```

### Using Docker Directly
```bash
# Build the image
docker build -t flywheel .

# Run the container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your-api-key \
  flywheel

# Run with environment file
docker run -p 8000:8000 --env-file .env flywheel
```

### Using Helper Scripts
```bash
# Linux/Mac
chmod +x scripts/*.sh
./scripts/run_docker.sh

# Windows PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\run_docker.ps1
```

## Running Tests in Container

### Using Docker Compose (Recommended)
```bash
# Run all tests
docker compose run --rm test

# Run with verbose output
docker compose run --rm test pytest -v

# Run specific test file
docker compose run --rm test pytest tests/test_knowledge_integration.py -v
```

### Using Docker Directly
```bash
# Run tests in temporary container
docker run --rm \
  -e OPENAI_API_KEY=sk-test-key-for-testing \
  -e DATABASE_URL=sqlite:///./test_chatbot.db \
  flywheel pytest -q

# Interactive testing session
docker run -it --rm flywheel bash
# Inside container: pytest -v --tb=long
```

### Using Helper Scripts
```bash
# Linux/Mac
./scripts/test_docker.sh

# Windows PowerShell
.\scripts\test_docker.ps1
```

## Environment Configuration

### Required Environment Variables
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Optional Environment Variables
```bash
DATABASE_URL=sqlite:///./chatbot.db
DEFAULT_MODEL=gpt-4o
DEFAULT_TEMPERATURE=0.7
CORS_ORIGINS=["*"]
DEBUG=false
```

### Using .env File
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=sk-your-actual-api-key
DATABASE_URL=sqlite:///./chatbot.db
DEFAULT_MODEL=gpt-4o
DEFAULT_TEMPERATURE=0.7
CORS_ORIGINS=["*"]
DEBUG=false
```

Docker Compose will automatically load this file.

## Production Deployment

### Docker Compose Production Setup
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEBUG=false
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Scaling the Application
```bash
# Run multiple instances
docker compose up --scale app=3

# With load balancer (nginx example)
docker compose -f docker-compose.yml -f docker-compose.nginx.yml up
```

### Health Monitoring
```bash
# Check container health
docker ps

# View health check logs
docker inspect flywheel-app | grep -A 10 Health

# Manual health check
curl http://localhost:8000/health
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Error: bind: address already in use
# Solution: Stop existing services or use different port
docker compose down
# or
docker run -p 8001:8000 flywheel
```

#### 2. Environment Variables Not Loading
```bash
# Check if .env file exists and has correct format
cat .env

# Verify variables in container
docker compose run --rm app env | grep OPENAI
```

#### 3. Tests Failing in Container
```bash
# Check test environment
docker compose run --rm test env

# Run tests with debug output
docker compose run --rm test pytest -v --tb=long

# Interactive debugging
docker compose run --rm test bash
```

#### 4. Container Won't Start
```bash
# Check container logs
docker compose logs app

# Check if image built correctly
docker images | grep flywheel

# Rebuild image
docker compose build --no-cache
```

### Platform-Specific Issues

#### Windows Issues
- **Docker Desktop:** Ensure Docker Desktop is running
- **WSL2:** Use WSL2 backend for better performance
- **File Paths:** Use forward slashes in volume mounts
- **PowerShell:** Set execution policy for scripts

#### macOS Issues
- **M1/M2 Macs:** Image builds for ARM64 automatically
- **Docker Desktop:** Allocate sufficient memory (4GB+)
- **File Permissions:** Ensure scripts are executable

#### Linux Issues
- **Docker Permissions:** Add user to docker group
- **SELinux:** May need to configure container contexts
- **Firewall:** Ensure port 8000 is accessible

### Performance Optimization

#### Image Size Optimization
```dockerfile
# Multi-stage build example (if needed)
FROM python:3.11-slim as builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
# ... rest of Dockerfile
```

#### Runtime Optimization
```bash
# Limit container resources
docker run --memory=512m --cpus=1.0 flywheel

# Use production WSGI server (already using uvicorn)
# Configure uvicorn workers for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## Development Workflow

### Development with Live Reload
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app/backend
      - ./frontend:/app/frontend
    environment:
      - DEBUG=true
```

### Testing Workflow
```bash
# 1. Build image
docker build -t flywheel .

# 2. Run tests
./scripts/test_docker.sh

# 3. Start application
./scripts/run_docker.sh

# 4. Manual testing
open http://localhost:8000
```

## Security Considerations

### Container Security
- Base image regularly updated (python:3.11-slim)
- No unnecessary packages installed
- Environment variables for secrets (not hardcoded)
- Health checks for monitoring
- Non-privileged container execution

### Network Security
- Only necessary port (8000) exposed
- CORS properly configured
- No sensitive data in logs
- Environment variable injection for API keys

### Production Recommendations
```bash
# Use specific image tags (not latest)
docker build -t flywheel:v1.0.0 .

# Scan for vulnerabilities
docker scout cves flywheel:v1.0.0

# Use secrets management
docker swarm init
echo "sk-your-api-key" | docker secret create openai_key -
```

## Monitoring and Logging

### Container Logs
```bash
# View application logs
docker compose logs -f app

# View specific service logs
docker compose logs test

# Export logs
docker compose logs app > app.log
```

### Health Monitoring
```bash
# Continuous health check
watch -n 5 'curl -s http://localhost:8000/health'

# Health check in monitoring systems
# Endpoint: GET http://localhost:8000/health
# Expected: {"status":"healthy","version":"1.0.0"}
```

### Performance Monitoring
```bash
# Container resource usage
docker stats flywheel-app

# Detailed container info
docker inspect flywheel-app
```

## Backup and Recovery

### Database Backup
```bash
# Backup SQLite database
docker compose exec app cp /app/backend/chatbot.db /tmp/backup.db
docker cp $(docker compose ps -q app):/tmp/backup.db ./backup.db
```

### Configuration Backup
```bash
# Backup environment configuration
cp .env .env.backup
cp docker-compose.yml docker-compose.yml.backup
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
# .github/workflows/docker.yml
name: Docker Build and Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t flywheel .
      - name: Run tests
        run: docker run --rm flywheel pytest -q
```

### Deployment Pipeline
```bash
# 1. Build and test
docker build -t flywheel:$VERSION .
docker run --rm flywheel:$VERSION pytest -q

# 2. Push to registry
docker tag flywheel:$VERSION registry.example.com/flywheel:$VERSION
docker push registry.example.com/flywheel:$VERSION

# 3. Deploy to production
docker service update --image registry.example.com/flywheel:$VERSION production_app
```

This Docker setup provides a robust, scalable, and maintainable deployment solution for the Data Flywheel Chatbot while maintaining all existing functionality and test coverage.
