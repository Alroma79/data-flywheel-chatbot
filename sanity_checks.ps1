# Sanity Checks - Interview Warmup (PowerShell-safe version)
# Run after launch_backend.ps1 is already running.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File .\sanity_checks.ps1

$BASE  = "http://127.0.0.1:8000"
$TOKEN = "local-dev-token"

function Step($name, [ScriptBlock]$action) {
  Write-Host ">>> $name"
  try {
    & $action
  } catch {
    Write-Host "ERROR: $($_.Exception.Message)"
  }
  Write-Host ""
}

# 1) API up
Step "Docs (/docs)"           { (Invoke-WebRequest -UseBasicParsing "$BASE/docs").StatusCode }
Step "OpenAPI (/openapi.json)"{ (Invoke-RestMethod "$BASE/openapi.json") | Select-Object -First 1 | Out-String }

# 2) Chat
$chatBody = @{
  message    = "Final pre-interview sanity check"
  session_id = "demo-live"
} | ConvertTo-Json
Step "Chat (POST /api/v1/chat)" {
  Invoke-RestMethod -Method POST "$BASE/api/v1/chat" -ContentType "application/json" -Body $chatBody | ConvertTo-Json -Depth 6
}

# 3) History (Bearer)
$headers = @{ Authorization = "Bearer $TOKEN" }
Step "History (GET /api/v1/chat-history)" {
  Invoke-RestMethod "$BASE/api/v1/chat-history?session_id=demo-live" -Headers $headers | Select-Object -First 3 | ConvertTo-Json -Depth 6
}

# 4) Feedback (POST /api/v1/feedback)
$hist = Invoke-RestMethod "$BASE/api/v1/chat-history?session_id=demo-live" -Headers $headers
$lastAssistant = ($hist | Where-Object { $_.role -eq "assistant" } | Select-Object -Last 1).content
$fbBody = @{
  message       = $lastAssistant
  user_feedback = "thumbs_up"
  comment       = "Looks good."
} | ConvertTo-Json
Step "Feedback (POST /api/v1/feedback)" {
  Invoke-RestMethod -Method POST "$BASE/api/v1/feedback" -ContentType "application/json" -Body $fbBody | ConvertTo-Json -Depth 6
}

# 5) Active Config
Step "Active Config (GET /api/v1/config)" {
  Invoke-RestMethod "$BASE/api/v1/config" -Headers $headers | ConvertTo-Json -Depth 6
}

# 6) (Optional) Configs List
Step "Configs List (GET /api/v1/configs)" {
  Invoke-RestMethod "$BASE/api/v1/configs" -Headers $headers | ConvertTo-Json -Depth 6
}

Write-Host ">>> Sanity checks complete."
