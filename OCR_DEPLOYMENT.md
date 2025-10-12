# OCR Feature Deployment Guide

## Overview

The OCR (Optical Character Recognition) feature enables extraction of text from images embedded in PDF documents using Tesseract OCR.

## Automatic Deployment with Portainer

### Prerequisites
- Portainer configured to pull from GitHub Container Registry
- Repository: `ghcr.io/timur-nocodia/doc_processing_service:latest`

### Deployment Process

1. **Automatic Build on Git Push**
   - Every push to `main` branch triggers GitHub Actions
   - Docker image is built with latest code including OCR support
   - Image is pushed to GitHub Container Registry
   - Tag: `ghcr.io/timur-nocodia/doc_processing_service:latest`

2. **Portainer Auto-Update**
   - Portainer watches the GitHub registry
   - When new image is available, Portainer pulls it
   - Services are automatically recreated with new image
   - **No manual intervention required**

### What's Included in the Image

✅ Tesseract OCR system package
✅ English (eng) language pack
✅ Russian (rus) language pack
✅ Python pytesseract wrapper
✅ Image extraction modules
✅ OCR processing pipeline

## Configuration

### Environment Variables

Add to your Portainer stack or docker-compose:

```yaml
environment:
  - OCR_LANGUAGES=eng+rus  # Default: English + Russian
```

**Supported Language Formats:**
- Single: `OCR_LANGUAGES=eng`
- Multiple: `OCR_LANGUAGES=eng+rus`
- More: `OCR_LANGUAGES=eng+rus+deu+fra`

### Available Language Codes
- `eng` - English
- `rus` - Russian
- `deu` - German
- `fra` - French
- `spa` - Spanish
- `ita` - Italian
- `por` - Portuguese
- `nld` - Dutch
- `pol` - Polish
- `jpn` - Japanese
- `chi_sim` - Chinese Simplified
- `chi_tra` - Chinese Traditional
- `ara` - Arabic

**Note:** Only `eng` and `rus` are pre-installed. To add more languages, you need to update the Dockerfile.

## API Usage

### Check OCR Availability

```bash
curl http://localhost:5001/health
```

Response includes:
```json
{
  "ocr_available": true,
  "ocr_languages": "eng+rus"
}
```

### Use OCR on PDF

**Sync Processing:**
```bash
curl -X POST \
  -H "X-API-Key: default_dev_key" \
  -F "file=@document.pdf" \
  "http://localhost:5001/convert?ocr=true"
```

**Async Processing:**
```bash
# Start processing
curl -X POST \
  -H "X-API-Key: default_dev_key" \
  -F "file=@document.pdf" \
  "http://localhost:5001/convert?async=true&ocr=true"

# Check status
curl -H "X-API-Key: default_dev_key" \
  http://localhost:5001/task/{task_id}
```

### OCR Output Format

When OCR finds images, the output includes:

```json
{
  "text": "Original PDF text...\n\n============================================================\nOCR TEXT FROM IMAGES\n============================================================\n\n[IMAGE ON PAGE 1: 1024x768px]\nExtracted text from image\n[END IMAGE]\n\n[IMAGE ON PAGE 2: 800x600px]\nMore OCR text\n[END IMAGE]",
  "metadata": {
    "ocr_enabled": true,
    "text_length": 15432
  }
}
```

## How It Works

1. **Request Received** with `ocr=true` parameter
2. **PDF Processed** - Extract native text
3. **Images Detected** - Find embedded images in PDF
4. **Image Extraction** - Save images temporarily to `/tmp`
5. **OCR Processing** - Run Tesseract on each image
6. **Text Enrichment** - Append OCR results with annotations
7. **Cleanup** - Delete temporary image files
8. **Response** - Return combined text

## Performance Considerations

### Processing Time
- Without OCR: ~1-2 seconds per PDF
- With OCR: +0.5-2 seconds per image (depends on size/complexity)

### Recommendations
- Use **async mode** (`async=true`) for PDFs with many images
- OCR is **opt-in** - only enable when needed
- System automatically skips OCR if no images found

### Resource Usage
- Memory: +50-100MB per concurrent OCR operation
- CPU: OCR is CPU-intensive, adjust worker count accordingly
- Disk: Temporary images stored in `/tmp`, auto-cleaned

## Monitoring

### Check OCR Status
```bash
# Health check
curl http://localhost:5001/health | jq '.ocr_available, .ocr_languages'

# View logs
docker-compose logs doc-converter | grep -i ocr
docker-compose logs celery-worker | grep -i ocr
```

### Common Log Messages
```
INFO:ocr_processor:OCR processor initialized with languages: eng+rus
INFO:ocr_processor:Tesseract version: X.X.X
INFO:reliable_extractor:Found N images in PDF, performing OCR
INFO:image_extractor:Extracted N images from {file}
```

## Troubleshooting

### OCR Not Available

**Check health endpoint:**
```bash
curl http://localhost:5001/health | jq '.ocr_available'
```

If `false`:
1. Verify image has Tesseract: `docker-compose exec doc-converter which tesseract`
2. Check Tesseract install: `docker-compose exec doc-converter tesseract --version`
3. Verify languages: `docker-compose exec doc-converter tesseract --list-langs`

### No OCR Text in Output

**Possible causes:**
1. PDF has no images (expected behavior)
2. Images are vector graphics (not extractable as raster)
3. Image extraction errors (check logs)

**Check logs:**
```bash
docker-compose logs doc-converter | grep -E "image|ocr" | tail -20
```

### Poor OCR Quality

**Solutions:**
1. Ensure source images are high resolution (300+ DPI)
2. Verify correct language pack is configured
3. Check image quality in source PDF

## Testing

### Test Without OCR (Baseline)
```bash
curl -X POST -H "X-API-Key: default_dev_key" \
  -F "file=@test.pdf" \
  "http://localhost:5001/convert"
```

### Test With OCR
```bash
curl -X POST -H "X-API-Key: default_dev_key" \
  -F "file=@test.pdf" \
  "http://localhost:5001/convert?ocr=true"
```

### Using Test Script
```bash
# Without OCR
python test_service.py --file test.pdf

# With OCR
python test_service.py --file test.pdf --ocr
```

## Update Process

### Automatic Updates via Portainer

1. **Developer pushes code** to GitHub `main` branch
2. **GitHub Actions** builds new Docker image
3. **Image pushed** to ghcr.io registry with `latest` tag
4. **Portainer detects** new image version
5. **Portainer pulls** new image automatically
6. **Services recreated** with new code
7. **Health checks** verify services are healthy

### Manual Force Update (if needed)

```bash
# Pull latest image
docker-compose pull

# Recreate services
docker-compose up -d

# Verify health
docker-compose ps
curl http://localhost:5001/health
```

## Production Checklist

- [ ] Verify `OCR_LANGUAGES` environment variable is set
- [ ] Check health endpoint shows `ocr_available: true`
- [ ] Test OCR with sample scanned PDF
- [ ] Monitor processing times with OCR enabled
- [ ] Verify temporary files are cleaned up
- [ ] Check logs for OCR-related errors
- [ ] Test both sync and async OCR processing
- [ ] Verify image extraction works for your PDF types

## Security Notes

- OCR processing happens in isolated container
- Temporary images stored in `/tmp` with secure permissions
- Images automatically deleted after processing
- No image data persisted or logged
- Standard API key authentication required

## Support

For issues related to:
- **OCR not detecting images**: Check PDF structure and image types
- **Language support**: Update Dockerfile to add language packs
- **Performance**: Adjust worker count and use async mode
- **Errors**: Check logs with `docker-compose logs doc-converter`

