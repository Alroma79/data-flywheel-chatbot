"""
Comprehensive tests for frontend integration and static file serving.
Tests both automated API integration and frontend file serving.
"""

import pytest
import requests
import json
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:8000"
API_BASE_URL = f"{BASE_URL}/api/v1"

class TestFrontendIntegration:
    """Test suite for frontend integration and static file serving."""
    
    @pytest.fixture(scope="class")
    def server_health_check(self):
        """Ensure server is running before tests."""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            assert response.status_code == 200, "Server is not running"
        except requests.exceptions.RequestException:
            pytest.skip("Server is not running. Start with: cd backend && uvicorn app.main:app --reload")

    # Static File Serving Tests
    
    def test_frontend_html_serving(self, server_health_check):
        """Test that index.html is served at root path."""
        response = requests.get(BASE_URL)
        
        assert response.status_code == 200
        assert response.headers.get('content-type', '').startswith('text/html')
        
        content = response.text
        assert "Data Flywheel Chatbot" in content
        assert "app.js" in content
        assert '<div class="container">' in content
        assert 'id="messages"' in content
    
    def test_javascript_file_serving(self, server_health_check):
        """Test that app.js is served correctly."""
        response = requests.get(f"{BASE_URL}/app.js")
        
        assert response.status_code == 200
        assert response.headers.get('content-type', '').startswith('application/javascript') or \
               response.headers.get('content-type', '').startswith('text/javascript')
        
        content = response.text
        assert "api.post" in content
        assert "sendMessage" in content
        assert "uploadFile" in content
        assert "loadChatHistory" in content
    
    def test_static_file_404_handling(self, server_health_check):
        """Test that non-existent static files return 404."""
        response = requests.get(f"{BASE_URL}/nonexistent.js")
        assert response.status_code == 404

    # API Accessibility Tests
    
    def test_api_endpoints_accessible_with_frontend(self, server_health_check):
        """Test that API endpoints remain accessible when frontend is mounted."""
        endpoints = [
            ("/health", 200),
            ("/api/v1/chat-history", 200),  # Should work even without params due to defaults
        ]
        
        for endpoint, expected_status in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == expected_status, f"Endpoint {endpoint} failed"
    
    def test_cors_headers_present(self, server_health_check):
        """Test that CORS headers are properly configured for frontend requests."""
        response = requests.options(
            f"{API_BASE_URL}/chat",
            headers={
                "Origin": BASE_URL,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        # Should have CORS headers
        assert "Access-Control-Allow-Origin" in response.headers or \
               "access-control-allow-origin" in response.headers

    # Frontend-Backend Integration Tests
    
    def test_frontend_chat_api_integration(self, server_health_check):
        """Test that frontend can successfully communicate with chat API."""
        # Simulate a frontend chat request
        headers = {
            "Content-Type": "application/json",
            "Origin": BASE_URL,
            "Referer": BASE_URL
        }
        
        payload = {"message": "Hello from frontend test"}
        response = requests.post(f"{API_BASE_URL}/chat", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert len(data["reply"]) > 0
    
    def test_frontend_file_upload_simulation(self, server_health_check):
        """Test file upload as it would be done from frontend."""
        # Create a simple test file
        test_content = "Frontend integration test file content"
        
        files = {'file': ('frontend_test.txt', test_content, 'text/plain')}
        headers = {
            "Origin": BASE_URL,
            "Referer": BASE_URL
        }
        
        response = requests.post(f"{API_BASE_URL}/knowledge/files", files=files, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "frontend_test.txt"
        assert "id" in data
    
    def test_frontend_feedback_submission(self, server_health_check):
        """Test feedback submission as it would be done from frontend."""
        headers = {
            "Content-Type": "application/json",
            "Origin": BASE_URL,
            "Referer": BASE_URL
        }
        
        payload = {
            "message": "Test message for frontend feedback",
            "user_feedback": "thumbs_up",
            "comment": "Frontend integration test"
        }
        
        response = requests.post(f"{API_BASE_URL}/feedback", json=payload, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert "message" in data
    
    def test_frontend_history_loading(self, server_health_check):
        """Test chat history loading as it would be done from frontend."""
        headers = {
            "Origin": BASE_URL,
            "Referer": BASE_URL
        }
        
        response = requests.get(f"{API_BASE_URL}/chat-history?limit=10", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    # Error Handling Tests
    
    def test_frontend_error_handling(self, server_health_check):
        """Test that API errors are properly formatted for frontend consumption."""
        # Test invalid chat request
        headers = {
            "Content-Type": "application/json",
            "Origin": BASE_URL
        }
        
        payload = {"message": ""}  # Empty message should cause error
        response = requests.post(f"{API_BASE_URL}/chat", json=payload, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data or "message" in data
    
    def test_frontend_validation_error_format(self, server_health_check):
        """Test that validation errors are properly formatted."""
        headers = {
            "Content-Type": "application/json",
            "Origin": BASE_URL
        }
        
        # Send invalid JSON structure
        payload = {"invalid_field": "test"}
        response = requests.post(f"{API_BASE_URL}/chat", json=payload, headers=headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data or "message" in data

    # Performance and Load Tests
    
    def test_concurrent_frontend_requests(self, server_health_check):
        """Test that frontend can handle multiple concurrent requests."""
        import concurrent.futures
        import threading
        
        def make_request():
            headers = {"Content-Type": "application/json", "Origin": BASE_URL}
            payload = {"message": f"Concurrent test {threading.current_thread().ident}"}
            response = requests.post(f"{API_BASE_URL}/chat", json=payload, headers=headers)
            return response.status_code == 200
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # At least 80% should succeed (allowing for some rate limiting)
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8, f"Success rate too low: {success_rate}"

    # Content Security Tests
    
    def test_frontend_content_security(self, server_health_check):
        """Test that frontend serves secure content."""
        response = requests.get(BASE_URL)
        
        # Check that no obvious security issues in HTML
        content = response.text.lower()
        assert "eval(" not in content
        assert "innerhtml" not in content  # Should use textContent/createElement
        assert "document.write" not in content
    
    def test_api_response_headers(self, server_health_check):
        """Test that API responses have appropriate security headers."""
        response = requests.get(f"{API_BASE_URL}/chat-history")
        
        # Should have JSON content type
        assert "application/json" in response.headers.get("content-type", "")
        
        # Should not expose server details
        server_header = response.headers.get("server", "").lower()
        assert "uvicorn" not in server_header or "fastapi" not in server_header

    # Integration Smoke Test
    
    def test_full_workflow_simulation(self, server_health_check):
        """Test complete workflow as frontend would execute it."""
        headers = {
            "Content-Type": "application/json",
            "Origin": BASE_URL,
            "Referer": BASE_URL
        }
        
        # Step 1: Upload a file
        test_content = "Integration test: Machine learning is a powerful technology."
        files = {'file': ('workflow_test.txt', test_content, 'text/plain')}
        upload_response = requests.post(f"{API_BASE_URL}/knowledge/files", files=files)
        assert upload_response.status_code == 201
        
        # Step 2: Ask a related question
        chat_payload = {"message": "What is machine learning?"}
        chat_response = requests.post(f"{API_BASE_URL}/chat", json=chat_payload, headers=headers)
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        
        # Step 3: Submit feedback
        feedback_payload = {
            "message": chat_payload["message"],
            "user_feedback": "thumbs_up",
            "comment": "Integration test feedback"
        }
        feedback_response = requests.post(f"{API_BASE_URL}/feedback", json=feedback_payload, headers=headers)
        assert feedback_response.status_code == 201
        
        # Step 4: Load history
        history_response = requests.get(f"{API_BASE_URL}/chat-history?limit=5", headers=headers)
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert len(history_data) > 0
        
        # Verify the workflow created the expected data
        assert "reply" in chat_data
        recent_message = next((msg for msg in history_data if msg["user_message"] == chat_payload["message"]), None)
        assert recent_message is not None
