# 🚀 Complete Deployment Guide

## Latest Updates

### ✨ OCR Feature Added (2025-10-12)
- ✅ Tesseract OCR support for PDF image extraction
- ✅ Multi-language support (EN+RU default, configurable)
- ✅ Opt-in via `ocr=true` query parameter
- ✅ Automatic GitHub Actions build and push
- ✅ See [OCR_DEPLOYMENT.md](OCR_DEPLOYMENT.md) for details

### Previous Critical Issue Resolution

The container health issues were caused by **Docker volume caching** where `app_code:/app` volume mounts were overriding the new code in Docker images with old cached code.

✅ **FIXED**: Removed all problematic volume mounts from docker-compose.yml
✅ **VERIFIED**: All required files are present and valid

## Automated Deployment Process

### Production (via Portainer)

**Automatic Updates:**
1. Push code to GitHub `main` branch
2. GitHub Actions builds Docker image
3. Image pushed to `ghcr.io/timur-nocodia/doc_processing_service:latest`
4. Portainer auto-detects and pulls new image
5. Services automatically recreated with new code

**No manual intervention required!**

### Local Development Deployment

#### Step 1: Validate Build
```bash
./validate_build.sh
```
This checks that all required files are present and properly configured.

#### Step 2: Fresh Deployment
```bash
./deploy_fresh.sh
```
This script will:
- Stop all containers
- Remove old containers and cached images
- Build fresh images with `--no-cache`
- Start new containers with the latest code

#### Step 3: Monitor Health Status
```bash
# Check container status (should show all as healthy after ~60-90 seconds)
docker-compose ps

# Monitor real-time logs
docker-compose logs -f

# Check specific service logs
docker-compose logs doc-converter
docker-compose logs celery-worker
docker-compose logs celery-beat
docker-compose logs redis
```

## Expected Healthy State

After successful deployment, `docker-compose ps` should show:

```
         Name                        Command                  State                    Ports                  
------------------------------------------------------------------------------------------------------------
algiers_celery-beat_1      ./startup.sh celery -A app ...   Up (healthy)                                   
algiers_celery-worker_1    ./startup.sh celery -A app ...   Up (healthy)                                   
algiers_doc-converter_1    ./startup.sh gunicorn -w 2 ...   Up (healthy)   0.0.0.0:5001->5000/tcp         
algiers_redis_1            docker-entrypoint.sh redis ...   Up (healthy)   6379/tcp                        
```

## Health Check Timing

- **Redis**: Ready in ~10-15 seconds
- **Doc-converter**: Ready in ~20-30 seconds  
- **Celery-worker**: Ready in ~60 seconds
- **Celery-beat**: Ready in ~90 seconds

## What Was Fixed

1. **Volume Caching Issue**:
   - ❌ Before: `- app_code:/app` volume mounts cached old code
   - ✅ After: Removed volume mounts, Docker image provides fresh code

2. **Task Registration**:
   - ❌ Before: `app.cleanup_task` (unregistered task error)
   - ✅ After: `app_full.cleanup_temp_files` (proper task name)

3. **Office Processing**:
   - ✅ Added: Full Excel (.xlsx/.xls) and PowerPoint (.pptx/.ppt) support
   - ✅ Added: Intelligent fallback when Office dependencies unavailable

4. **Security**:
   - ✅ Added: Non-root user execution (no more superuser warnings)

5. **Startup Reliability**:
   - ✅ Added: Comprehensive dependency verification
   - ✅ Added: Redis connection retry with exponential backoff
   - ✅ Added: Graceful import handling for Office dependencies

## API Testing

Once deployed, test the service:

```bash
# Health check (now includes OCR status)
curl http://localhost:5001/health

# Document conversion
curl -X POST -H "X-API-Key: default_dev_key" \
     -F "file=@test.docx" \
     http://localhost:5001/convert

# Document conversion with OCR
curl -X POST -H "X-API-Key: default_dev_key" \
     -F "file=@test.pdf" \
     "http://localhost:5001/convert?ocr=true"

# Supported formats
curl -H "X-API-Key: default_dev_key" \
     http://localhost:5001/formats
```

### Health Check Response
```json
{
  "status": "healthy",
  "document_processing": true,
  "enhanced_features": false,
  "ocr_available": true,
  "ocr_languages": "eng+rus",
  "redis": "healthy",
  "supported_formats": ["txt", "rtf", "pdf", "docx", "doc", "xlsx", "xls", "pptx"]
}
```

## Troubleshooting

If containers remain unhealthy:

1. **Check startup logs**:
   ```bash
   docker-compose logs doc-converter --tail=50
   ```

2. **Verify Redis connectivity**:
   ```bash
   docker-compose exec doc-converter python -c "import redis; r=redis.Redis(host='redis'); print(r.ping())"
   ```

3. **Test Office dependencies**:
   ```bash
   docker-compose exec doc-converter python -c "import openpyxl, xlrd, pandas; from pptx import Presentation; print('OK')"
   ```

4. **Manual health check**:
   ```bash
   docker-compose exec celery-worker python simple_health_check.py celery-worker
   docker-compose exec celery-beat python simple_health_check.py celery-beat
   ```

## Key Files Updated

- ✅ `docker-compose.yml` - Production registry configuration + OCR env
- ✅ `Dockerfile` - Tesseract OCR installation
- ✅ `app.py` - OCR parameter and health check
- ✅ `reliable_extractor.py` - OCR integration
- ✅ `image_extractor.py` - NEW: Image extraction from PDFs
- ✅ `ocr_processor.py` - NEW: Tesseract OCR wrapper
- ✅ `.github/workflows/docker-build-push.yml` - NEW: Auto-build pipeline
- ✅ `OCR_DEPLOYMENT.md` - NEW: OCR-specific documentation

## Success Criteria

✅ All 4 containers show "Up (healthy)" status
✅ No "unregistered task" errors in logs  
✅ Office document processing works (Excel/PowerPoint)
✅ **OCR available** (`ocr_available: true` in health check)
✅ **OCR languages** configured (default: `eng+rus`)
✅ API endpoints respond correctly
✅ Temp file cleanup runs without errors
✅ **GitHub Actions** builds and pushes on commit