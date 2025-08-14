"""
Graceful shutdown handler for the document processing service
"""
import os
import signal
import logging
import threading
import time
from typing import List, Callable, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class GracefulShutdownManager:
    """Manages graceful shutdown of the service"""
    
    def __init__(self, shutdown_timeout: float = 30.0):
        self.shutdown_timeout = shutdown_timeout
        self._shutdown_callbacks: List[Callable] = []
        self._is_shutting_down = False
        self._shutdown_lock = threading.RLock()
        self._active_requests = 0
        self._request_lock = threading.RLock()
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info("Graceful shutdown manager initialized")
    
    def register_shutdown_callback(self, callback: Callable):
        """Register a callback to be called during shutdown"""
        with self._shutdown_lock:
            self._shutdown_callbacks.append(callback)
            logger.debug(f"Registered shutdown callback: {callback.__name__}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name} signal, initiating graceful shutdown")
        self.shutdown()
    
    @contextmanager
    def request_context(self):
        """Context manager to track active requests"""
        if self._is_shutting_down:
            raise RuntimeError("Service is shutting down, cannot process new requests")
        
        with self._request_lock:
            self._active_requests += 1
        
        try:
            yield
        finally:
            with self._request_lock:
                self._active_requests -= 1
    
    def is_shutting_down(self) -> bool:
        """Check if service is currently shutting down"""
        return self._is_shutting_down
    
    def get_active_requests(self) -> int:
        """Get count of currently active requests"""
        return self._active_requests
    
    def shutdown(self):
        """Perform graceful shutdown"""
        with self._shutdown_lock:
            if self._is_shutting_down:
                logger.warning("Shutdown already in progress")
                return
            
            self._is_shutting_down = True
            logger.info("Starting graceful shutdown process")
        
        # Wait for active requests to complete
        self._wait_for_requests_completion()
        
        # Execute shutdown callbacks
        self._execute_shutdown_callbacks()
        
        logger.info("Graceful shutdown completed")
    
    def _wait_for_requests_completion(self):
        """Wait for active requests to complete"""
        start_time = time.time()
        
        while self._active_requests > 0:
            remaining_time = self.shutdown_timeout - (time.time() - start_time)
            
            if remaining_time <= 0:
                logger.warning(f"Shutdown timeout reached, {self._active_requests} requests still active")
                break
            
            logger.info(f"Waiting for {self._active_requests} active requests to complete "
                       f"({remaining_time:.1f}s remaining)")
            time.sleep(1)
        
        if self._active_requests == 0:
            logger.info("All active requests completed")
    
    def _execute_shutdown_callbacks(self):
        """Execute all registered shutdown callbacks"""
        logger.info(f"Executing {len(self._shutdown_callbacks)} shutdown callbacks")
        
        for callback in self._shutdown_callbacks:
            try:
                logger.debug(f"Executing shutdown callback: {callback.__name__}")
                callback()
            except Exception as e:
                logger.error(f"Error in shutdown callback {callback.__name__}: {e}")

# Global shutdown manager instance
shutdown_manager = GracefulShutdownManager()

def cleanup_temp_files_on_shutdown():
    """Cleanup function for temporary files during shutdown"""
    try:
        import glob
        pattern = '/tmp/*_*.*'  # Match our UUID-prefixed temp files
        temp_files = glob.glob(pattern)
        
        if temp_files:
            logger.info(f"Cleaning up {len(temp_files)} temporary files during shutdown")
            for file_path in temp_files:
                try:
                    os.remove(file_path)
                except OSError:
                    pass  # File may have been already removed
        
        logger.info("Temporary file cleanup completed")
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {e}")

def close_redis_connections():
    """Close Redis connections during shutdown"""
    try:
        from redis_manager import redis_manager
        redis_manager.close()
        logger.info("Redis connections closed")
    except Exception as e:
        logger.error(f"Error closing Redis connections: {e}")

def celery_shutdown_handler():
    """Handle Celery worker shutdown"""
    try:
        # This would be called in Celery worker processes
        logger.info("Celery worker shutting down gracefully")
        # Additional Celery-specific cleanup can be added here
    except Exception as e:
        logger.error(f"Error in Celery shutdown handler: {e}")

# Register default cleanup callbacks
shutdown_manager.register_shutdown_callback(cleanup_temp_files_on_shutdown)
shutdown_manager.register_shutdown_callback(close_redis_connections)

def graceful_shutdown_middleware(app):
    """Flask middleware for graceful shutdown"""
    @app.before_request
    def before_request():
        if shutdown_manager.is_shutting_down():
            from flask import jsonify
            return jsonify({"error": "Service is shutting down"}), 503
    
    return app