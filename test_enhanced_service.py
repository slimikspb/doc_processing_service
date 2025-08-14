#!/usr/bin/env python3
"""
Enhanced test script for the document processing service with monitoring and health checks
"""
import requests
import argparse
import json
import time
import sys
from pathlib import Path

def test_health_endpoint(base_url, api_key=None):
    """Test the basic health endpoint"""
    print("Testing basic health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✓ Basic health check passed")
            return True
        else:
            print(f"✗ Basic health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Basic health check error: {e}")
        return False

def test_detailed_health(base_url, api_key):
    """Test the detailed health endpoint"""
    print("Testing detailed health endpoint...")
    try:
        headers = {'X-API-Key': api_key} if api_key else {}
        response = requests.get(f"{base_url}/health/detailed", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Detailed health check passed")
            print(f"  Overall status: {data.get('status', 'unknown')}")
            
            components = data.get('components', {})
            for component, status in components.items():
                health_status = "✓" if status.get('healthy', False) else "✗"
                print(f"  {health_status} {component}: {status.get('data', status.get('error', 'unknown'))}")
            
            return True
        else:
            print(f"✗ Detailed health check failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Detailed health check error: {e}")
        return False

def test_metrics_endpoint(base_url, api_key):
    """Test the metrics endpoint"""
    print("Testing metrics endpoint...")
    try:
        headers = {'X-API-Key': api_key} if api_key else {}
        response = requests.get(f"{base_url}/metrics", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Metrics endpoint passed")
            
            # Display key metrics
            system = data.get('system', {})
            service = data.get('service', {})
            
            print(f"  CPU: {system.get('cpu_percent', 0)}%")
            print(f"  Memory: {system.get('memory_percent', 0)}%")
            print(f"  Disk: {system.get('disk_usage_percent', 0)}%")
            print(f"  Uptime: {service.get('uptime_seconds', 0)}s")
            print(f"  Total requests: {service.get('total_requests', 0)}")
            print(f"  Temp files: {service.get('temp_files_count', 0)} ({service.get('temp_files_size_mb', 0)}MB)")
            
            # Circuit breaker status
            cb = data.get('circuit_breaker', {})
            if 'state' in cb:
                print(f"  Circuit breaker: {cb['state']} (failures: {cb.get('failure_count', 0)})")
            
            return True
        else:
            print(f"✗ Metrics endpoint failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Metrics endpoint error: {e}")
        return False

def test_status_endpoint(base_url, api_key):
    """Test the status endpoint"""
    print("Testing status endpoint...")
    try:
        headers = {'X-API-Key': api_key} if api_key else {}
        response = requests.get(f"{base_url}/status", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Status endpoint passed")
            print(f"  Service: {data.get('service', 'unknown')}")
            print(f"  Status: {data.get('status', 'unknown')}")
            print(f"  Active requests: {data.get('active_requests', 0)}")
            return True
        else:
            print(f"✗ Status endpoint failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Status endpoint error: {e}")
        return False

def test_document_conversion(base_url, api_key, test_file=None):
    """Test document conversion with circuit breaker"""
    print("Testing document conversion...")
    
    # Create a test file if none provided
    if not test_file:
        test_file = "test_doc.txt"
        with open(test_file, 'w') as f:
            f.write("This is a test document for conversion testing.")
    
    try:
        headers = {'X-API-Key': api_key} if api_key else {}
        
        with open(test_file, 'rb') as f:
            files = {'document': f}
            response = requests.post(f"{base_url}/convert", 
                                   headers=headers, 
                                   files=files, 
                                   timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Document conversion passed")
            print(f"  Filename: {data.get('filename', 'unknown')}")
            print(f"  Status: {data.get('status', 'unknown')}")
            print(f"  Text length: {len(data.get('text', ''))}")
            return True
        elif response.status_code == 503:
            print("⚠ Document conversion failed (service unavailable - circuit breaker may be open)")
            return False
        else:
            print(f"✗ Document conversion failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Document conversion error: {e}")
        return False
    finally:
        # Clean up test file if we created it
        if test_file == "test_doc.txt":
            try:
                Path(test_file).unlink()
            except:
                pass

def test_circuit_breaker_behavior(base_url, api_key):
    """Test circuit breaker behavior by triggering failures"""
    print("Testing circuit breaker behavior...")
    
    headers = {'X-API-Key': api_key} if api_key else {}
    
    # Create an invalid file that should cause textract to fail
    bad_file = "bad_test_file.fake"
    with open(bad_file, 'wb') as f:
        f.write(b"This is not a real document format that textract can handle")
    
    failures = 0
    try:
        # Try to trigger failures to open the circuit breaker
        for i in range(5):
            print(f"  Attempt {i+1}/5 - sending bad file...")
            
            with open(bad_file, 'rb') as f:
                files = {'document': f}
                response = requests.post(f"{base_url}/convert", 
                                       headers=headers, 
                                       files=files, 
                                       timeout=30)
            
            if response.status_code in [500, 503]:
                failures += 1
                print(f"    Expected failure: {response.status_code}")
            else:
                print(f"    Unexpected response: {response.status_code}")
            
            time.sleep(1)  # Brief delay between requests
        
        print(f"✓ Circuit breaker test completed ({failures}/5 failures)")
        return True
        
    except Exception as e:
        print(f"✗ Circuit breaker test error: {e}")
        return False
    finally:
        # Clean up test file
        try:
            Path(bad_file).unlink()
        except:
            pass

def run_all_tests(base_url, api_key, test_file=None):
    """Run all enhanced tests"""
    print(f"Running enhanced tests against {base_url}")
    print("=" * 50)
    
    results = []
    
    # Basic tests
    results.append(test_health_endpoint(base_url, api_key))
    results.append(test_status_endpoint(base_url, api_key))
    
    # Enhanced monitoring tests
    results.append(test_detailed_health(base_url, api_key))
    results.append(test_metrics_endpoint(base_url, api_key))
    
    # Functionality tests
    results.append(test_document_conversion(base_url, api_key, test_file))
    
    # Advanced tests
    results.append(test_circuit_breaker_behavior(base_url, api_key))
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠ Some tests failed")
        return False

def main():
    parser = argparse.ArgumentParser(description='Enhanced test suite for document processing service')
    parser.add_argument('--url', default='http://localhost:5001', 
                       help='Base URL of the service (default: http://localhost:5001)')
    parser.add_argument('--api-key', default='default_dev_key',
                       help='API key for authentication (default: default_dev_key)')
    parser.add_argument('--file', help='Test file to upload')
    parser.add_argument('--test', choices=['health', 'detailed-health', 'metrics', 'status', 'convert', 'circuit-breaker', 'all'],
                       default='all', help='Specific test to run')
    
    args = parser.parse_args()
    
    if args.test == 'health':
        success = test_health_endpoint(args.url, args.api_key)
    elif args.test == 'detailed-health':
        success = test_detailed_health(args.url, args.api_key)
    elif args.test == 'metrics':
        success = test_metrics_endpoint(args.url, args.api_key)
    elif args.test == 'status':
        success = test_status_endpoint(args.url, args.api_key)
    elif args.test == 'convert':
        success = test_document_conversion(args.url, args.api_key, args.file)
    elif args.test == 'circuit-breaker':
        success = test_circuit_breaker_behavior(args.url, args.api_key)
    else:  # all
        success = run_all_tests(args.url, args.api_key, args.file)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()