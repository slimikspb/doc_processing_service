#!/bin/bash

echo "🧪 Quick Test of Document Processing Service"
echo "==========================================="

# Create a test text file
echo "This is a test document for the document processing service." > test_document.txt
echo "It contains some text that should be extracted successfully." >> test_document.txt

# Test 1: Health check (no API key needed)
echo "1. Testing health endpoint..."
curl -s http://localhost:5001/health | jq . || curl -s http://localhost:5001/health

echo -e "\n\n2. Testing supported formats..."
curl -s http://localhost:5001/formats | jq . || curl -s http://localhost:5001/formats

# Test 3: Document conversion (API key required)
echo -e "\n\n3. Testing document conversion..."
curl -X POST http://localhost:5001/convert \
  -H "X-API-Key: default_dev_key" \
  -F "file=@test_document.txt" \
  | jq . || echo "jq not available, showing raw output"

# Test 4: Async processing
echo -e "\n\n4. Testing async processing..."
RESPONSE=$(curl -s -X POST "http://localhost:5001/convert?async=true" \
  -H "X-API-Key: default_dev_key" \
  -F "file=@test_document.txt")

echo "Async response: $RESPONSE"

# Extract task ID and check status
TASK_ID=$(echo $RESPONSE | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)

if [ ! -z "$TASK_ID" ]; then
    echo "Task ID: $TASK_ID"
    echo "Checking task status..."
    sleep 2
    curl -s http://localhost:5001/task/$TASK_ID \
      -H "X-API-Key: default_dev_key" \
      | jq . || curl -s http://localhost:5001/task/$TASK_ID -H "X-API-Key: default_dev_key"
fi

# Cleanup
rm -f test_document.txt

echo -e "\n\n✅ Quick test completed!"