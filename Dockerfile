# Data Flywheel Chatbot - Production Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for potential PDF processing
# Keep minimal to maintain lean image
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY backend/app/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY tests/ /app/tests/
COPY pytest.ini /app/pytest.ini

# Copy test files and validation scripts
COPY test_knowledge.txt /app/test_knowledge.txt
COPY run_validation.py /app/run_validation.py

# Create uploads directory
RUN mkdir -p /app/backend/uploads

# Set Python path to include backend/app
ENV PYTHONPATH=/app/backend

# Expose port
EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command to run the application
# Support Railway's dynamic PORT environment variable
WORKDIR /app/backend
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
