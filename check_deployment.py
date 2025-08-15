#!/usr/bin/env python3
"""
Deployment validation script to check if services are running correctly
"""
import requests
import time
import sys

def check_service_health(base_url="http://localhost:5001", timeout=30):
    """Check if the service is healthy and responding"""
    print(f"🔍 Checking service health at {base_url}")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Basic health check
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Basic health check: PASSED")
                break
            else:
                print(f"⚠️  Health check returned: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"⏳ Service not ready yet: {e}")
            time.sleep(2)
            continue
    else:
        print("❌ Service failed to become healthy within timeout")
        return False
    
    # Check supported formats
    try:
        response = requests.get(f"{base_url}/formats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            total_formats = data.get('total_supported', 0)
            office_formats = data.get('office_documents', {}).get('formats', [])
            print(f"✅ Supported formats: {total_formats} total")
            if office_formats:
                print(f"✅ Office support: {office_formats}")
            else:
                print("⚠️  Office support: Not available (fallback mode)")
        else:
            print(f"⚠️  Formats endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not check formats: {e}")
    
    return True

def check_task_registration():
    """Check if Celery tasks are properly registered"""
    print("\n🔍 Checking Celery task registration...")
    
    # This would require access to Docker logs, so we'll provide instructions
    print("To check Celery task registration:")
    print("1. Run: docker-compose logs celery-worker | grep 'tasks'")
    print("2. Look for: app.cleanup_temp_files and app.process_document")
    print("3. Should NOT see: 'Received unregistered task' errors")

def check_security():
    """Check if security warnings are resolved"""
    print("\n🔍 Checking security configuration...")
    print("To verify non-root user:")
    print("1. Run: docker-compose logs celery-worker | grep 'superuser'")
    print("2. Should NOT see: 'running the worker with superuser privileges' warning")

def main():
    print("🚀 Document Processing Service Deployment Validation")
    print("=" * 55)
    
    # Wait a moment for services to start
    print("⏳ Waiting 10 seconds for services to initialize...")
    time.sleep(10)
    
    # Check service health
    service_healthy = check_service_health()
    
    # Provide manual check instructions
    check_task_registration()
    check_security()
    
    print("\n" + "=" * 55)
    if service_healthy:
        print("✅ Deployment validation: PASSED")
        print("\n📋 Next steps:")
        print("1. Check container health in Docker UI (should show 'healthy')")
        print("2. Run full tests: python test_enhanced_service.py")
        print("3. Test Office docs: python test_office_documents.py")
    else:
        print("❌ Deployment validation: FAILED")
        print("\n🔧 Troubleshooting:")
        print("1. Check logs: docker-compose logs")
        print("2. Rebuild: docker-compose build && docker-compose up -d")
        print("3. Check if ports are available: netstat -tulpn | grep 5001")
    
    return 0 if service_healthy else 1

if __name__ == '__main__':
    sys.exit(main())