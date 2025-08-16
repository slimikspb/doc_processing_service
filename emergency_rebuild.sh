#!/bin/bash

echo "🔥 EMERGENCY DOCKER REBUILD - CLEARING ALL CACHES 🔥"
echo "=================================================="

# Stop and remove everything
echo "1. Stopping all containers..."
docker-compose down --remove-orphans

echo "2. Removing all volumes..."
docker-compose down -v

echo "3. Removing all images related to this project..."
docker-compose down --rmi all

echo "4. Pruning system (removes unused images, containers, networks)..."
docker system prune -af

echo "5. Building with no cache..."
docker-compose build --no-cache --pull

echo "6. Starting services..."
docker-compose up -d

echo "7. Checking status..."
sleep 10
docker-compose ps
docker-compose logs doc-converter | head -20

echo "✅ Emergency rebuild complete!"
echo "If you still see startup.sh logs, there's a deeper Docker cache issue on your system."