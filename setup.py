#!/usr/bin/env python3
"""
Data Flywheel Chatbot Setup Script
Runs migrations/init, seeds active config, and runs tests
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None, shell=False):
    """Run a command and return success status"""
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            shell=shell, 
            check=True,
            capture_output=True,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def write_step(message):
    """Print step message"""
    print(f"\033[92m==> {message}\033[0m")

def write_error(message):
    """Print error message"""
    print(f"\033[91mERROR: {message}\033[0m")

def write_success(message):
    """Print success message"""
    print(f"\033[92mSUCCESS: {message}\033[0m")

def main():
    parser = argparse.ArgumentParser(description='Setup Data Flywheel Chatbot')
    parser.add_argument('--skip-tests', action='store_true', 
                      help='Skip running tests after setup')
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    print("\033[96mData Flywheel Chatbot Setup\033[0m")
    print("\033[96m=========================\033[0m")
    print()

    backend_dir = script_dir / 'backend'
    
    # Step 1: Database Migration
    write_step("Initializing database and applying migrations")
    
    # Initialize database
    success, output = run_command([
        sys.executable, '-c', 
        'from app.init_db import init_database; init_database()'
    ], cwd=backend_dir)
    
    if success:
        write_success("Database initialized successfully")
    else:
        write_error(f"Failed to initialize database: {output}")
        return 1

    # Apply migration
    write_step("Applying database migration")
    success, output = run_command([
        sys.executable, '-c',
        "from app.migrations.add_session_columns import run_migration; run_migration('chatbot.db')"
    ], cwd=backend_dir)
    
    if success:
        write_success("Database migration completed")
    else:
        write_error(f"Failed to apply migration: {output}")
        return 1

    # Step 2: Seed Configuration  
    write_step("Seeding active configuration")
    
    seed_script = """
import sys
sys.path.append('.')
from app.db import SessionLocal
from app.models import ChatbotConfig
import json

session = SessionLocal()
try:
    # Check for existing active config
    config = session.query(ChatbotConfig).filter(ChatbotConfig.is_active == True).first()
    if not config:
        default_config = ChatbotConfig(
            name='dev-default',
            config_json={
                'model': 'gpt-4o-mini',
                'temperature': 0.3,
                'system_prompt': 'You are a helpful assistant.',
                'max_tokens': None
            },
            is_active=True
        )
        session.add(default_config)
        session.commit()
        print('Created default active configuration')
    else:
        print(f'Active configuration already exists: {config.name}')
finally:
    session.close()
"""
    
    success, output = run_command([
        sys.executable, '-c', seed_script
    ], cwd=backend_dir)
    
    if success:
        write_success("Configuration seeded successfully")
        if output.strip():
            print(f"  {output.strip()}")
    else:
        write_error(f"Failed to seed configuration: {output}")
        return 1

    # Step 3: Verify Schema
    write_step("Verifying database schema")
    
    try:
        success, output = run_command([
            'sqlite3', 'chatbot.db', 'PRAGMA table_info(chat_history);'
        ], cwd=backend_dir)
        
        if success and 'session_id' in output and 'role' in output and 'content' in output:
            write_success("Database schema verified - all required columns present")
        else:
            write_error("Schema verification failed - missing required columns")
            return 1
    except FileNotFoundError:
        # sqlite3 not available, skip verification
        print("  \033[93mWARNING: sqlite3 not found, skipping schema verification\033[0m")

    # Step 4: Run Tests (unless skipped)
    if not args.skip_tests:
        write_step("Running tests")
        success, output = run_command([
            sys.executable, '-m', 'pytest', 
            'tests/test_chat_sessions.py', '-v', '--tb=short'
        ], cwd=backend_dir)
        
        if success:
            write_success("All tests passed")
        else:
            write_error(f"Test execution failed: {output}")
            return 1

    print()
    write_success("Setup completed successfully!")
    print()
    print("\033[96mNext steps:\033[0m")
    print("1. Start the server: cd backend && uvicorn app.main:app --reload")
    print("2. Open browser: http://localhost:8000/")
    print("3. Test API: http://localhost:8000/docs")
    print()
    print("\033[93mDatabase location: backend/chatbot.db\033[0m")
    print("\033[93mTo view chat history: sqlite3 backend/chatbot.db 'SELECT * FROM chat_history;'\033[0m")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())