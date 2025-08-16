#!/bin/bash

echo "🔍 Build Validation Script"
echo "========================="

# Exit on any error
set -e

# Function to print colored output
print_check() {
    echo -n "🔷 $1... "
}

print_success() {
    echo "✅"
}

print_error() {
    echo "❌ $1"
    exit 1
}

print_warning() {
    echo "⚠️ $1"
}

echo ""
echo "Checking required files for Docker build:"

# Check main application files
print_check "app_full.py"
[ -f "app_full.py" ] && print_success || print_error "Missing app_full.py"

print_check "requirements.txt"
[ -f "requirements.txt" ] && print_success || print_error "Missing requirements.txt"

print_check "Dockerfile"
[ -f "Dockerfile" ] && print_success || print_error "Missing Dockerfile"

print_check "docker-compose.yml"
[ -f "docker-compose.yml" ] && print_success || print_error "Missing docker-compose.yml"

# Check support modules
print_check "startup.sh"
[ -f "startup.sh" ] && print_success || print_error "Missing startup.sh"

print_check "simple_health_check.py"
[ -f "simple_health_check.py" ] && print_success || print_error "Missing simple_health_check.py"

# Check core modules
files_to_check=(
    "file_cleanup.py"
    "redis_manager.py" 
    "circuit_breaker.py"
    "graceful_shutdown.py"
    "monitoring.py"
    "health_checks.py"
    "office_processor.py"
    "document_extractor.py"
    "fallback_extractor.py"
)

for file in "${files_to_check[@]}"; do
    print_check "$file"
    [ -f "$file" ] && print_success || print_warning "Missing $file (optional)"
done

echo ""
echo "Checking Docker configuration:"

print_check "Docker compose syntax"
docker-compose config > /dev/null 2>&1 && print_success || print_error "docker-compose.yml has syntax errors"

print_check "Startup script is executable"
[ -x "startup.sh" ] && print_success || print_error "startup.sh is not executable"

echo ""
echo "Checking requirements.txt content:"

if [ -f "requirements.txt" ]; then
    echo "📋 Required packages:"
    cat requirements.txt | grep -E "^[a-zA-Z]" | sort
else
    print_error "requirements.txt not found"
fi

echo ""
echo "🔍 Checking for potential issues:"

# Check for volume mounts that might cache old code
if grep -q "app_code:/app" docker-compose.yml 2>/dev/null; then
    print_warning "Found app_code volume mount - this will cache old code!"
    echo "   Remove 'app_code:/app' from docker-compose.yml volumes"
else
    print_check "No problematic app_code volume mounts"
    print_success
fi

# Check if main containers use app_full
if grep -q "app_full" docker-compose.yml; then
    print_check "Services reference app_full"
    print_success
else
    print_warning "Services don't reference app_full - might use old app.py"
fi

echo ""
echo "✅ Build validation completed!"
echo ""
echo "Next steps:"
echo "1. Run: ./deploy_fresh.sh"
echo "2. Monitor: docker-compose logs -f"
echo "3. Check health: docker-compose ps"