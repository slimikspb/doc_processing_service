"""
Redis connection manager with retry logic and health monitoring
"""
import os
import time
import redis
import logging
from typing import Optional, Dict, Any
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class RedisConnectionManager:
    """Manages Redis connections with retry logic and health monitoring"""
    
    def __init__(self, 
                 redis_url: str = None,
                 max_retries: int = 5,
                 initial_retry_delay: float = 1.0,
                 max_retry_delay: float = 60.0,
                 backoff_multiplier: float = 2.0,
                 socket_timeout: float = 5.0,
                 socket_connect_timeout: float = 5.0):
        
        self.redis_url = redis_url or os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay
        self.backoff_multiplier = backoff_multiplier
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        
        self._connection: Optional[redis.Redis] = None
        self._last_health_check = 0
        self._health_check_interval = 30  # seconds
        self._is_healthy = False
    
    def _create_connection(self) -> redis.Redis:
        """Create a new Redis connection with proper configuration"""
        return redis.from_url(
            self.redis_url,
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout,
            retry_on_timeout=True,
            decode_responses=False  # Keep binary for Celery compatibility
        )
    
    def _test_connection(self, connection: redis.Redis) -> bool:
        """Test if a Redis connection is working"""
        try:
            connection.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis connection test failed: {e}")
            return False
    
    def _wait_with_backoff(self, attempt: int) -> None:
        """Wait with exponential backoff"""
        delay = min(
            self.initial_retry_delay * (self.backoff_multiplier ** attempt),
            self.max_retry_delay
        )
        logger.info(f"Waiting {delay:.2f}s before retry attempt {attempt + 1}")
        time.sleep(delay)
    
    def get_connection(self, force_reconnect: bool = False) -> redis.Redis:
        """Get a healthy Redis connection with retry logic"""
        current_time = time.time()
        
        # Check if we need to verify connection health
        if (not force_reconnect and 
            self._connection and 
            self._is_healthy and 
            (current_time - self._last_health_check) < self._health_check_interval):
            return self._connection
        
        # Test existing connection
        if not force_reconnect and self._connection:
            if self._test_connection(self._connection):
                self._is_healthy = True
                self._last_health_check = current_time
                return self._connection
            else:
                logger.warning("Existing Redis connection is unhealthy, reconnecting...")
        
        # Create new connection with retry logic
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Attempting to connect to Redis (attempt {attempt + 1}/{self.max_retries})")
                
                connection = self._create_connection()
                
                if self._test_connection(connection):
                    self._connection = connection
                    self._is_healthy = True
                    self._last_health_check = current_time
                    logger.info("Successfully connected to Redis")
                    return connection
                else:
                    connection.close()
                    
            except Exception as e:
                logger.error(f"Redis connection attempt {attempt + 1} failed: {e}")
            
            if attempt < self.max_retries - 1:
                self._wait_with_backoff(attempt)
        
        # All attempts failed
        self._is_healthy = False
        raise redis.ConnectionError(f"Failed to connect to Redis after {self.max_retries} attempts")
    
    @contextmanager
    def get_connection_context(self):
        """Context manager for Redis connections"""
        connection = None
        try:
            connection = self.get_connection()
            yield connection
        except Exception as e:
            logger.error(f"Error in Redis connection context: {e}")
            raise
        finally:
            # Connection is managed by the manager, no need to close
            pass
    
    def execute_with_retry(self, operation, *args, **kwargs):
        """Execute a Redis operation with retry logic"""
        for attempt in range(self.max_retries):
            try:
                connection = self.get_connection()
                return operation(connection, *args, **kwargs)
            
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.warning(f"Redis operation failed (attempt {attempt + 1}): {e}")
                
                if attempt < self.max_retries - 1:
                    # Force reconnect on next attempt
                    self._is_healthy = False
                    self._wait_with_backoff(attempt)
                else:
                    raise
            
            except Exception as e:
                # Non-connection related errors shouldn't trigger retries
                logger.error(f"Redis operation error (non-retryable): {e}")
                raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of Redis connection"""
        try:
            connection = self.get_connection()
            info = connection.info()
            
            return {
                "healthy": True,
                "connected": True,
                "memory_usage": info.get('used_memory', 0),
                "memory_usage_mb": info.get('used_memory', 0) / (1024 * 1024),
                "connected_clients": info.get('connected_clients', 0),
                "uptime_seconds": info.get('uptime_in_seconds', 0),
                "redis_version": info.get('redis_version', 'unknown')
            }
        
        except Exception as e:
            return {
                "healthy": False,
                "connected": False,
                "error": str(e)
            }
    
    def close(self):
        """Close the Redis connection"""
        if self._connection:
            try:
                self._connection.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                self._connection = None
                self._is_healthy = False

# Global instance
redis_manager = RedisConnectionManager()

def with_redis_retry(max_retries: int = 3):
    """Decorator for functions that need Redis with retry logic"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return redis_manager.execute_with_retry(
                lambda conn: func(conn, *args, **kwargs)
            )
        return wrapper
    return decorator