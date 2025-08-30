#!/bin/bash
# Data Flywheel Chatbot - Docker Test Script (Linux/Mac)

set -e

echo "🧪 Data Flywheel Chatbot - Docker Test Suite"
echo "============================================"

# Build the image if it doesn't exist
if ! docker images | grep -q flywheel; then
    echo "📦 Building Docker image first..."
    docker build -t flywheel .
fi

echo "🚀 Running tests in Docker container..."
echo ""

# Run tests using docker compose
if [ -f "docker-compose.yml" ]; then
    echo "Using Docker Compose..."
    docker compose run --rm test
    test_exit_code=$?
else
    echo "Using direct Docker run..."
    docker run --rm \
        -e OPENAI_API_KEY=sk-test-key-for-testing \
        -e DATABASE_URL=sqlite:///./test_chatbot.db \
        -e DEBUG=true \
        flywheel pytest -q --tb=short
    test_exit_code=$?
fi

echo ""
if [ $test_exit_code -eq 0 ]; then
    echo "✅ All tests passed in Docker container!"
    echo ""
    echo "🎉 Docker containerization is working correctly"
    echo "📋 Next steps:"
    echo "   - Deploy with: docker compose up -d"
    echo "   - Scale with: docker compose up --scale app=3"
    echo "   - Monitor with: docker compose logs -f"
else
    echo "❌ Tests failed in Docker container"
    echo "📋 Troubleshooting:"
    echo "   - Check logs: docker compose logs test"
    echo "   - Debug interactively: docker compose run --rm test bash"
    echo "   - Verify environment variables are set correctly"
    exit 1
fi
