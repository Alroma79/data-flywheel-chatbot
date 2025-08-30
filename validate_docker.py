#!/usr/bin/env python3
"""
Docker validation script for Data Flywheel Chatbot.
Validates that Docker build, run, and test execution work correctly.
"""

import subprocess
import sys
import time
import requests
import json

def run_command(cmd, description, capture_output=True):
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"✅ {description} - Success")
                return True, result.stdout
            else:
                print(f"❌ {description} - Failed")
                print(f"Error: {result.stderr}")
                return False, result.stderr
        else:
            result = subprocess.run(cmd, shell=True, timeout=300)
            success = result.returncode == 0
            print(f"{'✅' if success else '❌'} {description} - {'Success' if success else 'Failed'}")
            return success, ""
    except subprocess.TimeoutExpired:
        print(f"❌ {description} - Timeout")
        return False, "Timeout"
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False, str(e)

def check_docker_available():
    """Check if Docker is available."""
    success, _ = run_command("docker --version", "Checking Docker availability")
    return success

def check_docker_compose_available():
    """Check if Docker Compose is available."""
    success, _ = run_command("docker compose version", "Checking Docker Compose availability")
    return success

def build_docker_image():
    """Build the Docker image."""
    return run_command("docker build -t flywheel .", "Building Docker image")

def test_docker_run():
    """Test running the Docker container."""
    # Clean up any existing container
    run_command("docker stop flywheel-test 2>/dev/null || true", "Cleaning up existing container")
    run_command("docker rm flywheel-test 2>/dev/null || true", "Removing existing container")
    
    # Start container in background
    success, _ = run_command(
        "docker run -d --name flywheel-test -p 8001:8000 "
        "-e OPENAI_API_KEY=sk-test-key-for-testing flywheel",
        "Starting Docker container"
    )
    
    if not success:
        return False
    
    # Wait for container to be ready
    print("⏳ Waiting for container to be ready...")
    time.sleep(10)
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:8001/health", timeout=10)
        if response.status_code == 200:
            print("✅ Container health check - Success")
            health_success = True
        else:
            print(f"❌ Container health check - Failed (status: {response.status_code})")
            health_success = False
    except Exception as e:
        print(f"❌ Container health check - Error: {e}")
        health_success = False
    
    # Test frontend serving
    try:
        response = requests.get("http://localhost:8001/", timeout=10)
        if response.status_code == 200 and "Data Flywheel Chatbot" in response.text:
            print("✅ Frontend serving - Success")
            frontend_success = True
        else:
            print("❌ Frontend serving - Failed")
            frontend_success = False
    except Exception as e:
        print(f"❌ Frontend serving - Error: {e}")
        frontend_success = False
    
    # Clean up
    run_command("docker stop flywheel-test", "Stopping test container")
    run_command("docker rm flywheel-test", "Removing test container")
    
    return health_success and frontend_success

def test_docker_compose():
    """Test Docker Compose functionality."""
    # Clean up
    run_command("docker compose down", "Cleaning up Docker Compose")
    
    # Test compose build
    success, _ = run_command("docker compose build", "Building with Docker Compose")
    if not success:
        return False
    
    # Test compose up (detached)
    success, _ = run_command("docker compose up -d", "Starting with Docker Compose")
    if not success:
        return False
    
    # Wait for service to be ready
    print("⏳ Waiting for Docker Compose service...")
    time.sleep(10)
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        compose_success = response.status_code == 200
        print(f"{'✅' if compose_success else '❌'} Docker Compose health check")
    except Exception as e:
        print(f"❌ Docker Compose health check - Error: {e}")
        compose_success = False
    
    # Clean up
    run_command("docker compose down", "Stopping Docker Compose")
    
    return compose_success

def test_in_container_tests():
    """Test running pytest inside the container."""
    return run_command(
        "docker compose run --rm test",
        "Running tests in container"
    )

def main():
    """Main validation function."""
    print("🐳 Docker Validation Suite for Data Flywheel Chatbot")
    print("=" * 60)
    
    # Check prerequisites
    if not check_docker_available():
        print("❌ Docker is not available. Please install Docker first.")
        sys.exit(1)
    
    if not check_docker_compose_available():
        print("❌ Docker Compose is not available. Please install Docker Compose first.")
        sys.exit(1)
    
    print("✅ Prerequisites met")
    print()
    
    # Run validation tests
    tests = [
        ("Docker Image Build", build_docker_image),
        ("Docker Container Run", test_docker_run),
        ("Docker Compose", test_docker_compose),
        ("In-Container Tests", test_in_container_tests),
    ]
    
    passed_tests = 0
    failed_tests = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        
        success, _ = test_func()
        if success:
            passed_tests += 1
            print(f"✅ {test_name} - PASSED")
        else:
            failed_tests.append(test_name)
            print(f"❌ {test_name} - FAILED")
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 DOCKER VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed_tests}/{len(tests)} tests")
    
    if failed_tests:
        print(f"Failed tests: {', '.join(failed_tests)}")
        print("\n❌ Docker validation failed")
        print("\n📋 Troubleshooting:")
        print("   - Check Docker is running: docker ps")
        print("   - Check logs: docker compose logs")
        print("   - Verify .env file exists with OPENAI_API_KEY")
        print("   - See DOCS/04_docker_guide.md for detailed troubleshooting")
        sys.exit(1)
    else:
        print("\n🎉 All Docker validation tests passed!")
        print("\n📋 Docker setup is ready for production:")
        print("   - Build: docker build -t flywheel .")
        print("   - Run: docker compose up -d")
        print("   - Test: docker compose run --rm test")
        print("   - Monitor: docker compose logs -f")
        print("\n✅ Ready for deployment!")

if __name__ == "__main__":
    main()
