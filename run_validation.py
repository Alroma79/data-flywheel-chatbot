#!/usr/bin/env python3
"""
Comprehensive validation runner for Data Flywheel Chatbot.
Runs both automated tests and provides manual testing guidance.
"""

import subprocess
import sys
import requests
import time
import os, pathlib
BACKEND = pathlib.Path(__file__).parent / "backend"
os.environ.setdefault("PYTHONPATH", str(BACKEND))


def check_server_running():
    """Check if the server is running."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def run_automated_tests():
    """Run all automated tests using pytest."""
    print("🧪 Running Automated Tests")
    print("=" * 50)
    
    if not check_server_running():
        print("❌ Server is not running!")
        print("Please start the server first:")
        print("   cd backend && uvicorn app.main:app --reload")
        return False
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        success = result.returncode == 0
        print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")
        return success
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_quick_smoke_test():
    """Run a quick smoke test of core functionality."""
    print("\n🔥 Running Quick Smoke Test")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    tests = [
        ("Server Health", lambda: requests.get(f"{base_url}/health").status_code == 200),
        ("Frontend Loading", lambda: "Data Flywheel Chatbot" in requests.get(base_url).text),
        ("JavaScript Serving", lambda: "sendMessage" in requests.get(f"{base_url}/app.js").text),
        ("Chat API", lambda: requests.post(f"{base_url}/api/v1/chat", 
                                         json={"message": "test"}).status_code == 200),
        ("History API", lambda: requests.get(f"{base_url}/api/v1/chat-history").status_code == 200),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {test_name}")
                passed += 1
            else:
                print(f"❌ {test_name}")
        except Exception as e:
            print(f"❌ {test_name} - Error: {e}")
    
    print(f"\nSmoke Test Results: {passed}/{len(tests)} passed")
    return passed == len(tests)

def show_manual_testing_guide():
    """Display manual testing instructions."""
    print("\n📋 Manual Testing Guide")
    print("=" * 50)
    print("1. Open browser: http://localhost:8000/")
    print("2. Upload test_knowledge.txt file")
    print("3. Ask: 'What is machine learning?'")
    print("4. Verify knowledge sources appear")
    print("5. Click 👍 feedback button")
    print("6. Click 'Load Recent' button")
    print("7. Verify conversation history loads")
    print("\nFor detailed instructions, see: DOCS AND PICS/03_validation.md")

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking Dependencies")
    print("=" * 30)
    
    required_packages = ['pytest', 'requests', 'fastapi', 'uvicorn']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Install with: pip install -r backend/app/requirements.txt")
        return False
    
    return True

def main():
    """Main validation runner."""
    print("🚀 Data Flywheel Chatbot - Validation Suite")
    print("=" * 60)
    print("Validating Task 1 (Knowledge Integration) & Task 2 (Frontend)")
    print()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    print()
    
    # Check if server is running
    if not check_server_running():
        print("❌ Server is not running!")
        print("\nTo start the server:")
        print("   cd backend")
        print("   uvicorn app.main:app --reload")
        print("\nThen run this script again.")
        sys.exit(1)
    
    print("✅ Server is running")
    print()
    
    # Run smoke test first
    smoke_passed = run_quick_smoke_test()
    
    if not smoke_passed:
        print("\n❌ Smoke test failed. Please check server configuration.")
        sys.exit(1)
    
    # Run full automated tests
    tests_passed = run_automated_tests()
    
    # Show manual testing guide
    show_manual_testing_guide()
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Smoke Test: {'✅ PASS' if smoke_passed else '❌ FAIL'}")
    print(f"Automated Tests: {'✅ PASS' if tests_passed else '❌ FAIL'}")
    print("Manual Tests: 📋 See guide above")
    
    if smoke_passed and tests_passed:
        print("\n🎉 Validation successful! Ready for Task 3 (Docker & Tests)")
        print("\nNext steps:")
        print("1. Complete manual testing checklist")
        print("2. Document results in DOCS AND PICS/03_validation.md")
        print("3. Proceed to Docker containerization")
    else:
        print("\n❌ Validation failed. Please fix issues before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
