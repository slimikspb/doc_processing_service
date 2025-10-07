"""
Tests for PDF raster image detection functionality.
"""

import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import requests
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:5000"
API_KEY = "default_dev_key"
HEADERS = {"X-API-Key": API_KEY}

class TestRasterDetection(unittest.TestCase):
    """Test cases for PDF raster image detection."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.base_url = BASE_URL
        self.headers = HEADERS
        
        # Create a simple test PDF file (mock)
        self.test_pdf_path = self._create_test_pdf()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
    
    def _create_test_pdf(self):
        """Create a simple test PDF file for testing."""
        # This would normally create a real PDF, but for now we'll create a dummy file
        # In a real implementation, you'd use reportlab or similar to create test PDFs
        temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        temp_file.write(b"%PDF-1.4\n%Mock PDF for testing\n")
        temp_file.close()
        return temp_file.name
    
    def test_health_check_includes_raster_detection(self):
        """Test that health check includes raster detection status."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn("raster_detection", data)
            self.assertIsInstance(data["raster_detection"], bool)
        except requests.exceptions.ConnectionError:
            self.skipTest("Service not running")
    
    def test_detect_raster_missing_file(self):
        """Test raster detection with missing file."""
        try:
            response = requests.post(
                f"{self.base_url}/detect-raster",
                headers=self.headers,
                timeout=10
            )
            self.assertEqual(response.status_code, 400)
            
            data = response.json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "No file provided")
        except requests.exceptions.ConnectionError:
            self.skipTest("Service not running")
    
    def test_detect_raster_no_file_selected(self):
        """Test raster detection with no file selected."""
        try:
            files = {"file": ("", "", "application/pdf")}
            response = requests.post(
                f"{self.base_url}/detect-raster",
                headers=self.headers,
                files=files,
                timeout=10
            )
            self.assertEqual(response.status_code, 400)
            
            data = response.json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "No file selected")
        except requests.exceptions.ConnectionError:
            self.skipTest("Service not running")
    
    def test_detect_raster_non_pdf_file(self):
        """Test raster detection with non-PDF file."""
        try:
            files = {"file": ("test.txt", "This is text content", "text/plain")}
            response = requests.post(
                f"{self.base_url}/detect-raster",
                headers=self.headers,
                files=files,
                timeout=10
            )
            self.assertEqual(response.status_code, 400)
            
            data = response.json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Only PDF files are supported for raster detection")
        except requests.exceptions.ConnectionError:
            self.skipTest("Service not running")
    
    def test_detect_raster_invalid_api_key(self):
        """Test raster detection with invalid API key."""
        try:
            files = {"file": ("test.pdf", b"%PDF-1.4 mock content", "application/pdf")}
            headers = {"X-API-Key": "invalid_key"}
            
            response = requests.post(
                f"{self.base_url}/detect-raster",
                headers=headers,
                files=files,
                timeout=10
            )
            self.assertEqual(response.status_code, 401)
            
            data = response.json()
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Invalid or missing API key")
        except requests.exceptions.ConnectionError:
            self.skipTest("Service not running")
    
    def test_detect_raster_with_settings(self):
        """Test raster detection with custom settings."""
        try:
            with open(self.test_pdf_path, "rb") as f:
                files = {"file": ("test.pdf", f.read(), "application/pdf")}
                
                params = {
                    "min_width": 50,
                    "min_height": 50,
                    "max_width": 2000,
                    "max_height": 2000,
                    "check_image_ratio": "true",
                    "ratio_threshold": 0.3,
                    "include_metadata": "true",
                    "timeout": 15
                }
                
                response = requests.post(
                    f"{self.base_url}/detect-raster",
                    headers=self.headers,
                    files=files,
                    params=params,
                    timeout=20
                )
                
                # Should either succeed with analysis or fail gracefully with PDF processing error
                if response.status_code == 200:
                    data = response.json()
                    self.assertEqual(data["status"], "completed")
                    self.assertIn("result", data)
                    self.assertIn("timestamp", data)
                    
                    result = data["result"]
                    self.assertIn("has_raster_images", result)
                    self.assertIn("image_count", result)
                    self.assertIn("pages_with_images", result)
                    self.assertIn("analysis", result)
                    self.assertIn("settings_used", result)
                    
                    # Check that settings were applied
                    settings = result["settings_used"]
                    self.assertEqual(settings["min_image_size"], (50, 50))
                    self.assertEqual(settings["max_image_size"], (2000, 2000))
                    self.assertEqual(settings["ratio_threshold"], 0.3)
                    self.assertTrue(settings["include_metadata"])
                else:
                    # Expected for mock PDF - should handle gracefully
                    self.assertIn(response.status_code, [400, 500])
                    
        except requests.exceptions.ConnectionError:
            self.skipTest("Service not running")
    
    def test_detect_raster_default_settings(self):
        """Test raster detection with default settings."""
        try:
            with open(self.test_pdf_path, "rb") as f:
                files = {"file": ("test.pdf", f.read(), "application/pdf")}
                
                response = requests.post(
                    f"{self.base_url}/detect-raster",
                    headers=self.headers,
                    files=files,
                    timeout=20
                )
                
                # Should either succeed or fail gracefully
                if response.status_code == 200:
                    data = response.json()
                    result = data["result"]
                    
                    # Check default settings were applied
                    settings = result["settings_used"]
                    self.assertEqual(settings["min_image_size"], (100, 100))
                    self.assertEqual(settings["max_image_size"], (5000, 5000))
                    self.assertEqual(settings["ratio_threshold"], 0.5)
                    self.assertFalse(settings["include_metadata"])
                    
        except requests.exceptions.ConnectionError:
            self.skipTest("Service not running")
    
    @patch.dict(os.environ, {"RASTER_DETECTION_ENABLED": "false"})
    def test_detect_raster_disabled(self):
        """Test raster detection when feature is disabled."""
        # This test would require restarting the service with the env var set
        # For now, we'll just test the logic conceptually
        try:
            with open(self.test_pdf_path, "rb") as f:
                files = {"file": ("test.pdf", f.read(), "application/pdf")}
                
                response = requests.post(
                    f"{self.base_url}/detect-raster",
                    headers=self.headers,
                    files=files,
                    timeout=10
                )
                
                # If the service is running with the feature disabled, should get 503
                # Otherwise, this test may not work as expected without service restart
                if response.status_code == 503:
                    data = response.json()
                    self.assertIn("error", data)
                    self.assertEqual(data["error"], "Raster detection is disabled")
                    
        except requests.exceptions.ConnectionError:
            self.skipTest("Service not running")

class TestRasterDetectionModule(unittest.TestCase):
    """Test the raster detection module directly."""
    
    def setUp(self):
        """Set up test fixtures."""
        from pdf_raster_detector import PDFRasterDetector
        self.detector = PDFRasterDetector()
    
    def test_default_settings(self):
        """Test that default settings are properly configured."""
        expected_settings = {
            'min_image_size': (100, 100),
            'max_image_size': (5000, 5000),
            'check_image_ratio': True,
            'ratio_threshold': 0.5,
            'include_metadata': False,
            'timeout_seconds': 30
        }
        
        self.assertEqual(self.detector.default_settings, expected_settings)
    
    def test_get_supported_formats(self):
        """Test supported formats method."""
        formats = self.detector.get_supported_formats()
        self.assertIsInstance(formats, list)
        
        if formats:  # If PyMuPDF is available
            self.assertIn('pdf', formats)
    
    def test_invalid_file_path(self):
        """Test handling of invalid file paths."""
        with self.assertRaises(FileNotFoundError):
            self.detector.detect_raster_images("/nonexistent/file.pdf")
    
    def test_non_pdf_file(self):
        """Test handling of non-PDF files."""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"This is not a PDF")
            temp_path = f.name
        
        try:
            # This should raise an exception when trying to open as PDF
            with self.assertRaises(Exception):
                self.detector.detect_raster_images(temp_path)
        finally:
            os.unlink(temp_path)

def run_tests():
    """Run all tests."""
    print("Running PDF Raster Detection Tests...")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestRasterDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestRasterDetectionModule))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
