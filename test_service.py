import requests
import sys
import os
import argparse

def test_health(api_key=None):
    """Test the health endpoint"""
    try:
        # Health endpoint doesn't require API key, but we'll include headers for consistency
        headers = {}
        if api_key:
            headers['X-API-Key'] = api_key
            
        response = requests.get('http://localhost:5001/health', headers=headers)
        print(f"Health check status code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing health endpoint: {str(e)}")
        return False

def test_convert(file_path, api_key, async_mode=False):
    """Test the convert endpoint with a document file"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    try:
        # Set up headers with API key
        headers = {'X-API-Key': api_key}
        
        # Prepare URL with async parameter if needed
        url = 'http://localhost:5001/convert'
        if async_mode:
            url += '?async=true'
            print("Testing in asynchronous mode")
        
        # Send the request
        with open(file_path, 'rb') as f:
            files = {'document': f}
            response = requests.post(url, headers=headers, files=files)
        
        print(f"Convert endpoint status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result}")
            
            # If async mode, check task status
            if async_mode and 'task_id' in result:
                print("Checking task status...")
                task_id = result['task_id']
                return test_task_status(task_id, api_key)
            
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error testing convert endpoint: {str(e)}")
        return False

def test_task_status(task_id, api_key):
    """Test the task status endpoint"""
    try:
        headers = {'X-API-Key': api_key}
        url = f'http://localhost:5001/task/{task_id}'
        
        # Poll for task completion (max 10 attempts)
        for attempt in range(1, 11):
            print(f"Polling attempt {attempt}/10...")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print(f"Task status: {result.get('status', 'unknown')}")
                
                if result.get('status') == 'completed':
                    print(f"Task completed successfully: {result}")
                    return True
                elif result.get('status') == 'failed':
                    print(f"Task failed: {result}")
                    return False
                
                # Wait before next poll
                import time
                time.sleep(1)
            else:
                print(f"Error checking task status: {response.text}")
                return False
        
        print("Task did not complete within the polling time")
        return False
    except Exception as e:
        print(f"Error checking task status: {str(e)}")
        return False

if __name__ == '__main__':
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Test document processing service API')
    parser.add_argument('--file', '-f', help='Path to document file for testing')
    parser.add_argument('--api-key', '-k', default=os.environ.get('API_KEY', 'default_dev_key'),
                        help='API key for authentication (default: from API_KEY env var)')
    parser.add_argument('--async-mode', '-a', action='store_true', dest='async_mode', help='Test asynchronous processing')
    parser.add_argument('--cleanup', '-c', action='store_true', help='Test cleanup endpoint')
    
    args = parser.parse_args()
    
    print("Testing document processing service...\n")
    print(f"Using API key: {args.api_key[:5]}...{args.api_key[-5:]}\n")
    
    # Test health endpoint
    print("1. Testing health endpoint...")
    health_ok = test_health(args.api_key)
    print(f"Health endpoint test {'PASSED' if health_ok else 'FAILED'}\n")
    
    # Test convert endpoint if a file path is provided
    if args.file:
        file_path = args.file
        print(f"2. Testing convert endpoint with file: {file_path}")
        convert_ok = test_convert(file_path, args.api_key, args.async_mode)
        print(f"Convert endpoint test {'PASSED' if convert_ok else 'FAILED'}\n")
    else:
        print("2. Skipping convert endpoint test (no file provided)")
        print("   To test the convert endpoint, run: python test_service.py --file path/to/document.docx\n")
        convert_ok = None
    
    # Test cleanup endpoint if requested
    if args.cleanup:
        print("3. Testing cleanup endpoint...")
        try:
            headers = {'X-API-Key': args.api_key}
            response = requests.post('http://localhost:5001/cleanup', headers=headers)
            if response.status_code == 200:
                result = response.json()
                print(f"Cleanup task started: {result}")
                if 'task_id' in result:
                    cleanup_ok = test_task_status(result['task_id'], args.api_key)
                    print(f"Cleanup endpoint test {'PASSED' if cleanup_ok else 'FAILED'}\n")
                else:
                    cleanup_ok = True
                    print("Cleanup endpoint test PASSED\n")
            else:
                print(f"Error: {response.text}")
                cleanup_ok = False
                print("Cleanup endpoint test FAILED\n")
        except Exception as e:
            print(f"Error testing cleanup endpoint: {str(e)}")
            cleanup_ok = False
            print("Cleanup endpoint test FAILED\n")
    else:
        cleanup_ok = None
    
    print("Test summary:")
    print(f"- Health endpoint: {'OK' if health_ok else 'FAILED'}")
    if convert_ok is not None:
        print(f"- Convert endpoint: {'OK' if convert_ok else 'FAILED'}")
    if cleanup_ok is not None:
        print(f"- Cleanup endpoint: {'OK' if cleanup_ok else 'FAILED'}")
