#!/usr/bin/env powershell

# Data Flywheel Chatbot Setup Script
# Runs migrations/init, seeds active config, and runs tests

param(
    [switch]$SkipTests,
    [switch]$Help
)

if ($Help) {
    Write-Host "Data Flywheel Chatbot Setup Script" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\setup.ps1 [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -SkipTests    Skip running tests after setup"
    Write-Host "  -Help         Show this help message"
    Write-Host ""
    Write-Host "This script will:" -ForegroundColor Cyan
    Write-Host "  1. Initialize/migrate database"
    Write-Host "  2. Seed active configuration"
    Write-Host "  3. Run tests (unless -SkipTests is specified)"
    exit 0
}

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

function Write-Success {
    param([string]$Message)
    Write-Host "SUCCESS: $Message" -ForegroundColor Green
}

# Change to script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "Data Flywheel Chatbot Setup" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Database Migration
Write-Step "Initializing database and applying migrations"
try {
    Set-Location backend
    python -c "from app.init_db import init_database; init_database()" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Database initialized successfully"
    } else {
        throw "Database initialization failed"
    }
} catch {
    Write-Error "Failed to initialize database: $_"
    exit 1
}

Write-Step "Applying database migration"
try {
    python -c "from app.migrations.add_session_columns import run_migration; run_migration('chatbot.db')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Database migration completed"
    } else {
        throw "Migration failed"
    }
} catch {
    Write-Error "Failed to apply migration: $_"
    exit 1
}

# Step 2: Seed Configuration
Write-Step "Seeding active configuration"
try {
    $seedScript = @"
import sys
sys.path.append('.')
from app.db import SessionLocal
from app.models import ChatbotConfig
import json

session = SessionLocal()
try:
    # Check for existing active config
    config = session.query(ChatbotConfig).filter(ChatbotConfig.is_active == True).first()
    if not config:
        default_config = ChatbotConfig(
            name='dev-default',
            config_json={
                'model': 'gpt-4o-mini',
                'temperature': 0.3,
                'system_prompt': 'You are a helpful assistant.',
                'max_tokens': None
            },
            is_active=True
        )
        session.add(default_config)
        session.commit()
        print('Created default active configuration')
    else:
        print(f'Active configuration already exists: {config.name}')
finally:
    session.close()
"@

    $seedScript | python
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Configuration seeded successfully"
    } else {
        throw "Configuration seeding failed"
    }
} catch {
    Write-Error "Failed to seed configuration: $_"
    exit 1
}

# Step 3: Verify Schema
Write-Step "Verifying database schema"
try {
    $schemaOutput = sqlite3 chatbot.db "PRAGMA table_info(chat_history);" 2>$null
    if ($schemaOutput -match "session_id" -and $schemaOutput -match "role" -and $schemaOutput -match "content") {
        Write-Success "Database schema verified - all required columns present"
    } else {
        throw "Schema verification failed"
    }
} catch {
    Write-Error "Failed to verify database schema: $_"
    exit 1
}

# Step 4: Run Tests (unless skipped)
if (-not $SkipTests) {
    Write-Step "Running tests"
    try {
        python -m pytest tests/test_chat_sessions.py -v --tb=short
        if ($LASTEXITCODE -eq 0) {
            Write-Success "All tests passed"
        } else {
            throw "Tests failed"
        }
    } catch {
        Write-Error "Test execution failed: $_"
        exit 1
    }
}

# Return to original directory
Set-Location $ScriptDir

Write-Host ""
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Start the server: cd backend && uvicorn app.main:app --reload"
Write-Host "2. Open browser: http://localhost:8000/"
Write-Host "3. Test API: http://localhost:8000/docs"
Write-Host ""
Write-Host "Database location: backend/chatbot.db" -ForegroundColor Yellow
Write-Host "To view chat history: sqlite3 backend/chatbot.db 'SELECT * FROM chat_history;'" -ForegroundColor Yellow