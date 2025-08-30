#!/bin/bash
# Data Flywheel Chatbot - Docker Run Script (Linux/Mac)

set -e

echo "🐳 Data Flywheel Chatbot - Docker Setup"
echo "======================================"

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t flywheel .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Docker build failed"
    exit 1
fi

# Stop any existing container
echo "🛑 Stopping any existing containers..."
docker stop flywheel-app 2>/dev/null || true
docker rm flywheel-app 2>/dev/null || true

# Run the container
echo "🚀 Starting container..."
docker run -d \
    --name flywheel-app \
    -p 8000:8000 \
    --env-file .env 2>/dev/null || docker run -d \
    --name flywheel-app \
    -p 8000:8000 \
    -e OPENAI_API_KEY=sk-test-key-for-testing \
    flywheel

# Wait for container to be ready
echo "⏳ Waiting for container to be ready..."
sleep 5

# Check if container is running
if docker ps | grep -q flywheel-app; then
    echo "✅ Container is running!"
    echo ""
    echo "🌐 Application URLs:"
    echo "   Frontend: http://localhost:8000/"
    echo "   Health:   http://localhost:8000/health"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs:    docker logs flywheel-app"
    echo "   Stop app:     docker stop flywheel-app"
    echo "   Remove app:   docker rm flywheel-app"
    echo "   Run tests:    ./scripts/test_docker.sh"
else
    echo "❌ Container failed to start"
    echo "📋 Check logs with: docker logs flywheel-app"
    exit 1
fi
