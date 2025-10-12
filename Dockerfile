# syntax=docker/dockerfile:1
FROM python:3.9-slim as builder

# Build stage - install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies in builder stage
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# Production stage
FROM python:3.9-slim

# Install only runtime dependencies including Tesseract OCR
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Python optimizations
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/usr/local/bin:$PATH"

# Copy and install wheels from builder
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# Verify critical dependencies
RUN python -c "import flask, celery, redis; print('✓ Core dependencies OK')" && \
    python -c "import fitz, pdfplumber; print('✓ PDF dependencies OK')" && \
    python -c "import docx, openpyxl; print('✓ Office dependencies OK')" && \
    python -c "from pptx import Presentation; print('✓ PowerPoint dependencies OK')" && \
    python -c "import pytesseract; print('✓ OCR dependencies OK')" && \
    which celery && which gunicorn && which tesseract

# Copy application code
COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser reliable_extractor.py .
COPY --chown=appuser:appuser image_extractor.py .
COPY --chown=appuser:appuser ocr_processor.py .
COPY --chown=appuser:appuser pdf_raster_detector.py .
COPY --chown=appuser:appuser file_cleanup.py .
COPY --chown=appuser:appuser redis_manager.py .
COPY --chown=appuser:appuser circuit_breaker.py .
COPY --chown=appuser:appuser graceful_shutdown.py .
COPY --chown=appuser:appuser monitoring.py .
COPY --chown=appuser:appuser health_checks.py .
COPY --chown=appuser:appuser simple_health_check.py .

# Create temp directory with proper permissions
RUN mkdir -p /tmp && chmod 755 /tmp && chown appuser:appuser /tmp

# Ensure appuser can write to working directory (for celery beat schedule file)
RUN chmod 755 /app && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Expose port
EXPOSE 5000

# Run with production server
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--timeout", "30", "--max-requests", "1000", "--max-requests-jitter", "50", "--worker-class", "sync", "app:app"]