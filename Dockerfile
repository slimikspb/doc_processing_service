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

# Install Python dependencies in stages for better error handling
RUN pip install --upgrade pip

# Install core dependencies first
RUN pip install --no-cache-dir \
    flask==2.0.1 \
    werkzeug==2.0.1 \
    gunicorn==20.1.0 \
    celery==5.2.3 \
    redis==4.3.4 \
    flask-cors==3.0.10 \
    psutil==5.9.4

# Install textract (can be problematic, so separate)
RUN pip install --no-cache-dir textract==1.6.5

# Install Office processing dependencies with compatible versions
RUN pip install --no-cache-dir \
    numpy==1.24.3 \
    openpyxl==3.0.10 \
    xlrd==2.0.1 \
    xlwt==1.3.0

# Install pandas with numpy already available
RUN pip install --no-cache-dir pandas==1.5.3

# Install PowerPoint processing
RUN pip install --no-cache-dir \
    python-pptx==0.6.21 \
    oletools==0.60.1

# Verify core installations work
RUN python -c "import flask, celery, redis, textract; print('✓ Core dependencies OK')" && \
    python -c "import openpyxl, xlrd, pandas; print('✓ Excel dependencies OK')" && \
    python -c "from pptx import Presentation; print('✓ PowerPoint dependencies OK')" && \
    which celery && celery --version

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

# Set PATH to ensure celery and other binaries are accessible
ENV PATH="/usr/local/bin:$PATH"

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application directly with Gunicorn
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--timeout", "30", "--max-requests", "1000", "--max-requests-jitter", "50", "--worker-class", "sync", "app_full:app"]