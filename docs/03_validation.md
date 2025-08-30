# Task 1 & Task 2 Validation Guide

## Overview

This document provides comprehensive validation procedures for both **Task 1 (Knowledge Integration)** and **Task 2 (Minimal Frontend)** of the Data Flywheel Chatbot project.

## Prerequisites

### System Requirements
- Python 3.8+ with pip
- Modern web browser (Chrome 80+, Firefox 75+, Safari 13+, Edge 80+)
- Terminal/command prompt access

### Setup Instructions

#### Option 1: Docker (Recommended)
```bash
# Build and start
docker compose up --build -d

# Seed demo data
./scripts/seed_demo.sh  # Linux/Mac
# or
.\scripts\seed_demo.ps1  # Windows
```

#### Option 2: Local Development
```bash
# Install dependencies
cd backend
pip install -r app/requirements.txt

# Start the server
uvicorn app.main:app --reload

# Seed demo data (in another terminal)
./scripts/seed_demo.sh
```

3. **Verify server is running:**
   ```bash
   curl http://localhost:8000/health
   # Expected: {"status":"healthy","version":"1.0.0"}
   ```

## Automated Testing

### Running All Tests
```bash
# From project root directory
pytest -q
```

**Expected Output:**
```
tests/test_frontend_integration.py ................    [100%]
tests/test_knowledge_integration.py ................   [100%]
======================== XX passed in X.XXs ========================
```

### Running Specific Test Suites
```bash
# Knowledge integration tests only
pytest tests/test_knowledge_integration.py -v

# Frontend integration tests only  
pytest tests/test_frontend_integration.py -v

# Run with detailed output
pytest -v --tb=long
```

### Test Coverage Summary

**Knowledge Integration Tests (18 tests):**
- ✅ File upload (TXT, PDF) - happy path
- ✅ Knowledge-enhanced chat responses
- ✅ Chat without knowledge fallback
- ✅ Feedback submission and storage
- ✅ Chat history retrieval
- ✅ Edge cases: empty files, oversized files, invalid types
- ✅ Error handling: invalid payloads, limits

**Frontend Integration Tests (15 tests):**
- ✅ Static file serving (HTML, JS)
- ✅ API accessibility with frontend mounted
- ✅ CORS configuration
- ✅ Frontend-backend communication simulation
- ✅ Error handling and validation
- ✅ Security headers and content
- ✅ Full workflow simulation

## Manual Validation Checklist

### Phase 1: Backend API Validation (5 minutes)

#### 1.1 Knowledge File Upload
```bash
# Test TXT file upload
curl -X POST "http://localhost:8000/api/v1/knowledge/files" \
  -F "file=@test_knowledge.txt"
```

**✅ Expected Result:**
```json
{
  "id": 1,
  "filename": "test_knowledge.txt",
  "size": 1234,
  "message": "File uploaded successfully"
}
```

#### 1.2 Knowledge-Enhanced Chat
```bash
# Ask question related to uploaded file
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is machine learning?"}'
```

**✅ Expected Result:**
```json
{
  "reply": "Based on the information from test_knowledge.txt, machine learning is...",
  "knowledge_sources": [
    {
      "filename": "test_knowledge.txt",
      "file_id": 1,
      "relevance_score": 0.85
    }
  ]
}
```

#### 1.3 Non-Knowledge Chat
```bash
# Ask unrelated question
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather today?"}'
```

**✅ Expected Result:**
```json
{
  "reply": "I don't have access to current weather information..."
}
```
*Note: No `knowledge_sources` field should be present*

#### 1.4 Feedback Submission
```bash
# Submit positive feedback
curl -X POST "http://localhost:8000/api/v1/feedback" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is machine learning?", "user_feedback": "thumbs_up", "comment": "Great answer!"}'
```

**✅ Expected Result:**
```json
{
  "message": "Feedback recorded successfully"
}
```

#### 1.5 Chat History Retrieval
```bash
# Get recent chat history
curl -X GET "http://localhost:8000/api/v1/chat-history?limit=5"
```

**✅ Expected Result:**
```json
[
  {
    "id": 1,
    "user_message": "What is machine learning?",
    "bot_reply": "Based on the information from...",
    "timestamp": "2024-08-30T10:30:00.123456"
  }
]
```

### Phase 2: Frontend Web Interface Validation (5 minutes)

#### 2.1 Access Web Interface
1. **Open browser:** Navigate to `http://localhost:8000/`
2. **✅ Verify:** Page loads with "Data Flywheel Chatbot" title
3. **✅ Verify:** Chat interface is visible with message input and send button
4. **✅ Verify:** File upload section is present
5. **✅ Verify:** "Load Recent" button is visible

#### 2.2 File Upload via Web Interface
1. **Click "Choose File"** button
2. **Select** `test_knowledge.txt` file
3. **Click "Upload"** button
4. **✅ Expected:** Green success message appears: "File uploaded successfully: test_knowledge.txt"
5. **✅ Expected:** Message disappears after 5 seconds

#### 2.3 Knowledge-Enhanced Chat via Web Interface
1. **Type message:** "What is machine learning?" in the input field
2. **Click "Send"** or press Enter
3. **✅ Expected:** User message appears in blue bubble on the right
4. **✅ Expected:** AI response appears in gray bubble on the left
5. **✅ Expected:** Knowledge sources section appears below AI response
6. **✅ Expected:** Source shows "test_knowledge.txt" with relevance score
7. **✅ Expected:** 👍/👎 feedback buttons appear below AI response

#### 2.4 Feedback Submission via Web Interface
1. **Click 👍** button on the AI response
2. **✅ Expected:** Button becomes highlighted/active
3. **✅ Expected:** Comment input field appears
4. **Type comment:** "Very helpful response"
5. **Click outside** the comment field or press Enter
6. **✅ Expected:** Green success message: "Feedback submitted successfully"

#### 2.5 Chat History Loading via Web Interface
1. **Click "Load Recent"** button
2. **✅ Expected:** Previous conversations load into the chat window
3. **✅ Expected:** Messages appear with timestamps
4. **✅ Expected:** Both user and AI messages are displayed
5. **✅ Expected:** Green success message: "Loaded X recent conversations"

#### 2.6 Non-Knowledge Chat via Web Interface
1. **Type message:** "What's the weather like today?"
2. **Click "Send"**
3. **✅ Expected:** AI responds without knowledge sources
4. **✅ Expected:** No "Sources:" section appears below response
5. **✅ Expected:** Response is general/fallback answer

### Phase 3: Edge Case Validation (2 minutes)

#### 3.1 Invalid File Upload
1. **Create a large file:** `dd if=/dev/zero of=large.txt bs=1M count=15` (Linux/Mac) or create 15MB+ file
2. **Try to upload** via web interface
3. **✅ Expected:** Red error message: "File size exceeds maximum allowed size"

#### 3.2 Empty Message Handling
1. **Leave message input empty**
2. **Click "Send"**
3. **✅ Expected:** Red error message: "Please enter a message"

#### 3.3 Unsupported File Type
1. **Try to upload** a .jpg or .docx file
2. **✅ Expected:** Red error message: "Only TXT and PDF files are allowed"

## Validation Results Documentation

### Test Environment
- **Date:** [Fill in test date]
- **Server Version:** [Check /health endpoint]
- **Browser:** [Browser name and version]
- **Operating System:** [OS details]

### Automated Test Results
```bash
# Run this command and paste results:
pytest -v --tb=short
```

**Results:**
```
[Paste pytest output here]
```

### Manual Test Results

| Test Case | Status | Notes |
|-----------|--------|-------|
| **Backend API Tests** | | |
| File Upload (TXT) | ✅/❌ | |
| Knowledge-Enhanced Chat | ✅/❌ | |
| Non-Knowledge Chat | ✅/❌ | |
| Feedback Submission | ✅/❌ | |
| Chat History Retrieval | ✅/❌ | |
| **Frontend Web Interface** | | |
| Page Loading | ✅/❌ | |
| File Upload UI | ✅/❌ | |
| Chat Interface | ✅/❌ | |
| Knowledge Sources Display | ✅/❌ | |
| Feedback Buttons | ✅/❌ | |
| History Loading | ✅/❌ | |
| **Edge Cases** | | |
| Large File Rejection | ✅/❌ | |
| Empty Message Handling | ✅/❌ | |
| Invalid File Type | ✅/❌ | |

### Screenshots

**Recommended screenshots to capture:**
1. **Frontend Homepage:** `http://localhost:8000/`
2. **Successful File Upload:** Green success message
3. **Knowledge-Enhanced Response:** AI response with sources
4. **Feedback Interface:** 👍/👎 buttons and comment field
5. **Chat History:** Loaded conversation history
6. **Error Handling:** Red error message example

## Troubleshooting Common Issues

### Server Won't Start
```bash
# Check if port 8000 is in use
netstat -an | grep 8000

# Kill existing processes
pkill -f uvicorn

# Restart server
cd backend && uvicorn app.main:app --reload
```

### Tests Failing
```bash
# Install missing dependencies
pip install -r backend/app/requirements.txt

# Check server health
curl http://localhost:8000/health

# Run tests with verbose output
pytest -v --tb=long
```

### Frontend Not Loading
1. **Check server logs** for static file mounting messages
2. **Verify frontend directory** exists at project root
3. **Clear browser cache** and refresh
4. **Check browser console** for JavaScript errors

### Knowledge Integration Not Working
1. **Verify file upload** succeeded (check uploads/ directory)
2. **Check file content** is readable text
3. **Try simpler questions** that match file content exactly
4. **Check server logs** for knowledge processing errors

## Performance Benchmarks

### Expected Response Times
- **File Upload (1MB):** < 2 seconds
- **Chat Response (no knowledge):** < 3 seconds  
- **Chat Response (with knowledge):** < 5 seconds
- **History Loading (10 messages):** < 1 second
- **Frontend Page Load:** < 500ms

### Resource Usage
- **Memory:** < 200MB for basic operation
- **CPU:** < 10% during normal chat operations
- **Disk:** Uploaded files stored in `backend/uploads/`

## Validation Sign-off

**Validator Name:** ________________  
**Date:** ________________  
**Overall Status:** ✅ PASS / ❌ FAIL  

**Summary:**
- Automated tests: ___/33 passed
- Manual tests: ___/12 passed  
- Critical issues: ________________
- Recommendations: ________________

**Approval for Task 3 (Docker & Tests):** ✅ YES / ❌ NO

---

*This validation confirms that both Knowledge Integration (Task 1) and Minimal Frontend (Task 2) meet all specified requirements and are ready for production deployment.*
