FROM python:3.9-slim

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install system dependencies for textract and office document processing
RUN apt-get update && apt-get install -y \
    antiword \
    unrtf \
    poppler-utils \
    libjpeg-dev \
    libxml2-dev \
    libxslt1-dev \
    tesseract-ocr \
    build-essential \
    curl \
    supervisor \
    # Additional dependencies for pandas and Excel processing
    libssl-dev \
    libffi-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    # Verify Office processing dependencies are installed correctly
    python -c "import openpyxl; import xlrd; import pandas; from pptx import Presentation; print('✓ Office dependencies verified')" || \
    (echo "Reinstalling Office dependencies..." && pip install --force-reinstall openpyxl xlrd xlwt pandas python-pptx oletools)

# Copy the application code
COPY app_full.py app.py
COPY app_full.py .
COPY file_cleanup.py .
COPY redis_manager.py .
COPY circuit_breaker.py .
COPY graceful_shutdown.py .
COPY monitoring.py .
COPY health_checks.py .
COPY simple_health_check.py .
COPY office_processor.py .
COPY document_extractor.py .
COPY fallback_extractor.py .

# Create temp directory and set permissions
RUN mkdir -p /tmp && chmod 755 /tmp

# Change ownership to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application directly with Gunicorn
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--timeout", "30", "--max-requests", "1000", "--max-requests-jitter", "50", "--worker-class", "sync", "app_full:app"]