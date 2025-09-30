# demo_flow.ps1
# Demo script for Noxus interview – shows full flywheel: config → chat → feedback → history

# --- Settings ---
$BASE = "http://127.0.0.1:8000"
$TOKEN = "local-dev-token"   # only needed for /chat-history if auth enforced
$SESSION = "demo-session"

Write-Host ">>> Health & Version"
curl.exe "$BASE/health"
curl.exe "$BASE/version"
Pause

Write-Host "`n>>> Get Current Config"
curl.exe -s "$BASE/api/v1/config"
Pause

Write-Host "`n>>> Update Config (temperature=0.2)"
$body = @{
  name = "default"
  config_json = @{
    model = "gpt-4o"
    system_prompt = "You are a helpful chatbot for the Data Flywheel."
    temperature = 0.2
  }
} | ConvertTo-Json
curl.exe -s -X POST "$BASE/api/v1/config" -H "Content-Type: application/json" -d $body
Pause

Write-Host "`n>>> Send Chat"
$chat = @{
  message = "Give me a one-line summary of the flywheel idea."
  session_id = $SESSION
} | ConvertTo-Json
curl.exe -s -X POST "$BASE/api/v1/chat" -H "Content-Type: application/json" -d $chat
Pause

Write-Host "`n>>> Submit Feedback"
$fb = @{
  message = "Great explanation!"
  user_feedback = "thumbs_up"
  comment = "Very clear"
} | ConvertTo-Json
curl.exe -s -X POST "$BASE/api/v1/feedback" -H "Content-Type: application/json" -d $fb
Pause

Write-Host "`n>>> Get Chat History"
curl.exe -s "$BASE/api/v1/chat-history?session_id=$SESSION" -H "Authorization: Bearer $TOKEN"
Pause

Write-Host "`n>>> Demo flow complete!"
