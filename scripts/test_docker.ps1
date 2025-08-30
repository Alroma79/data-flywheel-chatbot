# Data Flywheel Chatbot - Docker Test Script (Windows PowerShell)

Write-Host "🧪 Data Flywheel Chatbot - Docker Test Suite" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Build the image if it doesn't exist
$imageExists = docker images --format "table {{.Repository}}" | Select-String "flywheel"
if (-not $imageExists) {
    Write-Host "📦 Building Docker image first..." -ForegroundColor Yellow
    docker build -t flywheel .
}

Write-Host "🚀 Running tests in Docker container..." -ForegroundColor Yellow
Write-Host ""

# Run tests using docker compose
if (Test-Path "docker-compose.yml") {
    Write-Host "Using Docker Compose..." -ForegroundColor Green
    docker compose run --rm test
    $testExitCode = $LASTEXITCODE
} else {
    Write-Host "Using direct Docker run..." -ForegroundColor Green
    docker run --rm `
        -e OPENAI_API_KEY=sk-test-key-for-testing `
        -e DATABASE_URL=sqlite:///./test_chatbot.db `
        -e DEBUG=true `
        flywheel pytest -q --tb=short
    $testExitCode = $LASTEXITCODE
}

Write-Host ""
if ($testExitCode -eq 0) {
    Write-Host "✅ All tests passed in Docker container!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎉 Docker containerization is working correctly" -ForegroundColor Cyan
    Write-Host "📋 Next steps:" -ForegroundColor Cyan
    Write-Host "   - Deploy with: docker compose up -d" -ForegroundColor White
    Write-Host "   - Scale with: docker compose up --scale app=3" -ForegroundColor White
    Write-Host "   - Monitor with: docker compose logs -f" -ForegroundColor White
} else {
    Write-Host "❌ Tests failed in Docker container" -ForegroundColor Red
    Write-Host "📋 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   - Check logs: docker compose logs test" -ForegroundColor White
    Write-Host "   - Debug interactively: docker compose run --rm test bash" -ForegroundColor White
    Write-Host "   - Verify environment variables are set correctly" -ForegroundColor White
    exit 1
}
