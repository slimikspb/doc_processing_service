# Deployment Guide

This guide shows how to deploy the Document Processing Service using the standard configuration.

## Quick Deployment

```bash
# Clone and enter directory
git clone <repository-url>
cd doc_processing_service

# Start all services (pulls latest image from GitHub registry)
docker-compose up -d

# Check everything is running
docker-compose ps

# Test the service
python test_service.py

# Test with OCR
python test_service.py --file test.pdf --ocr
```

### Automatic Updates via Portainer

**Production servers with Portainer:**
- Portainer watches `ghcr.io/timur-nocodia/doc_processing_service:latest`
- On git push to main, GitHub Actions builds new image
- Portainer auto-pulls and recreates services
- **Zero manual intervention required**

## Production Deployment

### 1. Environment Configuration

Create a `.env` file:

```bash
# Security
API_KEY=your_secure_api_key_here

# Performance
MAX_CONTENT_LENGTH=52428800  # 50MB

# OCR Configuration
OCR_LANGUAGES=eng+rus  # English + Russian (default)
# OCR_LANGUAGES=eng+rus+deu  # Add German
# OCR_LANGUAGES=eng  # English only

# Redis (usually defaults are fine)
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 2. Deploy with Custom Configuration

```bash
# Build and start with environment file
docker-compose --env-file .env up -d

# Or set variables directly
API_KEY=prod_key MAX_CONTENT_LENGTH=104857600 docker-compose up -d
```

### 3. Health Check

```bash
# Basic health
curl http://localhost:5001/health

# Should return:
{
  "status": "healthy",
  "document_processing": true,
  "ocr_available": true,
  "ocr_languages": "eng+rus",
  "supported_formats": ["txt", "rtf", "pdf", "docx", "doc", "xlsx", "xls", "pptx"]
}
```

### 4. Test Document Processing

```bash
# Test with any document
curl -X POST \
  -H "X-API-Key: your_api_key" \
  -F "file=@test_document.pdf" \
  http://localhost:5001/convert

# Test with OCR enabled (extracts text from images in PDF)
curl -X POST \
  -H "X-API-Key: your_api_key" \
  -F "file=@scanned_document.pdf" \
  "http://localhost:5001/convert?ocr=true"

# Test async processing with OCR
curl -X POST \
  -H "X-API-Key: your_api_key" \
  -F "file=@large_document.pdf" \
  "http://localhost:5001/convert?async=true&ocr=true"
```

## Monitoring

### Container Status
```bash
# Check all containers
docker-compose ps

# Check logs
docker-compose logs doc-converter
docker-compose logs celery-worker
docker-compose logs celery-beat
docker-compose logs redis
```

### Service Health
```bash
# Detailed health with Redis status
curl http://localhost:5001/health

# Supported formats
curl http://localhost:5001/formats
```

## Scaling

### Scale Workers
```bash
# Run 3 celery workers for high load
docker-compose up -d --scale celery-worker=3
```

### Resource Limits

The service includes production-ready resource limits:

- **doc-converter**: 1GB RAM, 1 CPU
- **celery-worker**: 1GB RAM, 1 CPU  
- **celery-beat**: 256MB RAM, 0.25 CPU
- **redis**: 512MB RAM, 0.5 CPU

## Troubleshooting

### Service Won't Start

```bash
# Clean rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Permission Issues

```bash
# Check celery-beat logs for permission errors
docker-compose logs celery-beat

# Should see successful beat start, not permission denied
```

### Document Processing Fails

```bash
# Check supported formats
curl http://localhost:5001/formats

# Ensure file size is under limit (50MB default)
# Verify API key is correct
# Check file format is supported
```

## Updating

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Verify update
python test_service.py
```

## Production Checklist

- [ ] Set secure `API_KEY` in environment
- [ ] Configure appropriate `MAX_CONTENT_LENGTH`
- [ ] Configure `OCR_LANGUAGES` if needed (default: eng+rus)
- [ ] All containers show as "healthy" in `docker-compose ps`
- [ ] Health endpoint returns `"status": "healthy"`
- [ ] Health endpoint shows `"ocr_available": true`
- [ ] Document conversion test passes
- [ ] OCR test passes (with scanned PDF)
- [ ] Logs show no errors or warnings
- [ ] Redis persistence is working (data survives restarts)
- [ ] Celery beat is scheduling cleanup tasks
- [ ] GitHub Actions workflow runs successfully on push
- [ ] Portainer auto-updates enabled (if using Portainer)

## Default Configuration

The service comes with sensible defaults:

- **Port**: 5001 (external) → 5000 (internal)
- **API Key**: `default_dev_key` (change for production!)
- **File Size Limit**: 50MB
- **OCR Languages**: English + Russian (`eng+rus`)
- **Supported Formats**: PDF, DOCX, XLSX, PPTX, TXT, RTF
- **OCR**: Opt-in via `ocr=true` parameter
- **Redis**: Persistent data with automatic cleanup
- **Security**: Non-root user execution
- **Auto-Deploy**: GitHub Actions + Portainer integration

Ready for production use with `docker-compose up -d`!

## Additional Documentation

- **[OCR_DEPLOYMENT.md](OCR_DEPLOYMENT.md)** - Detailed OCR feature guide
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment reference
- **[README.md](README.md)** - Full API documentation and usage examples