# Use official Python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install backend dependencies
COPY ../backend/app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY ../backend/app .

# Start FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
