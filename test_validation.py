#!/usr/bin/env python3
"""
Test script to debug the validation issue with the chat endpoint.
"""

import sys
import json
import requests
from pydantic import ValidationError

# Add backend app to path
sys.path.append('backend/app')

def test_pydantic_validation():
    """Test Pydantic validation directly."""
    print("=== Testing Pydantic Validation ===")
    try:
        from schemas import ChatRequest
        
        # Test with the same data we're sending via curl
        test_data = {"message": "Hello!"}
        print(f"Testing with data: {test_data}")
        
        request = ChatRequest(**test_data)
        print(f"✅ Pydantic validation passed: {request.message}")
        return True
        
    except ValidationError as e:
        print(f"❌ Pydantic validation failed:")
        print(f"Errors: {e.errors()}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

def test_fastapi_endpoint():
    """Test the FastAPI endpoint directly."""
    print("\n=== Testing FastAPI Endpoint ===")
    try:
        url = "http://127.0.0.1:8000/api/v1/chat"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        data = {"message": "Hello!"}
        
        print(f"Sending POST to {url}")
        print(f"Headers: {headers}")
        print(f"Data: {data}")
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 422:
            try:
                error_data = response.json()
                print(f"Validation Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print("Could not parse error response as JSON")
        
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server - is it running?")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_config_loading():
    """Test configuration loading."""
    print("\n=== Testing Configuration Loading ===")
    try:
        from config import get_settings
        settings = get_settings()
        print(f"✅ Settings loaded successfully")
        print(f"Debug: {settings.debug}")
        print(f"Database URL: {settings.database_url}")
        return True
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Debugging Chat Endpoint Validation Issue")
    print("=" * 50)
    
    # Test configuration first
    config_ok = test_config_loading()
    
    # Test Pydantic validation
    pydantic_ok = test_pydantic_validation()
    
    # Test FastAPI endpoint
    endpoint_ok = test_fastapi_endpoint()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"Config Loading: {'✅' if config_ok else '❌'}")
    print(f"Pydantic Validation: {'✅' if pydantic_ok else '❌'}")
    print(f"FastAPI Endpoint: {'✅' if endpoint_ok else '❌'}")
    
    if not endpoint_ok and pydantic_ok:
        print("\n💡 The issue seems to be with the FastAPI endpoint, not Pydantic validation.")
        print("   This could be a middleware, routing, or server configuration issue.")
