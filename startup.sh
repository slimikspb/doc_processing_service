#!/bin/bash
# Comprehensive startup script for full-featured document processing service

set -e

echo "🚀 Starting Full-Featured Document Processing Service"
echo "=================================================="

# Function to wait for Redis
wait_for_redis() {
    echo "⏳ Waiting for Redis to be ready..."
    timeout 30 bash -c 'until echo > /dev/tcp/redis/6379; do sleep 1; done'
    echo "✅ Redis is ready"
}

# Function to verify Python dependencies
verify_dependencies() {
    echo "🔍 Verifying Python dependencies..."
    
    # Test core dependencies
    python -c "import flask, celery, redis, textract; print('✅ Core dependencies OK')"
    
    # Test Office processing dependencies
    if python -c "import openpyxl, xlrd, pandas; from pptx import Presentation; print('✅ Office dependencies OK')" 2>/dev/null; then
        echo "✅ Office processing fully available"
        export OFFICE_SUPPORT=true
    else
        echo "⚠️  Office dependencies not available - will use fallback mode"
        export OFFICE_SUPPORT=false
    fi
    
    # Test enhanced modules
    if python -c "import sys; sys.path.append('/app'); from redis_manager import redis_manager; print('✅ Enhanced modules OK')" 2>/dev/null; then
        echo "✅ Enhanced features available"
        export ENHANCED_FEATURES=true
    else
        echo "⚠️  Enhanced features not available - will use basic mode"
        export ENHANCED_FEATURES=false
    fi
}

# Function to initialize the application
initialize_app() {
    echo "🔧 Initializing application..."
    
    # Set Python path
    export PYTHONPATH="/app:$PYTHONPATH"
    
    # Test app import
    if python -c "import app_full; print('✅ Application imports successfully')"; then
        echo "✅ Application ready to start"
    else
        echo "❌ Application import failed"
        exit 1
    fi
}

# Main startup sequence
main() {
    echo "Starting at $(date)"
    
    # Wait for Redis if this is a worker/beat service
    if [[ "$1" == *"celery"* ]]; then
        wait_for_redis
    fi
    
    # Verify dependencies
    verify_dependencies
    
    # Initialize application
    initialize_app
    
    echo "✅ Startup checks completed successfully"
    echo "🚀 Starting service: $*"
    echo "=================================================="
    
    # Execute the actual command
    exec "$@"
}

# Run main function with all arguments
main "$@"