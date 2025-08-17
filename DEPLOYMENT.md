# Deployment Guide

This guide shows how to deploy the Document Processing Service using the standard configuration.

## Quick Deployment

```bash
# Clone and enter directory
git clone <repository-url>
cd doc_processing_service

# Start all services
docker-compose up -d

# Check everything is running
docker-compose ps

# Test the service
python test_service.py
```

## Production Deployment

### 1. Environment Configuration

Create a `.env` file:

```bash
# Security
API_KEY=your_secure_api_key_here

# Performance
MAX_CONTENT_LENGTH=52428800  # 50MB

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
- [ ] All containers show as "healthy" in `docker-compose ps`
- [ ] Health endpoint returns `"status": "healthy"`
- [ ] Document conversion test passes
- [ ] Logs show no errors or warnings
- [ ] Redis persistence is working (data survives restarts)
- [ ] Celery beat is scheduling cleanup tasks

## Default Configuration

The service comes with sensible defaults:

- **Port**: 5001 (external) → 5000 (internal)
- **API Key**: `default_dev_key` (change for production!)
- **File Size Limit**: 50MB
- **Supported Formats**: PDF, DOCX, XLSX, PPTX, TXT, RTF
- **Redis**: Persistent data with automatic cleanup
- **Security**: Non-root user execution

Ready for production use with `docker-compose up -d`!