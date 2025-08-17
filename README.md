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