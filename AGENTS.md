# Agent Guidelines for Document Processing Service

## Build/Test Commands
- **Run tests**: `python test_service.py`
- **Test specific file**: `python test_service.py --file path/to/document.pdf`
- **Test async mode**: `python test_service.py --async-mode`
- **Test cleanup**: `python test_service.py --cleanup`
- **Health check**: `curl http://localhost:5001/health`

## Code Style Guidelines
- **Python version**: 3.8+
- **Imports**: Group standard library, third-party, then local imports
- **Formatting**: 4-space indentation, 79-char line limit
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Error handling**: Use try/except with specific exceptions, log warnings
- **Type hints**: Not required but encouraged for new code
- **Docstrings**: Use triple quotes for module/function descriptions
- **Logging**: Use `logging` module, format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

## Architecture Notes
- Flask app with Celery for async processing
- Redis for task queue and caching
- Graceful degradation when optional modules unavailable
- Use `DOCUMENT_PROCESSING_AVAILABLE` and `ENHANCED_FEATURES_AVAILABLE` flags
- All endpoints require `X-API-Key` header except `/health` and `/formats`