#!/usr/bin/env python3
"""
Startup script for the Data Flywheel Chatbot application.

This script helps users quickly start the application with proper setup.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_env_file():
    """Check if .env file exists."""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("📝 Please copy .env.example to .env and configure your settings")
        print("   Especially set your OPENAI_API_KEY")
        return False
    print("✅ .env file found")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, cwd=".")
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def initialize_database():
    """Initialize the database."""
    print("🗄️  Initializing database...")
    try:
        subprocess.run([
            sys.executable, "-c", 
            "import sys; sys.path.append('backend/app'); from init_db import init_database; init_database()"
        ], check=True, cwd=".")
        print("✅ Database initialized successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to initialize database")
        return False

def start_server():
    """Start the FastAPI server."""
    print("🚀 Starting the Data Flywheel Chatbot server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API documentation: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop the server")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--reload", "--host", "0.0.0.0", "--port", "8000"
        ], cwd="backend/app")
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except subprocess.CalledProcessError:
        print("❌ Failed to start server")

def main():
    """Main startup function."""
    print("🤖 Data Flywheel Chatbot Startup Script")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Check environment file
    if not check_env_file():
        return
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Initialize database
    if not initialize_database():
        return
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
