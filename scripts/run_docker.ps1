# Data Flywheel Chatbot - Docker Run Script (Windows PowerShell)

Write-Host "🐳 Data Flywheel Chatbot - Docker Setup" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Build the Docker image
Write-Host "📦 Building Docker image..." -ForegroundColor Yellow
docker build -t flywheel .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Docker image built successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    exit 1
}

# Stop any existing container
Write-Host "🛑 Stopping any existing containers..." -ForegroundColor Yellow
docker stop flywheel-app 2>$null
docker rm flywheel-app 2>$null

# Run the container
Write-Host "🚀 Starting container..." -ForegroundColor Yellow

# Try to use .env file, fallback to default env vars
$envFileExists = Test-Path ".env"
if ($envFileExists) {
    docker run -d --name flywheel-app -p 8000:8000 --env-file .env flywheel
} else {
    docker run -d --name flywheel-app -p 8000:8000 -e OPENAI_API_KEY=sk-test-key-for-testing flywheel
}

# Wait for container to be ready
Write-Host "⏳ Waiting for container to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if container is running
$containerRunning = docker ps --filter "name=flywheel-app" --format "table {{.Names}}" | Select-String "flywheel-app"

if ($containerRunning) {
    Write-Host "✅ Container is running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Application URLs:" -ForegroundColor Cyan
    Write-Host "   Frontend: http://localhost:8000/" -ForegroundColor White
    Write-Host "   Health:   http://localhost:8000/health" -ForegroundColor White
    Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "📋 Useful commands:" -ForegroundColor Cyan
    Write-Host "   View logs:    docker logs flywheel-app" -ForegroundColor White
    Write-Host "   Stop app:     docker stop flywheel-app" -ForegroundColor White
    Write-Host "   Remove app:   docker rm flywheel-app" -ForegroundColor White
    Write-Host "   Run tests:    .\scripts\test_docker.ps1" -ForegroundColor White
} else {
    Write-Host "❌ Container failed to start" -ForegroundColor Red
    Write-Host "📋 Check logs with: docker logs flywheel-app" -ForegroundColor Yellow
    exit 1
}
