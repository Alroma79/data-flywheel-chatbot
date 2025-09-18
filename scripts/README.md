# Project Utility Scripts

This directory contains development and validation scripts to assist with project setup, testing, and maintenance.

## Available Scripts

### start.py
A comprehensive startup script for the Data Flywheel Chatbot. It helps users:
- Check Python version compatibility
- Verify .env configuration
- Install project dependencies
- Initialize the database
- Start the FastAPI server

### run_validation.py
A validation runner that:
- Checks project dependencies
- Runs smoke tests
- Executes full automated test suite
- Provides manual testing guidance

### validate_docker.py
A Docker configuration validation script that:
- Checks Docker and Docker Compose availability
- Tests Docker image build
- Validates container run
- Verifies Docker Compose functionality
- Runs tests inside the container

## Usage

Each script is designed to be run from the project root directory. Always ensure you have activated your virtual environment and installed dependencies before running these scripts.