# Document Converter Service

Converts Word documents (DOC, DOCX), ODT, and RTF files to plain text. Built with Flask, Celery, and Redis for reliable async processing.

## Quick Start

```bash
# Start everything
docker-compose up -d

# Test it works
curl http://localhost:5001/health

# Convert a document (replace YOUR_API_KEY with actual key from docker-compose.yml)
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "document=@your-file.docx" \
  http://localhost:5001/convert
```

## API Endpoints

### 1. Convert Document
**POST** `/convert`

**Headers:**
- `X-API-Key: your_api_key` (required)

**Body:**
- Form field name: `document` (NOT "file")
- Supported formats: DOC, DOCX, ODT, RTF, PPTX, PDF

**Sync mode (default):**
```bash
curl -X POST \
  -H "X-API-Key: default_dev_key" \
  -F "document=@test.docx" \
  http://localhost:5001/convert
```

**Async mode (for large files):**
```bash
curl -X POST \
  -H "X-API-Key: default_dev_key" \
  -F "document=@large.docx" \
  http://localhost:5001/convert?async=true
```

Returns task_id for checking status.

### 2. Check Async Task Status
**GET** `/task/<task_id>`

```bash
curl -H "X-API-Key: default_dev_key" \
  http://localhost:5001/task/abc-123-def
```

### 3. Health Check
**GET** `/health` (no auth required)

```bash
curl http://localhost:5001/health
```

### 4. Manual Cleanup
**POST** `/cleanup`

```bash
curl -X POST -H "X-API-Key: default_dev_key" \
  http://localhost:5001/cleanup
```

## n8n Integration

### HTTP Request Node Configuration:

1. **Method:** POST
2. **URL:** `http://doc-converter:5001/convert` (or your service URL)
3. **Authentication:** 
   - Type: Generic Credential → Header Auth
   - Name: `X-API-Key`
   - Value: Your API key
4. **Send Body:** Yes
5. **Body Content Type:** Form-Data
6. **Body Parameters:**
   - Parameter Type: Form Data
   - Name: `document` ⚠️ (NOT "file")
   - Input Data Field Name: `data` (or your binary property name)

### Common n8n Errors:

- **"No document file provided"** → Check field name is `document` not `file`
- **"source.on is not a function"** → Use Input Data Field Name instead of expression
- **401 Unauthorized** → Add X-API-Key header

## Environment Variables

Set in `docker-compose.yml`:

```yaml
API_KEY: your_secure_key_here        # Default: default_dev_key
MAX_CONTENT_LENGTH: 16777216         # Max file size (16MB default)
PORT: 5000                            # Internal port (mapped to 5001)
CELERY_BROKER_URL: redis://redis:6379/0
```

## Testing

```bash
# Basic test script
python test_service.py

# Test with specific file
python test_service.py --file test.docx --api-key your_key

# Test async mode
python test_service.py --file large.docx --async-mode

# Test multiple formats
python test_multiple_formats.py
```

## Monitoring

```bash
# View all logs
docker-compose logs -f

# Check specific service
docker-compose logs doc-converter
docker-compose logs celery-worker

# Container status
docker-compose ps
```

## Troubleshooting

### Service won't start
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### File size errors
Increase MAX_CONTENT_LENGTH in docker-compose.yml (default 16MB)

### Encoding errors
Service automatically tries UTF-8, CP1251, then UTF-8 with replacement

### Disk space issues
- Cleanup runs hourly automatically
- Manual cleanup: `POST /cleanup`
- Check /tmp usage: `docker exec doc-converter df -h /tmp`

### Port conflicts
Change external port in docker-compose.yml:
```yaml
ports:
  - "8080:5000"  # Change 8080 to any free port
```

## Architecture

- **Flask API** → Handles HTTP requests
- **Celery Workers** → Process documents async
- **Redis** → Message queue and result storage
- **Celery Beat** → Hourly temp file cleanup

Files are temporarily stored in `/tmp` with UUID prefixes and deleted after processing.