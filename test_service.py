#!/usr/bin/env python3
"""
Test script for the document processing service.
"""

import requests
import json
import time
import argparse
import sys
from pathlib import Path

# Service configuration
BASE_URL = "http://localhost:5001"
API_KEY = "default_dev_key"

def test_health():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {data.get('status')}")
            print(f"   Document processing: {data.get('document_processing')}")
            print(f"   Supported formats: {data.get('supported_formats', [])}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_formats():
    """Test formats endpoint."""
    print("\n🔍 Testing formats endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/formats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Formats endpoint working")
            print(f"   Supported: {data.get('supported_formats', [])}")
            return True
        else:
            print(f"❌ Formats endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Formats endpoint error: {e}")
        return False

def create_test_file(file_type="txt"):
    """Create a test file for testing."""
    test_content = """
    This is a test document for the document processing service.
    
    It contains multiple paragraphs to test text extraction.
    
    The service should be able to extract this text successfully.
    """
    
    test_file = Path(f"test_document.{file_type}")
    
    if file_type == "txt":
        with open(test_file, 'w') as f:
            f.write(test_content)
    else:
        print(f"⚠️  Cannot create {file_type} file programmatically, using txt instead")
        test_file = Path("test_document.txt")
        with open(test_file, 'w') as f:
            f.write(test_content)
    
    return test_file

def test_document_conversion(file_path=None, async_mode=False, ocr_enabled=False):
    """Test document conversion."""
    print(f"\n🔍 Testing document conversion (async={async_mode}, ocr={ocr_enabled})...")
    
    # Create test file if none provided
    if not file_path:
        file_path = create_test_file()
        cleanup_file = True
    else:
        cleanup_file = False
    
    try:
        if not Path(file_path).exists():
            print(f"❌ Test file not found: {file_path}")
            return False
        
        headers = {"X-API-Key": API_KEY}
        
        with open(file_path, 'rb') as f:
            files = {"file": f}
            params = {
                "async": "true" if async_mode else "false",
                "ocr": "true" if ocr_enabled else "false"
            }
            
            response = requests.post(
                f"{BASE_URL}/convert",
                files=files,
                headers=headers,
                params=params
            )
        
        if response.status_code == 200:
            data = response.json()
            
            if async_mode:
                task_id = data.get('task_id')
                print(f"✅ Async conversion started, task ID: {task_id}")
                
                # Poll for result
                print("   Waiting for result...")
                for attempt in range(30):  # Wait up to 30 seconds
                    time.sleep(1)
                    status_response = requests.get(
                        f"{BASE_URL}/task/{task_id}",
                        headers=headers
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        
                        if status == 'completed':
                            print(f"✅ Async conversion completed")
                            print(f"   Text length: {len(status_data.get('text', ''))}")
                            return True
                        elif status == 'failed':
                            print(f"❌ Async conversion failed: {status_data.get('error')}")
                            return False
                        else:
                            print(f"   Status: {status}")
                
                print("❌ Async conversion timed out")
                return False
            else:
                print(f"✅ Sync conversion completed")
                print(f"   Text length: {len(data.get('text', ''))}")
                print(f"   Status: {data.get('status')}")
                
                # Check for OCR enrichment if enabled
                if ocr_enabled:
                    text = data.get('text', '')
                    if 'OCR TEXT FROM IMAGES' in text:
                        print(f"   ✅ OCR enrichment detected in output")
                    else:
                        print(f"   ⚠️  OCR enabled but no OCR text found (might be no images)")
                
                return True
        else:
            print(f"❌ Conversion failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Conversion error: {e}")
        return False
    
    finally:
        # Cleanup test file if we created it
        if cleanup_file and Path(file_path).exists():
            try:
                Path(file_path).unlink()
            except:
                pass

def test_cleanup():
    """Test manual cleanup endpoint."""
    print("\n🔍 Testing cleanup endpoint...")
    try:
        headers = {"X-API-Key": API_KEY}
        response = requests.post(f"{BASE_URL}/cleanup", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cleanup triggered successfully")
            print(f"   Task ID: {data.get('task_id')}")
            return True
        else:
            print(f"❌ Cleanup failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        return False

def main():
    global API_KEY
    
    parser = argparse.ArgumentParser(description="Test document processing service")
    parser.add_argument("--file", help="Path to test file")
    parser.add_argument("--async-mode", action="store_true", help="Test async processing")
    parser.add_argument("--ocr", action="store_true", help="Test OCR processing")
    parser.add_argument("--cleanup", action="store_true", help="Test cleanup endpoint")
    parser.add_argument("--api-key", default=API_KEY, help="API key to use")
    
    args = parser.parse_args()
    
    API_KEY = args.api_key
    
    print("🚀 Testing Document Processing Service")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Basic health and formats tests
    if not test_health():
        all_tests_passed = False
    
    if not test_formats():
        all_tests_passed = False
    
    # Document conversion tests
    if args.file or not args.cleanup:
        if not test_document_conversion(args.file, async_mode=False, ocr_enabled=args.ocr):
            all_tests_passed = False
        
        if args.async_mode:
            if not test_document_conversion(args.file, async_mode=True, ocr_enabled=args.ocr):
                all_tests_passed = False
    
    # Cleanup test
    if args.cleanup:
        if not test_cleanup():
            all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()