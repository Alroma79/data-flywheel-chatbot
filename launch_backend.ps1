# Launch Backend - Interview Warmup
# Usage: Right-click > Run with PowerShell OR run: powershell -ExecutionPolicy Bypass -File .\launch_backend.ps1

# --- Edit these if needed ---
$ProjectRoot = "C:\Users\ALROMA\Documents\Masters Project\data-flywheel-chatbot"
$VenvActivate = "$ProjectRoot\venv\Scripts\Activate.ps1"
$Token       = "local-dev-token"
$DbUrl       = "sqlite:///C:/Users/ALROMA/Documents/Masters Project/data-flywheel-chatbot/backend/chatbot.db"
$BindAddr    = "127.0.0.1"   # <-- renamed from $Host to avoid PS built-in
$Port        = 8000

# --- Prep environment ---
Write-Host ">>> Switching to project root: $ProjectRoot"
Set-Location $ProjectRoot

Write-Host ">>> Activating virtual environment"
& $VenvActivate

Write-Host ">>> Setting environment variables"
$env:DATABASE_URL = $DbUrl
$env:APP_TOKEN    = $Token   # adjust name if your code uses API_KEY/APP_TOKEN
$env:DEMO_MODE    = "true"   # optional

Write-Host ">>> Starting backend with Uvicorn (access logs ON)"
uvicorn backend.app.main:app --reload --host $BindAddr --port $Port --access-log --log-level info

