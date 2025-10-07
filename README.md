# Document Processing Service

A production-ready Flask microservice that converts various document formats (PDF, DOCX, XLSX, PPTX, TXT, RTF) to plain text JSON. Features reliable document processing using stable libraries instead of textract, with Celery for async processing and Redis for task queue management.

## ✨ Features

- **Multiple Document Formats**: PDF, DOCX, XLSX, PPTX, TXT, RTF
- **Reliable Processing**: Uses PyMuPDF, pdfplumber, python-docx, openpyxl, python-pptx instead of problematic textract
- **Async & Sync Processing**: Choose between immediate or background processing
- **Production Ready**: Multi-stage Docker builds, health checks, non-root security
- **API Key Authentication**: Secure endpoint access
- **Comprehensive Monitoring**: Health, metrics, and status endpoints

## 🚀 Quick Start

```bash
# Start all services
docker-compose up -d

# Check health
curl http://localhost:5001/health

# List supported formats
curl http://localhost:5001/formats

# Test document conversion
python test_service.py --file your_document.pdf --api-key default_dev_key
```

## 📋 API Endpoints

### Health Check
```bash
GET /health
# No authentication required
curl http://localhost:5001/health
```

### Supported Formats
```bash
GET /formats  
# No authentication required
curl http://localhost:5001/formats
```

### Convert Document (Sync)
```bash
POST /convert
curl -X POST \
  -H "X-API-Key: default_dev_key" \
  -F "file=@document.pdf" \
  http://localhost:5001/convert
```

### Convert Document (Async)
```bash
POST /convert?async=true
curl -X POST \
  -H "X-API-Key: default_dev_key" \
  -F "file=@document.pdf" \
  "http://localhost:5001/convert?async=true"
```

### Check Task Status
```bash
GET /task/{task_id}
curl -H "X-API-Key: default_dev_key" \
  http://localhost:5001/task/your-task-id
```

### Manual Cleanup
```bash
POST /cleanup
curl -X POST \
  -H "X-API-Key: default_dev_key" \
  http://localhost:5001/cleanup
```

## 🔧 Configuration

Set environment variables in docker-compose.yml:

- `API_KEY`: Authentication key (default: `default_dev_key`)
- `MAX_CONTENT_LENGTH`: Max file size in bytes (default: 50MB)
- `CELERY_BROKER_URL`: Redis connection for Celery
- `CELERY_RESULT_BACKEND`: Redis backend for results

## 🧪 Testing

```bash
# Run comprehensive tests
python test_service.py

# Test with custom file
python test_service.py --file path/to/document.pdf

# Test async processing
python test_service.py --async-mode

# Test cleanup
python test_service.py --cleanup
```

## 📊 Supported Document Formats

- **PDF**: `.pdf` (PyMuPDF + pdfplumber)
- **Word**: `.docx`, `.doc` (python-docx)
- **Excel**: `.xlsx`, `.xls` (openpyxl + xlrd)
- **PowerPoint**: `.pptx` (python-pptx)
- **Text**: `.txt`, `.rtf` (chardet encoding detection)

## 🔄 Docker Architecture

The service uses a distributed architecture with four main components:

1. **Flask API Server** (`doc-converter`) - Main REST API
2. **Celery Workers** (`celery-worker`) - Async document processing
3. **Celery Beat** (`celery-beat`) - Scheduled cleanup tasks
4. **Redis** (`redis`) - Message broker and result backend

## 🛡️ Production Features

- **Multi-stage Docker builds** for optimized image size
- **Non-root user execution** for security
- **Health checks** for all services
- **Resource limits** to prevent resource exhaustion
- **Circuit breaker protection** for processing failures
- **Automatic cleanup** of temporary files
- **Graceful shutdown** handling

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs

# Rebuild if needed
docker-compose build --no-cache
docker-compose up -d
```

### File Upload Issues
- Ensure form field name is `file` (not `document`)
- Include `X-API-Key` header
- Check file size is under 50MB limit
- Verify file format is supported via `/formats` endpoint

### Performance Issues
- Use async processing for large files
- Monitor `/health` endpoint for service status
- Check Redis connection via health endpoint

## 📝 Response Format

### Successful Conversion
```json
{
  "text": "Extracted document text...",
  "metadata": {
    "file_type": "pdf",
    "file_size": 1024768,
    "text_length": 5432,
    "extractor": "reliable_extractor"
  },
  "status": "completed"
}
```

### Error Response
```json
{
  "error": "No file provided",
  "status": "failed"
}
```
## PDF Raster Image Detection

The service now includes a specialized endpoint for detecting raster image content in PDF files.

### Endpoint: `/detect-raster`

**Method**: POST  
**Authentication**: Requires `X-API-Key` header  
**Content-Type**: multipart/form-data

#### Request Parameters

- **file** (required): PDF file to analyze
- **min_width** (optional): Minimum image width in pixels (default: 100)
- **min_height** (optional): Minimum image height in pixels (default: 100)
- **max_width** (optional): Maximum image width in pixels (default: 5000)
- **max_height** (optional): Maximum image height in pixels (default: 5000)
- **check_image_ratio** (optional): Check if images dominate page area (default: true)
- **ratio_threshold** (optional): Page area ratio threshold (default: 0.5)
- **include_metadata** (optional): Return detailed image metadata (default: false)
- **timeout** (optional): Processing timeout in seconds (default: 30)

#### Example Request

```bash
curl -X POST http://localhost:5000/detect-raster \
  -H "X-API-Key: your_api_key" \
  -F "file=@document.pdf" \
  -F "min_width=50" \
  -F "min_height=50" \
  -F "ratio_threshold=0.3" \
  -F "include_metadata=true"
```

#### Response Format

```json
{
  "status": "completed",
  "result": {
    "has_raster_images": true,
    "image_count": 3,
    "pages_with_images": [1, 2, 3],
    "total_pages": 5,
    "analysis": {
      "total_images": 3,
      "pages_dominated_by_images": 2,
      "average_image_size": "800x600",
      "largest_image": "1200x900",
      "smallest_image": "400x300",
      "image_formats": ["rgb", "grayscale"],
      "total_image_area": 2400000
    },
    "detailed_images": [
      {
        "page": 1,
        "index": 0,
        "width": 800,
        "height": 600,
        "area": 480000,
        "dpi": 150,
        "color_space": "RGB",
        "format": "rgb",
        "bbox": {
          "x0": 50,
          "y0": 100,
          "x1": 450,
          "y1": 400
        }
      }
    ],
    "settings_used": {
      "min_image_size": [50, 50],
      "max_image_size": [5000, 5000],
      "check_image_ratio": true,
      "ratio_threshold": 0.3,
      "include_metadata": true,
      "timeout_seconds": 30
    }
  },
  "timestamp": "2025-01-15T10:30:00.000Z"
}
```

### Configuration

The raster detection feature can be configured using environment variables:

- **RASTER_DETECTION_ENABLED**: Enable/disable feature (default: true)
- **DEFAULT_MIN_IMAGE_SIZE**: Default minimum image size as "width,height" (default: "100,100")
- **DEFAULT_MAX_IMAGE_SIZE**: Default maximum image size as "width,height" (default: "5000,5000")
- **DEFAULT_RATIO_THRESHOLD**: Default page coverage threshold (default: 0.5)

### Use Cases

- **Document Quality Assessment**: Detect if PDFs contain scanned images instead of text
- **Content Analysis**: Determine if documents are image-heavy or text-based
- **Processing Optimization**: Route image-heavy PDFs to OCR pipelines
- **Storage Optimization**: Identify PDFs that could benefit from compression
- **Compliance Checking**: Ensure documents meet image content requirements

### Testing

Run the raster detection tests:

```bash
python test_raster_detection.py
```

The test suite includes:
- Endpoint validation tests
- Parameter validation tests
- Error handling tests
- Configuration tests
- Module unit tests
