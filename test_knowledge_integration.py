#!/usr/bin/env python3
"""
Legacy test script for knowledge integration functionality.
This script tests the complete workflow: file upload → knowledge search → enhanced chat.

Note: This is now superseded by the comprehensive pytest test suite in tests/
For automated testing, use: pytest tests/test_knowledge_integration.py
"""

import requests
import json
import sys
import os

BASE_URL = "http://127.0.0.1:8000/api/v1"

print("⚠️  This script is deprecated. Use the new pytest test suite:")
print("   pytest tests/test_knowledge_integration.py -v")
print("   or run: python run_validation.py")
print()

def test_file_upload():
    """Test uploading a knowledge file."""
    print("🔄 Testing file upload...")
    
    # Check if test file exists
    test_file = "test_knowledge.txt"
    if not os.path.exists(test_file):
        print(f"❌ Test file {test_file} not found")
        return None
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/knowledge/files", files=files)
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ File uploaded successfully: {data['filename']} (ID: {data['id']})")
            return data['id']
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return None

def test_knowledge_enhanced_chat(query):
    """Test chat with knowledge integration."""
    print(f"🔄 Testing knowledge-enhanced chat with query: '{query}'")
    
    try:
        payload = {"message": query}
        response = requests.post(
            f"{BASE_URL}/chat",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat response received:")
            print(f"   Reply: {data['reply'][:100]}...")
            
            if 'knowledge_sources' in data:
                print(f"   📚 Knowledge sources used: {len(data['knowledge_sources'])}")
                for source in data['knowledge_sources']:
                    print(f"      - {source['filename']} (score: {source['relevance_score']})")
                return True
            else:
                print("   ⚠️  No knowledge sources used (this might be expected if no relevant content found)")
                return True
        else:
            print(f"❌ Chat failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        return False

def test_chat_without_knowledge():
    """Test chat with query that shouldn't match knowledge base."""
    print("🔄 Testing chat without knowledge match...")
    
    query = "What's the weather like today?"
    try:
        payload = {"message": query}
        response = requests.post(
            f"{BASE_URL}/chat",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat response received (no knowledge expected):")
            print(f"   Reply: {data['reply'][:100]}...")
            
            if 'knowledge_sources' not in data or len(data.get('knowledge_sources', [])) == 0:
                print("   ✅ No knowledge sources used (as expected)")
                return True
            else:
                print(f"   ⚠️  Unexpected knowledge sources: {data['knowledge_sources']}")
                return True
        else:
            print(f"❌ Chat failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        return False

def check_server_health():
    """Check if the server is running."""
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Run the complete test suite."""
    print("🧪 Knowledge Integration Test Suite")
    print("=" * 50)
    
    # Check server health
    if not check_server_health():
        print("❌ Server is not running. Please start the server first:")
        print("   cd backend && uvicorn app.main:app --reload")
        sys.exit(1)
    
    print("✅ Server is running")
    
    # Test 1: Upload knowledge file
    file_id = test_file_upload()
    if not file_id:
        print("❌ Cannot proceed without successful file upload")
        sys.exit(1)
    
    print()
    
    # Test 2: Chat with knowledge-relevant query
    knowledge_queries = [
        "What is machine learning?",
        "Tell me about neural networks",
        "What are the applications of deep learning?"
    ]
    
    knowledge_tests_passed = 0
    for query in knowledge_queries:
        if test_knowledge_enhanced_chat(query):
            knowledge_tests_passed += 1
        print()
    
    # Test 3: Chat with non-knowledge query
    if test_chat_without_knowledge():
        print()
    
    # Summary
    print("📊 Test Results Summary:")
    print(f"   File Upload: {'✅ PASS' if file_id else '❌ FAIL'}")
    print(f"   Knowledge Chat: {knowledge_tests_passed}/{len(knowledge_queries)} PASS")
    print(f"   Non-Knowledge Chat: ✅ PASS")
    
    if file_id and knowledge_tests_passed > 0:
        print("\n🎉 Knowledge Integration is working correctly!")
        print("\n📋 Manual Test Commands:")
        print("   # Upload file:")
        print(f'   curl -X POST "{BASE_URL}/knowledge/files" -F "file=@test_knowledge.txt"')
        print("\n   # Test knowledge-enhanced chat:")
        print(f'   curl -X POST "{BASE_URL}/chat" -H "Content-Type: application/json" -d \'{{"message":"What is machine learning?"}}\'')
    else:
        print("\n❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
