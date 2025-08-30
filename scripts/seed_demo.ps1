# Demo seed script for Data Flywheel Chatbot (Windows PowerShell)

Write-Host "🌱 Seeding Demo Data for Data Flywheel Chatbot" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Check if server is running
try {
    $healthCheck = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5
    Write-Host "✅ Server is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Server is not running!" -ForegroundColor Red
    Write-Host "Please start the server first:" -ForegroundColor Yellow
    Write-Host "   docker compose up -d" -ForegroundColor White
    Write-Host "   or" -ForegroundColor White
    Write-Host "   cd backend && uvicorn app.main:app --reload" -ForegroundColor White
    exit 1
}

# Upload sample knowledge file
Write-Host "📁 Uploading sample knowledge file..." -ForegroundColor Yellow

if (Test-Path "docs/sample_knowledge.txt") {
    try {
        $form = @{
            file = Get-Item -Path "docs/sample_knowledge.txt"
        }
        $uploadResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/knowledge/files" -Method Post -Form $form
        Write-Host "✅ Sample knowledge file uploaded successfully" -ForegroundColor Green
        Write-Host "   File ID: $($uploadResponse.id)" -ForegroundColor White
    } catch {
        Write-Host "❌ Failed to upload knowledge file: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ Sample knowledge file not found at docs/sample_knowledge.txt" -ForegroundColor Red
    exit 1
}

# Create a sample chatbot configuration
Write-Host "⚙️  Creating sample chatbot configuration..." -ForegroundColor Yellow

$configData = @{
    name = "demo_config"
    config_json = @{
        system_prompt = "You are a helpful AI assistant specializing in data flywheels and business intelligence. Use the provided knowledge base to give accurate, well-sourced answers."
        model = "gpt-4o"
        temperature = 0.7
        max_tokens = 1000
    }
    is_active = $true
    tags = @("demo", "data-flywheel")
} | ConvertTo-Json -Depth 3

try {
    $configResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/config" -Method Post -Body $configData -ContentType "application/json"
    Write-Host "✅ Sample configuration created successfully" -ForegroundColor Green
    Write-Host "   Config ID: $($configResponse.id)" -ForegroundColor White
} catch {
    Write-Host "❌ Failed to create sample configuration: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Send a sample chat message to create history
Write-Host "💬 Creating sample chat history..." -ForegroundColor Yellow

$chatData = @{
    message = "What is a data flywheel?"
} | ConvertTo-Json

try {
    $chatResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" -Method Post -Body $chatData -ContentType "application/json"
    Write-Host "✅ Sample chat history created" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create sample chat: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 Demo seeding completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Open http://localhost:8000/ in your browser" -ForegroundColor White
Write-Host "   2. Try asking: 'What are the benefits of data flywheels?'" -ForegroundColor White
Write-Host "   3. Notice the knowledge sources in the response" -ForegroundColor White
Write-Host "   4. Click 👍 to provide feedback" -ForegroundColor White
Write-Host "   5. Click 'Load Recent' to see conversation history" -ForegroundColor White
Write-Host ""
Write-Host "🔗 You can also test the API with the Postman collection:" -ForegroundColor Cyan
Write-Host "   Import docs/Flywheel.postman_collection.json" -ForegroundColor White
