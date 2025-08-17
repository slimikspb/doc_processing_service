#!/bin/bash

echo "🔧 Fixing Celery Beat Permissions Issue"
echo "====================================="

# Stop the current deployment
echo "1. Stopping current containers..."
docker-compose -f docker-compose.reliable.yml down

# Rebuild with the fixed permissions
echo "2. Rebuilding with permissions fix..."
docker-compose -f docker-compose.reliable.yml build --no-cache

# Start the fixed version
echo "3. Starting the fixed version..."
docker-compose -f docker-compose.reliable.yml up -d

# Wait and check status
echo "4. Checking container status..."
sleep 10
docker-compose -f docker-compose.reliable.yml ps

# Check logs specifically for celery-beat
echo "5. Checking celery-beat logs..."
docker-compose -f docker-compose.reliable.yml logs celery-beat | tail -10

echo ""
echo "✅ Fix applied! Celery beat now uses /tmp for schedule file."
echo "Testing the service..."

# Quick test
sleep 5
curl -s http://localhost:5001/health || echo "Service not ready yet, check logs above"