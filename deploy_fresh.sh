#!/bin/bash

echo "🚀 Fresh Deployment Script - Ensuring New Code is Used"
echo "======================================================"

# Exit on any error
set -e

# Function to print colored output
print_status() {
    echo -e "\n🔷 $1"
}

print_success() {
    echo -e "✅ $1"
}

print_warning() {
    echo -e "⚠️ $1"
}

print_status "Step 1: Stopping all containers"
docker-compose down
print_success "Containers stopped"

print_status "Step 2: Removing old containers and images to prevent caching"
# Remove containers
docker-compose rm -f || true

# Remove dangling images
docker image prune -f || true

# Remove specific images related to this project
docker rmi $(docker images --filter "reference=*doc*" -q) 2>/dev/null || true
docker rmi $(docker images --filter "reference=*algiers*" -q) 2>/dev/null || true

print_success "Old containers and images removed"

print_status "Step 3: Building fresh images from scratch"
docker-compose build --no-cache --pull
print_success "Fresh images built"

print_status "Step 4: Starting services with new code"
docker-compose up -d
print_success "Services started"

print_status "Step 5: Waiting for services to initialize"
sleep 15

print_status "Step 6: Checking container health status"
echo ""
docker-compose ps

print_status "Step 7: Checking logs for any immediate issues"
echo ""
echo "=== Recent logs ==="
docker-compose logs --tail=20

print_status "Step 8: Running health checks"
echo ""

# Wait a bit more for health checks to complete
sleep 30

echo "=== Final Container Status ==="
docker-compose ps

echo ""
print_success "Deployment completed! Check the status above."
print_warning "If containers are still unhealthy, check logs with: docker-compose logs -f"

echo ""
echo "🔍 Quick debugging commands:"
echo "  docker-compose logs doc-converter"
echo "  docker-compose logs celery-worker" 
echo "  docker-compose logs celery-beat"
echo "  docker-compose logs redis"