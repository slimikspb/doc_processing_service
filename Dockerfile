FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for textract and its dependencies
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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .
COPY file_cleanup.py .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application with Gunicorn (with timeout and worker recycling)
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--timeout", "30", "--max-requests", "1000", "--max-requests-jitter", "50", "--worker-class", "sync", "app:app"]