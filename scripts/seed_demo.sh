#!/bin/bash
# Demo seed script for Data Flywheel Chatbot (Linux/Mac)

set -e

echo "🌱 Seeding Demo Data for Data Flywheel Chatbot"
echo "============================================="

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Server is not running!"
    echo "Please start the server first:"
    echo "   docker compose up -d"
    echo "   or"
    echo "   cd backend && uvicorn app.main:app --reload"
    exit 1
fi

echo "✅ Server is running"

# Upload sample knowledge file
echo "📁 Uploading sample knowledge file..."
if [ -f "docs/sample_knowledge.txt" ]; then
    curl -X POST "http://localhost:8000/api/v1/knowledge/files" \
         -F "file=@docs/sample_knowledge.txt" \
         -H "Accept: application/json" | jq '.'
    
    if [ $? -eq 0 ]; then
        echo "✅ Sample knowledge file uploaded successfully"
    else
        echo "❌ Failed to upload knowledge file"
        exit 1
    fi
else
    echo "❌ Sample knowledge file not found at docs/sample_knowledge.txt"
    exit 1
fi

# Create a sample chatbot configuration
echo "⚙️  Creating sample chatbot configuration..."
curl -X POST "http://localhost:8000/api/v1/config" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "demo_config",
       "config_json": {
         "system_prompt": "You are a helpful AI assistant specializing in data flywheels and business intelligence. Use the provided knowledge base to give accurate, well-sourced answers.",
         "model": "gpt-4o",
         "temperature": 0.7,
         "max_tokens": 1000
       },
       "is_active": true,
       "tags": ["demo", "data-flywheel"]
     }' | jq '.'

if [ $? -eq 0 ]; then
    echo "✅ Sample configuration created successfully"
else
    echo "❌ Failed to create sample configuration"
    exit 1
fi

# Send a sample chat message to create history
echo "💬 Creating sample chat history..."
curl -X POST "http://localhost:8000/api/v1/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "What is a data flywheel?"}' | jq '.'

if [ $? -eq 0 ]; then
    echo "✅ Sample chat history created"
else
    echo "❌ Failed to create sample chat"
fi

echo ""
echo "🎉 Demo seeding completed successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Open http://localhost:8000/ in your browser"
echo "   2. Try asking: 'What are the benefits of data flywheels?'"
echo "   3. Notice the knowledge sources in the response"
echo "   4. Click 👍 to provide feedback"
echo "   5. Click 'Load Recent' to see conversation history"
echo ""
echo "🔗 You can also test the API with the Postman collection:"
echo "   Import docs/Flywheel.postman_collection.json"
