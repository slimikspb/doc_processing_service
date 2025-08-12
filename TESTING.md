# Testing Multiple Document Formats

This document describes the comprehensive testing setup for various document formats supported by the Document Converter Service.

## Test Files Created

The following test files have been created in the `test_files/` directory:

| Format | File | Size | Description |
|--------|------|------|-------------|
| **DOCX** | test.docx | 36KB | Microsoft Word document with headings, paragraphs, and formatted content |
| **PDF** | test.pdf | 1.6KB | PDF document with multiple text lines |
| **XML** | test.xml | 798B | Structured XML with document metadata, sections, and content |
| **PPTX** | test.pptx | 29KB | PowerPoint presentation with title slide and bullet points |
| **XLSX** | test.xlsx | 5.6KB | Excel spreadsheet with multiple sheets, headers, and data |
| **CSV** | test.csv | 456B | Comma-separated values with employee data |
| **TXT** | test.txt | 350B | Plain text file with basic content |

## Test Scripts

### 1. Multi-Format Test Script

**File:** `test_multiple_formats.py`

A comprehensive testing script that validates document conversion for all supported formats.

**Features:**
- Tests all document formats in both sync and async modes
- Validates extracted content for format-specific elements
- Measures processing times and generates detailed reports
- Color-coded console output with progress tracking
- JSON export of test results

**Usage:**

```bash
# Test all formats (sync mode)
python test_multiple_formats.py

# Test with async processing
python test_multiple_formats.py --async

# Test specific formats only
python test_multiple_formats.py --formats docx pdf csv

# Verbose output with text previews
python test_multiple_formats.py --verbose

# Save results to JSON
python test_multiple_formats.py --output results.json

# Test with custom API key and URL
python test_multiple_formats.py --api-key your_key --url http://localhost:8080
```

### 2. Basic Service Test

**File:** `test_service.py`

Simple test script for basic functionality validation.

```bash
# Basic health check
python test_service.py

# Test with a specific file
python test_service.py --file test_files/test.docx

# Test async mode
python test_service.py --file test_files/test.pdf --async-mode
```

## Expected Test Results

When the service is running, you should see output like:

```
======================================================================
          Document Converter Service - Multi-Format Test Suite
======================================================================

API URL:    http://localhost:5001
API Key:    defau...v_key
Test Mode:  Synchronous

Checking service health... ✓ Service is healthy

======================================================================
              Testing 7 Document Formats (Sync Mode)
======================================================================
Testing Text File           ✓ PASSED (0.12s) - Valid response with 247 characters
Testing CSV File            ✓ PASSED (0.08s) - Valid response with 456 characters
Testing XML Document        ✓ PASSED (0.15s) - Valid response with 651 characters
Testing Microsoft Word     ✓ PASSED (1.23s) - Valid response with 1,234 characters
Testing PDF Document        ✓ PASSED (0.89s) - Valid response with 89 characters
Testing PowerPoint          ✓ PASSED (2.14s) - Valid response with 567 characters
Testing Excel Spreadsheet  ✓ PASSED (1.67s) - Valid response with 234 characters

======================================================================
                              Test Summary
======================================================================

Total Formats:  7
Passed:         7
Failed:         0
Skipped:        0
Pass Rate:      100.0%

Processing Times:
  Average: 1.05s
  Min:     0.08s
  Max:     2.14s
```

## Content Validation

The test script validates that extracted text contains expected content:

| Format | Validation Checks |
|--------|------------------|
| **XML** | "Test XML Document" or "Test Author" |
| **CSV** | "John Doe" or "Engineering" |
| **TXT** | "Test Text Document" |
| **DOCX** | "Test Document" or similar |
| **PDF** | "Test PDF Document" or similar |
| **PPTX** | "Test Presentation" or "Test Slide" |
| **XLSX** | "Column A" or "Row 1" or "Test Sheet" |

## Running the Full Test Suite

1. **Start the service:**
   ```bash
   docker-compose up -d
   ```

2. **Wait for services to be ready:**
   ```bash
   docker-compose logs -f
   # Wait for "Booting worker" messages from celery
   ```

3. **Run the comprehensive tests:**
   ```bash
   # All formats, sync mode
   python test_multiple_formats.py
   
   # All formats, async mode  
   python test_multiple_formats.py --async
   
   # Specific formats with verbose output
   python test_multiple_formats.py --formats docx pdf xlsx --verbose
   ```

## Troubleshooting

**Service not responding:**
- Check if Docker containers are running: `docker-compose ps`
- Check service logs: `docker-compose logs doc-converter`
- Verify port 5001 is not blocked: `curl http://localhost:5001/health`

**Test file not found errors:**
- Ensure test files exist: `ls -la test_files/`
- Recreate test files: `python create_test_files.py`

**Content validation failures:**
- Check if textract extracted content correctly
- Use `--verbose` flag to see extracted text previews
- Verify document content is not corrupted

**Network/timeout errors:**
- Increase timeout values in the test script
- Test with smaller files first
- Check Docker container resource limits

## Creating Additional Test Files

To add more test files or recreate existing ones:

```bash
# Install required libraries
pip install python-docx reportlab python-pptx openpyxl

# Run test file generator
python create_test_files.py
```

The generator will create sample files with test content and report which formats were successfully created.

## Integration with CI/CD

The test script returns appropriate exit codes:
- `0`: All tests passed
- `1`: One or more tests failed

Example integration:

```yaml
# GitHub Actions example
- name: Test document conversion
  run: |
    docker-compose up -d
    sleep 10  # Wait for services
    python test_multiple_formats.py --output test-results.json
  
- name: Upload test results
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: test-results
    path: test-results.json
```