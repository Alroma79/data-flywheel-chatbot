#!/usr/bin/env python3
"""
Test script for frontend integration.
Verifies that the frontend is properly served and API endpoints work.
"""

import requests
import sys
import time

BASE_URL = "http://127.0.0.1:8000"

def test_frontend_serving():
    """Test that the frontend HTML is served at root."""
    print("🔄 Testing frontend serving...")
    
    try:
        response = requests.get(BASE_URL, timeout=5)
        
        if response.status_code == 200:
            content = response.text
            if "Data Flywheel Chatbot" in content and "app.js" in content:
                print("✅ Frontend HTML served successfully")
                return True
            else:
                print("❌ Frontend HTML content incorrect")
                return False
        else:
            print(f"❌ Frontend serving failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend serving error: {str(e)}")
        return False

def test_static_js_serving():
    """Test that JavaScript file is served."""
    print("🔄 Testing JavaScript file serving...")
    
    try:
        response = requests.get(f"{BASE_URL}/app.js", timeout=5)
        
        if response.status_code == 200:
            content = response.text
            if "api.post" in content and "sendMessage" in content:
                print("✅ JavaScript file served successfully")
                return True
            else:
                print("❌ JavaScript file content incorrect")
                return False
        else:
            print(f"❌ JavaScript serving failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ JavaScript serving error: {str(e)}")
        return False

def test_api_endpoints_accessible():
    """Test that API endpoints are still accessible."""
    print("🔄 Testing API endpoint accessibility...")
    
    endpoints_to_test = [
        "/api/v1/chat-history",
        "/health"
    ]
    
    success_count = 0
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code in [200, 422]:  # 422 is OK for chat-history without params
                print(f"   ✅ {endpoint} accessible")
                success_count += 1
            else:
                print(f"   ❌ {endpoint} failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint} error: {str(e)}")
    
    if success_count == len(endpoints_to_test):
        print("✅ All API endpoints accessible")
        return True
    else:
        print(f"❌ {success_count}/{len(endpoints_to_test)} API endpoints accessible")
        return False

def test_cors_headers():
    """Test that CORS headers are properly set."""
    print("🔄 Testing CORS headers...")
    
    try:
        response = requests.options(f"{BASE_URL}/api/v1/chat", 
                                  headers={"Origin": "http://localhost:8000"}, 
                                  timeout=5)
        
        cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers"
        ]
        
        found_headers = 0
        for header in cors_headers:
            if header in response.headers:
                found_headers += 1
        
        if found_headers >= 2:  # At least 2 CORS headers should be present
            print("✅ CORS headers configured correctly")
            return True
        else:
            print(f"❌ CORS headers missing: found {found_headers}/{len(cors_headers)}")
            return False
            
    except Exception as e:
        print(f"❌ CORS test error: {str(e)}")
        return False

def check_server_running():
    """Check if server is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Run frontend integration tests."""
    print("🧪 Frontend Integration Test Suite")
    print("=" * 50)
    
    # Check if server is running
    if not check_server_running():
        print("❌ Server is not running. Please start it first:")
        print("   cd backend && uvicorn app.main:app --reload")
        sys.exit(1)
    
    print("✅ Server is running")
    print()
    
    # Run tests
    tests = [
        ("Frontend HTML Serving", test_frontend_serving),
        ("JavaScript File Serving", test_static_js_serving),
        ("API Endpoints Accessible", test_api_endpoints_accessible),
        ("CORS Configuration", test_cors_headers)
    ]
    
    passed_tests = 0
    
    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        if test_func():
            passed_tests += 1
        print()
    
    # Summary
    print("📊 Test Results Summary:")
    print(f"   Passed: {passed_tests}/{len(tests)} tests")
    
    if passed_tests == len(tests):
        print("\n🎉 All frontend integration tests passed!")
        print("\n🌐 Frontend is ready! Open: http://localhost:8000/")
        print("\n📋 Manual Testing Checklist:")
        print("   □ Upload a knowledge file")
        print("   □ Send a chat message")
        print("   □ Verify knowledge sources appear")
        print("   □ Click feedback buttons")
        print("   □ Load chat history")
        print("   □ Check browser console for errors")
    else:
        print(f"\n❌ {len(tests) - passed_tests} tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
