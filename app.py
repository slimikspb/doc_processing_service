import os
import logging
import uuid
import time
import glob
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, url_for, abort
from flask_cors import CORS
import textract
from celery import Celery
from celery.result import AsyncResult
from celery.schedules import crontab

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Import file cleanup utilities
from file_cleanup import cleanup_temp_files, get_temp_file_size_mb, TEMP_DIR

# Configure Celery
celery = Celery(
    app.name,
    broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Configure periodic tasks for cleanup
celery.conf.beat_schedule = {
    'cleanup-temp-files': {
        'task': 'app.cleanup_task',
        'schedule': crontab(minute='0', hour='*/1'),  # Run every hour
    },
}
celery.conf.update(app.config)

# Get max content length from environment or use default (16MB)
max_content_length = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
app.config['MAX_CONTENT_LENGTH'] = max_content_length

# API Key Configuration
API_KEY = os.environ.get('API_KEY', 'default_dev_key')  # Default key for development

# API Key Authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key in headers or query parameters
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key or api_key != API_KEY:
            logger.warning(f'Unauthorized access attempt from {request.remote_addr}')
            abort(401, description='Unauthorized: Invalid or missing API key')
            
        return f(*args, **kwargs)
    return decorated_function

@app.route('/health', methods=['GET'])
def health_check():
    logger.info('Health check endpoint accessed')
    return jsonify({'status': 'ok'})

@app.route('/cleanup', methods=['POST'])
@require_api_key
def trigger_cleanup():
    """Manually trigger the cleanup process"""
    logger.info('Manual cleanup triggered')
    task = cleanup_task.delay()
    return jsonify({
        'task_id': task.id,
        'status': 'cleanup_started',
        'message': 'Cleanup task started'
    })

@celery.task(name='app.cleanup_temp_files')
def cleanup_task():
    """Celery task wrapper for cleanup_temp_files function"""
    return cleanup_temp_files()

# Celery task for document processing
@celery.task(name='app.process_document')
def process_document(temp_path, original_filename):
    logger.info(f'Processing document: {original_filename}')
    
    try:
        # Extract text from the document
        try:
            # Try UTF-8 first
            text = textract.process(temp_path).decode('utf-8')
        except UnicodeDecodeError:
            # If UTF-8 fails, try other encodings
            try:
                text = textract.process(temp_path).decode('cp1251')  # Windows Cyrillic
            except UnicodeDecodeError:
                # Last resort - use 'replace' to handle unknown characters
                text = textract.process(temp_path).decode('utf-8', errors='replace')
        
        logger.info(f'Text extracted successfully from {original_filename}')
        
        # Remove temporary file
        os.remove(temp_path)
        
        return {
            'filename': original_filename,
            'text': text,
            'status': 'completed'
        }
    except Exception as e:
        logger.error(f'Error processing document: {str(e)}')
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {
            'filename': original_filename,
            'error': str(e),
            'status': 'failed'
        }

@app.route('/convert', methods=['POST'])
@require_api_key
def convert_document():
    logger.info('Convert endpoint accessed')
    
    # Log request details for debugging
    logger.debug(f'Request method: {request.method}')
    logger.debug(f'Request headers: {request.headers}')
    logger.debug(f'Request files: {request.files}')
    
    # Check if document file was provided
    if 'document' not in request.files:
        logger.error('No document file in request')
        return jsonify({'error': 'No document file provided'}), 400
    
    file = request.files['document']
    
    # Check if filename is empty
    if file.filename == '':
        logger.error('Empty filename')
        return jsonify({'error': 'Empty filename'}), 400
    
    # Check if async processing is requested
    async_processing = request.args.get('async', 'false').lower() == 'true'
    
    try:
        # Generate a unique filename to avoid collisions
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        temp_path = f'/tmp/{unique_filename}'
        file.save(temp_path)
        logger.info(f'File saved temporarily at {temp_path}')
        
        if async_processing:
            # Process the document asynchronously
            task = process_document.delay(temp_path, file.filename)
            
            # Return task ID for status checking
            return jsonify({
                'task_id': task.id,
                'status': 'processing',
                'status_url': url_for('get_task_status', task_id=task.id, _external=True)
            })
        else:
            # Process the document synchronously (original behavior)
            try:
                # Try UTF-8 first
                text = textract.process(temp_path).decode('utf-8')
            except UnicodeDecodeError:
                # If UTF-8 fails, try other encodings
                try:
                    text = textract.process(temp_path).decode('cp1251')  # Windows Cyrillic
                except UnicodeDecodeError:
                    # Last resort - use 'replace' to handle unknown characters
                    text = textract.process(temp_path).decode('utf-8', errors='replace')
            
            logger.info(f'Text extracted successfully from {file.filename}')
            
            # Remove temporary file
            os.remove(temp_path)
            
            # Return the extracted text
            return jsonify({
                'filename': file.filename,
                'text': text,
                'status': 'completed'
            })
    
    except Exception as e:
        logger.error(f'Error processing document: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/task/<task_id>', methods=['GET'])
@require_api_key
def get_task_status(task_id):
    """Check the status of an asynchronous task"""
    task_result = AsyncResult(task_id, app=celery)
    
    if task_result.state == 'PENDING':
        response = {
            'task_id': task_id,
            'status': 'processing'
        }
    elif task_result.state == 'SUCCESS':
        response = task_result.result
    else:
        response = {
            'task_id': task_id,
            'status': 'failed',
            'error': str(task_result.result) if task_result.result else 'Unknown error'
        }
    
    return jsonify(response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f'Starting application on port {port}')
    app.run(host='0.0.0.0', port=port, debug=True)