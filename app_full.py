"""
Full-featured document processing service with robust import handling
This version ensures all features work while handling dependency issues gracefully
"""
import os
import sys
import logging
import uuid
import time
import glob
import signal
import subprocess
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, url_for, abort
from flask_cors import CORS
import textract
from celery import Celery
from celery.result import AsyncResult
from celery.schedules import crontab
from celery.exceptions import SoftTimeLimitExceeded
from werkzeug.exceptions import RequestEntityTooLarge

# Configure logging first
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app first
app = Flask(__name__)
CORS(app)

# Feature flags - will be set based on successful imports
REDIS_MANAGER_AVAILABLE = False
CIRCUIT_BREAKER_AVAILABLE = False
SHUTDOWN_MANAGER_AVAILABLE = False
MONITORING_AVAILABLE = False
OFFICE_SUPPORT_AVAILABLE = False

# Initialize feature modules with careful error handling
def initialize_features():
    """Initialize enhanced features with robust error handling"""
    global REDIS_MANAGER_AVAILABLE, CIRCUIT_BREAKER_AVAILABLE, SHUTDOWN_MANAGER_AVAILABLE
    global MONITORING_AVAILABLE, OFFICE_SUPPORT_AVAILABLE
    global redis_manager, with_textract_circuit_breaker, textract_circuit_breaker, CircuitBreakerOpenException
    global shutdown_manager, graceful_shutdown_middleware, metrics_collector, create_monitoring_endpoints
    global office_processor, document_extractor
    
    logger.info("Initializing enhanced features...")
    
    # Try Redis manager
    try:
        sys.path.insert(0, '/app')
        from redis_manager import redis_manager
        REDIS_MANAGER_AVAILABLE = True
        logger.info("✓ Redis manager loaded successfully")
    except Exception as e:
        logger.warning(f"Redis manager not available: {e}")
        redis_manager = None
    
    # Try circuit breaker
    try:
        from circuit_breaker import with_textract_circuit_breaker, textract_circuit_breaker, CircuitBreakerOpenException
        CIRCUIT_BREAKER_AVAILABLE = True
        logger.info("✓ Circuit breaker loaded successfully")
    except Exception as e:
        logger.warning(f"Circuit breaker not available: {e}")
        # Create no-op decorators
        def with_textract_circuit_breaker(func):
            return func
        textract_circuit_breaker = None
        CircuitBreakerOpenException = Exception
    
    # Try graceful shutdown
    try:
        from graceful_shutdown import shutdown_manager, graceful_shutdown_middleware
        SHUTDOWN_MANAGER_AVAILABLE = True
        logger.info("✓ Graceful shutdown loaded successfully")
    except Exception as e:
        logger.warning(f"Graceful shutdown not available: {e}")
        shutdown_manager = None
        graceful_shutdown_middleware = lambda x: x
    
    # Try monitoring
    try:
        from monitoring import metrics_collector, create_monitoring_endpoints
        MONITORING_AVAILABLE = True
        logger.info("✓ Monitoring loaded successfully")
    except Exception as e:
        logger.warning(f"Monitoring not available: {e}")
        metrics_collector = None
        create_monitoring_endpoints = lambda x: x
    
    # Try Office processing
    try:
        # Test Office dependencies first
        import openpyxl
        import xlrd
        import pandas
        from pptx import Presentation
        
        from office_processor import office_processor
        from document_extractor import document_extractor
        OFFICE_SUPPORT_AVAILABLE = True
        logger.info("✓ Office processing loaded successfully")
    except Exception as e:
        logger.warning(f"Office processing not available: {e}")
        # Use fallback
        try:
            from fallback_extractor import fallback_document_extractor
            office_processor = None
            document_extractor = fallback_document_extractor
            logger.info("✓ Fallback extractor loaded")
        except Exception as e2:
            logger.error(f"Even fallback extractor failed: {e2}")
            office_processor = None
            document_extractor = None
    
    logger.info(f"Feature initialization complete. Office support: {OFFICE_SUPPORT_AVAILABLE}")

# Initialize features
initialize_features()

# Apply enhanced features if available
if SHUTDOWN_MANAGER_AVAILABLE and shutdown_manager:
    app = graceful_shutdown_middleware(app)

if MONITORING_AVAILABLE and metrics_collector:
    app = create_monitoring_endpoints(app)

# Import file cleanup utilities
from file_cleanup import cleanup_temp_files, get_temp_file_size_mb, TEMP_DIR

# Configure Celery with enhanced settings if Redis manager available
if REDIS_MANAGER_AVAILABLE:
    broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
    backend_url = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
else:
    broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
    backend_url = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

celery = Celery(
    app.name,
    broker=broker_url,
    backend=backend_url
)

# Configure Celery
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1
)

# Configure periodic tasks for cleanup
celery.conf.beat_schedule = {
    'cleanup-temp-files': {
        'task': 'app_full.cleanup_temp_files',
        'schedule': crontab(minute='0', hour='*/1'),  # Run every hour
    },
}
celery.conf.update(app.config)

# Get max content length from environment
max_content_length = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
app.config['MAX_CONTENT_LENGTH'] = max_content_length

# API Key Configuration
API_KEY = os.environ.get('API_KEY', 'default_dev_key')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
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

@app.route('/formats', methods=['GET'])
def supported_formats():
    """Get list of supported document formats"""
    logger.info('Supported formats endpoint accessed')
    
    try:
        if document_extractor:
            formats = document_extractor.get_supported_formats()
        else:
            # Basic formats when no extractor available
            formats = {
                'office_documents': [] if not OFFICE_SUPPORT_AVAILABLE else ['.xlsx', '.xls', '.pptx', '.ppt'],
                'textract_documents': ['.doc', '.docx', '.odt', '.rtf', '.pdf', '.txt', '.png', '.jpg', '.jpeg'],
                'all_supported': []
            }
            formats['all_supported'] = formats['office_documents'] + formats['textract_documents']
        
        return jsonify({
            'supported_formats': formats,
            'office_documents': {
                'formats': formats['office_documents'],
                'description': 'Microsoft Office documents (Excel, PowerPoint)',
                'features': ['Text extraction', 'Metadata extraction', 'Multi-sheet/slide support'] if OFFICE_SUPPORT_AVAILABLE else ['Not available - install dependencies'],
                'available': OFFICE_SUPPORT_AVAILABLE
            },
            'textract_documents': {
                'formats': formats['textract_documents'],
                'description': 'Documents supported by textract library',
                'features': ['Text extraction', 'OCR support', 'Multiple encodings']
            },
            'total_supported': len(formats['all_supported']),
            'feature_status': {
                'office_support': OFFICE_SUPPORT_AVAILABLE,
                'redis_manager': REDIS_MANAGER_AVAILABLE,
                'circuit_breaker': CIRCUIT_BREAKER_AVAILABLE,
                'monitoring': MONITORING_AVAILABLE,
                'graceful_shutdown': SHUTDOWN_MANAGER_AVAILABLE
            }
        })
    
    except Exception as e:
        logger.error(f'Error getting supported formats: {e}')
        return jsonify({'error': 'Failed to retrieve supported formats'}), 500

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

@celery.task(name='app_full.cleanup_temp_files', soft_time_limit=60, time_limit=90)
def cleanup_task():
    """Celery task wrapper for cleanup_temp_files function with timeout"""
    try:
        return cleanup_temp_files()
    except SoftTimeLimitExceeded:
        logger.error('Cleanup task timed out')
        return {'error': 'Cleanup timed out', 'status': 'failed'}

@celery.task(name='app_full.process_document', soft_time_limit=120, time_limit=180)
def process_document(temp_path, original_filename):
    logger.info(f'Processing document: {original_filename}')
    
    try:
        if document_extractor:
            # Use enhanced document extractor
            extraction_result = document_extractor.extract_text(temp_path, timeout=60)
            text = extraction_result['text']
            metadata = extraction_result.get('metadata', {})
            file_info = extraction_result.get('file_info', {})
        else:
            # Fallback to basic textract
            text = textract.process(temp_path).decode('utf-8', errors='replace')
            metadata = {'extraction_method': 'textract_basic'}
            file_info = {'processor_type': 'textract'}
        
        logger.info(f'Text extracted successfully from {original_filename}')
        
        # Remove temporary file
        os.remove(temp_path)
        
        return {
            'filename': original_filename,
            'text': text,
            'status': 'completed',
            'metadata': metadata,
            'file_info': file_info,
            'extraction_method': extraction_result.get('extraction_method', 'basic') if document_extractor else 'textract_basic'
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f'Task timed out processing {original_filename}')
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return {
            'filename': original_filename,
            'error': 'Processing timed out',
            'status': 'failed'
        }
    except Exception as e:
        logger.error(f'Error processing document: {str(e)}')
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return {
            'filename': original_filename,
            'error': str(e),
            'status': 'failed'
        }

@app.route('/convert', methods=['POST'])
@require_api_key
def convert_document():
    logger.info('Convert endpoint accessed')
    start_time = time.time()
    
    try:
        if SHUTDOWN_MANAGER_AVAILABLE and shutdown_manager:
            with shutdown_manager.request_context():
                return _process_convert_request(start_time)
        else:
            return _process_convert_request(start_time)
            
    except RuntimeError as e:
        logger.warning(f'Request rejected during shutdown: {e}')
        return jsonify({'error': 'Service is shutting down'}), 503
    except Exception as e:
        response_time = time.time() - start_time
        if MONITORING_AVAILABLE and metrics_collector:
            metrics_collector.record_request(False, response_time)
        logger.error(f'Unexpected error in convert endpoint: {e}')
        return jsonify({'error': 'Internal server error'}), 500

def _process_convert_request(start_time):
    """Process the convert request with proper error handling and metrics"""
    # Log request details for debugging
    logger.debug(f'Request method: {request.method}')
    logger.debug(f'Request headers: {request.headers}')
    logger.debug(f'Request files: {request.files}')
    
    # Check if document file was provided
    if 'document' not in request.files:
        logger.error('No document file in request')
        return jsonify({'error': 'No document file provided'}), 400
    
    file = request.files['document']
    
    if file.filename == '':
        logger.error('Empty filename')
        return jsonify({'error': 'Empty filename'}), 400
    
    async_processing = request.args.get('async', 'false').lower() == 'true'
    
    try:
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        temp_path = f'/tmp/{unique_filename}'
        
        try:
            file.save(temp_path)
            logger.info(f'File saved temporarily at {temp_path}')
        except RequestEntityTooLarge:
            logger.error('File too large')
            return jsonify({'error': 'File size exceeds maximum allowed'}), 413
        except Exception as e:
            logger.error(f'Failed to save file: {str(e)}')
            return jsonify({'error': 'Failed to save uploaded file'}), 500
        
        if async_processing:
            # Process asynchronously
            task = process_document.delay(temp_path, file.filename)
            
            response_time = time.time() - start_time
            if MONITORING_AVAILABLE and metrics_collector:
                metrics_collector.record_request(True, response_time)
            
            return jsonify({
                'task_id': task.id,
                'status': 'processing',
                'status_url': url_for('get_task_status', task_id=task.id, _external=True)
            })
        else:
            # Process synchronously
            try:
                if document_extractor:
                    extraction_result = document_extractor.extract_text(temp_path, timeout=30)
                    text = extraction_result['text']
                    metadata = extraction_result.get('metadata', {})
                    file_info = extraction_result.get('file_info', {})
                else:
                    # Basic textract fallback
                    text = textract.process(temp_path).decode('utf-8', errors='replace')
                    metadata = {'extraction_method': 'textract_basic'}
                    file_info = {'processor_type': 'textract'}
                    
            except Exception as e:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                logger.error(f'Failed to extract text: {str(e)}')
                return jsonify({'error': f'Failed to process document: {str(e)}'}), 500
            
            logger.info(f'Text extracted successfully from {file.filename}')
            
            # Remove temporary file
            os.remove(temp_path)
            
            # Return extracted text with enhanced metadata
            response_time = time.time() - start_time
            if MONITORING_AVAILABLE and metrics_collector:
                metrics_collector.record_request(True, response_time)
                
            return jsonify({
                'filename': file.filename,
                'text': text,
                'status': 'completed',
                'metadata': metadata,
                'file_info': file_info,
                'extraction_method': extraction_result.get('extraction_method', 'basic') if document_extractor else 'textract_basic'
            })
    
    except Exception as e:
        logger.error(f'Error processing document: {str(e)}')
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
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
    logger.info(f'Starting full-featured application on port {port}')
    logger.info(f'Office support: {OFFICE_SUPPORT_AVAILABLE}')
    logger.info(f'Enhanced features: Redis={REDIS_MANAGER_AVAILABLE}, Circuit={CIRCUIT_BREAKER_AVAILABLE}, Monitoring={MONITORING_AVAILABLE}')
    app.run(host='0.0.0.0', port=port, debug=True)