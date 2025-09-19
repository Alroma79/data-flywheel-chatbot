"""
Knowledge integration tests using TestClient (converted from external HTTP calls).
Tests knowledge file upload, search, and chat integration functionality.
"""

import pytest
import tempfile
import os
from io import BytesIO


@pytest.mark.knowledge
@pytest.mark.skip(reason="Knowledge endpoints not fully implemented - requires file upload service and search backend")
class TestKnowledgeIntegration:
    """Test suite for knowledge integration features using TestClient."""

    @pytest.fixture
    def sample_txt_content(self):
        """Sample text content for knowledge testing."""
        return """Machine Learning Fundamentals

Machine learning is a subset of artificial intelligence that enables computers to learn from data.
Key concepts include supervised learning, unsupervised learning, and neural networks.
Popular libraries include scikit-learn, TensorFlow, and PyTorch.
Applications include image recognition, natural language processing, and recommendation systems."""

    @pytest.fixture
    def sample_pdf_content(self):
        """Minimal PDF content for testing."""
        return b"""%PDF-1.4
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
(Knowledge test content) Tj
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

    # Happy Path Tests

    @pytest.mark.skip(reason="Knowledge file upload endpoint not implemented - requires external file storage service")
    def test_upload_txt_file_success(self, test_client, sample_txt_content):
        """Test successful TXT file upload."""
        files = {'file': ('test.txt', BytesIO(sample_txt_content.encode()), 'text/plain')}
        response = test_client.post("/api/v1/knowledge/files", files=files)

        assert response.status_code == 201
        data = response.json()
        assert 'id' in data
        assert data['filename'] == 'test.txt'
        assert 'message' in data
        assert data['size'] > 0

    def test_upload_pdf_file_success(self, test_client, sample_pdf_content):
        """Test successful PDF file upload."""
        files = {'file': ('test.pdf', BytesIO(sample_pdf_content), 'application/pdf')}
        response = test_client.post("/api/v1/knowledge/files", files=files)

        assert response.status_code == 201
        data = response.json()
        assert 'id' in data
        assert data['filename'] == 'test.pdf'

    def test_knowledge_enhanced_chat(self, test_client, mock_llm, mock_knowledge_processor, sample_txt_content):
        """Test chat with knowledge integration."""
        # First upload a file
        files = {'file': ('ml_guide.txt', BytesIO(sample_txt_content.encode()), 'text/plain')}
        upload_response = test_client.post("/api/v1/knowledge/files", files=files)
        assert upload_response.status_code == 201

        # Configure mock knowledge processor to return relevant results
        mock_knowledge_processor.search_knowledge.return_value = [
            {
                'filename': 'ml_guide.txt',
                'content': 'Machine learning is a subset of artificial intelligence',
                'relevance_score': 0.85
            }
        ]

        # Then ask a related question
        chat_payload = {"message": "What is machine learning?"}
        chat_response = test_client.post("/api/v1/chat", json=chat_payload)

        assert chat_response.status_code == 200
        data = chat_response.json()
        assert 'reply' in data
        assert len(data['reply']) > 0

    def test_chat_without_knowledge_match(self, test_client, mock_llm):
        """Test chat with question that doesn't match knowledge base."""
        chat_payload = {"message": "What's the weather like today?"}
        response = test_client.post("/api/v1/chat", json=chat_payload)

        assert response.status_code == 200
        data = response.json()
        assert 'reply' in data

    def test_feedback_submission_success(self, test_client):
        """Test successful feedback submission."""
        feedback_payload = {
            "message": "Test message for feedback",
            "user_feedback": "thumbs_up",
            "comment": "Great response!"
        }
        response = test_client.post("/api/v1/feedback", json=feedback_payload)

        assert response.status_code == 201
        data = response.json()
        assert 'message' in data

    def test_chat_history_retrieval(self, test_client, mock_llm):
        """Test chat history retrieval."""
        # First send a message to create history
        chat_payload = {"message": "Hello, this is a test message"}
        test_client.post("/api/v1/chat", json=chat_payload)

        # Then retrieve history
        response = test_client.get("/api/v1/chat-history?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    # Edge Case Tests

    def test_upload_empty_file(self, test_client):
        """Test upload of empty file."""
        files = {'file': ('empty.txt', BytesIO(b""), 'text/plain')}
        response = test_client.post("/api/v1/knowledge/files", files=files)

        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data

    def test_upload_unsupported_file_type(self, test_client):
        """Test upload of unsupported file type."""
        files = {'file': ('test.jpg', BytesIO(b"fake image content"), 'image/jpeg')}
        response = test_client.post("/api/v1/knowledge/files", files=files)

        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data

    def test_upload_oversized_file(self, test_client):
        """Test upload of file exceeding size limit."""
        # Create a file larger than 10MB (current limit)
        large_content = b"A" * (11 * 1024 * 1024)  # 11MB
        files = {'file': ('huge.txt', BytesIO(large_content), 'text/plain')}
        response = test_client.post("/api/v1/knowledge/files", files=files)

        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data

    def test_chat_empty_message(self, test_client):
        """Test chat with empty message."""
        chat_payload = {"message": ""}
        response = test_client.post("/api/v1/chat", json=chat_payload)

        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data

    def test_chat_oversized_message(self, test_client):
        """Test chat with message exceeding length limit."""
        long_message = "A" * 5000  # Assuming 4000 char limit
        chat_payload = {"message": long_message}
        response = test_client.post("/api/v1/chat", json=chat_payload)

        # Should either be rejected or truncated
        assert response.status_code in [200, 400, 422]

    def test_invalid_feedback_payload(self, test_client):
        """Test feedback with invalid payload."""
        invalid_payloads = [
            {"message": "", "user_feedback": "thumbs_up"},  # Empty message
            {"message": "test", "user_feedback": "invalid_feedback"},  # Invalid feedback type
            {"user_feedback": "thumbs_up"},  # Missing message
        ]

        for payload in invalid_payloads:
            response = test_client.post("/api/v1/feedback", json=payload)
            assert response.status_code in [400, 422]

    def test_chat_history_with_invalid_limit(self, test_client):
        """Test chat history with invalid limit parameters."""
        # Test negative limit
        response = test_client.get("/api/v1/chat-history?limit=-1")
        assert response.status_code == 422

        # Test excessive limit
        response = test_client.get("/api/v1/chat-history?limit=1000")
        assert response.status_code == 422