"""
Comprehensive tests for knowledge integration functionality.
Tests both happy paths and edge cases for file upload and knowledge retrieval.
"""

import pytest
import requests
import tempfile
import os
from io import BytesIO

BASE_URL = "http://127.0.0.1:8000/api/v1"

class TestKnowledgeIntegration:
    """Test suite for knowledge integration features."""
    
    @pytest.fixture(scope="class")
    def server_health_check(self):
        """Ensure server is running before tests."""
        try:
            response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health", timeout=5)
            assert response.status_code == 200, "Server is not running"
        except requests.exceptions.RequestException:
            pytest.skip("Server is not running. Start with: cd backend && uvicorn app.main:app --reload")
    
    @pytest.fixture
    def sample_txt_file(self):
        """Create a sample TXT file for testing."""
        content = """Machine Learning Fundamentals
        
Machine learning is a subset of artificial intelligence that enables computers to learn from data.
Key concepts include supervised learning, unsupervised learning, and neural networks.
Popular libraries include scikit-learn, TensorFlow, and PyTorch.
Applications include image recognition, natural language processing, and recommendation systems."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def sample_pdf_file(self):
        """Create a minimal PDF file for testing."""
        # Simple PDF content (minimal valid PDF structure)
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(pdf_content)
            f.flush()
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def oversized_file(self):
        """Create an oversized file for testing size limits."""
        # Create a file larger than 10MB (current limit)
        content = "A" * (11 * 1024 * 1024)  # 11MB
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()
            yield f.name
        os.unlink(f.name)

    # Happy Path Tests
    
    def test_upload_txt_file_success(self, server_health_check, sample_txt_file):
        """Test successful TXT file upload."""
        with open(sample_txt_file, 'rb') as f:
            files = {'file': ('test.txt', f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/knowledge/files", files=files)
        
        assert response.status_code == 201
        data = response.json()
        assert 'id' in data
        assert data['filename'] == 'test.txt'
        assert 'message' in data
        assert data['size'] > 0
    
    def test_upload_pdf_file_success(self, server_health_check, sample_pdf_file):
        """Test successful PDF file upload."""
        with open(sample_pdf_file, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/knowledge/files", files=files)
        
        assert response.status_code == 201
        data = response.json()
        assert 'id' in data
        assert data['filename'] == 'test.pdf'
    
    def test_knowledge_enhanced_chat(self, server_health_check, sample_txt_file):
        """Test chat with knowledge integration."""
        # First upload a file
        with open(sample_txt_file, 'rb') as f:
            files = {'file': ('ml_guide.txt', f, 'text/plain')}
            upload_response = requests.post(f"{BASE_URL}/knowledge/files", files=files)
        assert upload_response.status_code == 201
        
        # Then ask a related question
        chat_payload = {"message": "What is machine learning?"}
        chat_response = requests.post(f"{BASE_URL}/chat", json=chat_payload)
        
        assert chat_response.status_code == 200
        data = chat_response.json()
        assert 'reply' in data
        assert len(data['reply']) > 0
        
        # Should include knowledge sources
        if 'knowledge_sources' in data:
            assert len(data['knowledge_sources']) > 0
            source = data['knowledge_sources'][0]
            assert 'filename' in source
            assert 'relevance_score' in source
            assert source['filename'] == 'ml_guide.txt'
    
    def test_chat_without_knowledge_match(self, server_health_check):
        """Test chat with question that doesn't match knowledge base."""
        chat_payload = {"message": "What's the weather like today?"}
        response = requests.post(f"{BASE_URL}/chat", json=chat_payload)
        
        assert response.status_code == 200
        data = response.json()
        assert 'reply' in data
        # Should not have knowledge sources or have empty sources
        assert 'knowledge_sources' not in data or len(data.get('knowledge_sources', [])) == 0
    
    def test_feedback_submission_success(self, server_health_check):
        """Test successful feedback submission."""
        feedback_payload = {
            "message": "Test message for feedback",
            "user_feedback": "thumbs_up",
            "comment": "Great response!"
        }
        response = requests.post(f"{BASE_URL}/feedback", json=feedback_payload)
        
        assert response.status_code == 201
        data = response.json()
        assert 'message' in data
    
    def test_chat_history_retrieval(self, server_health_check):
        """Test chat history retrieval."""
        # First send a message to create history
        chat_payload = {"message": "Hello, this is a test message"}
        requests.post(f"{BASE_URL}/chat", json=chat_payload)
        
        # Then retrieve history
        response = requests.get(f"{BASE_URL}/chat-history?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            entry = data[0]
            assert 'user_message' in entry
            assert 'bot_reply' in entry
            assert 'timestamp' in entry

    # Edge Case Tests
    
    def test_upload_empty_file(self, server_health_check):
        """Test upload of empty file."""
        empty_content = BytesIO(b"")
        files = {'file': ('empty.txt', empty_content, 'text/plain')}
        response = requests.post(f"{BASE_URL}/knowledge/files", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
        assert 'empty' in data['detail'].lower()
    
    def test_upload_unsupported_file_type(self, server_health_check):
        """Test upload of unsupported file type."""
        content = BytesIO(b"fake image content")
        files = {'file': ('test.jpg', content, 'image/jpeg')}
        response = requests.post(f"{BASE_URL}/knowledge/files", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
        assert 'not supported' in data['detail']
    
    def test_upload_oversized_file(self, server_health_check, oversized_file):
        """Test upload of file exceeding size limit."""
        with open(oversized_file, 'rb') as f:
            files = {'file': ('huge.txt', f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/knowledge/files", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
        assert 'exceeds maximum' in data['detail']
    
    def test_chat_empty_message(self, server_health_check):
        """Test chat with empty message."""
        chat_payload = {"message": ""}
        response = requests.post(f"{BASE_URL}/chat", json=chat_payload)
        
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
    
    def test_chat_oversized_message(self, server_health_check):
        """Test chat with message exceeding length limit."""
        long_message = "A" * 5000  # Assuming 4000 char limit
        chat_payload = {"message": long_message}
        response = requests.post(f"{BASE_URL}/chat", json=chat_payload)
        
        # Should either be rejected or truncated
        assert response.status_code in [200, 400, 422]
    
    def test_invalid_feedback_payload(self, server_health_check):
        """Test feedback with invalid payload."""
        invalid_payloads = [
            {"message": "", "user_feedback": "thumbs_up"},  # Empty message
            {"message": "test", "user_feedback": "invalid_feedback"},  # Invalid feedback type
            {"user_feedback": "thumbs_up"},  # Missing message
        ]
        
        for payload in invalid_payloads:
            response = requests.post(f"{BASE_URL}/feedback", json=payload)
            assert response.status_code in [400, 422]
    
    def test_chat_history_with_invalid_limit(self, server_health_check):
        """Test chat history with invalid limit parameters."""
        # Test negative limit
        response = requests.get(f"{BASE_URL}/chat-history?limit=-1")
        assert response.status_code == 422
        
        # Test excessive limit
        response = requests.get(f"{BASE_URL}/chat-history?limit=1000")
        assert response.status_code == 422
