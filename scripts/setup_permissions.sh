#!/bin/bash
# Setup script permissions for Linux/Mac

echo "🔧 Setting up script permissions..."

# Make all shell scripts executable
chmod +x scripts/*.sh

echo "✅ Script permissions set:"
ls -la scripts/*.sh

echo ""
echo "📋 You can now run:"
echo "   ./scripts/run_docker.sh    - Build and run the application"
echo "   ./scripts/test_docker.sh   - Run tests in Docker"
