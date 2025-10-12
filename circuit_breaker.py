"""
Circuit breaker implementation for external service calls
"""
import time
import logging
import threading
from enum import Enum
from typing import Callable, Any, Dict, Optional
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5          # Number of failures to open circuit
    recovery_timeout: float = 60.0      # Seconds to wait before trying again
    success_threshold: int = 2          # Successes needed to close circuit in half-open
    timeout: float = 30.0               # Operation timeout in seconds
    expected_exception: tuple = (Exception,)  # Exceptions that count as failures

class CircuitBreaker:
    """Circuit breaker for protecting against cascading failures"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0
        self._lock = threading.RLock()
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    @property
    def state(self) -> CircuitState:
        return self._state
    
    @property
    def failure_count(self) -> int:
        return self._failure_count
    
    def _should_allow_request(self) -> bool:
        """Check if request should be allowed based on current state"""
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return True
            
            elif self._state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if time.time() - self._last_failure_time >= self.config.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' moving to HALF_OPEN state")
                    return True
                return False
            
            elif self._state == CircuitState.HALF_OPEN:
                return True
            
            return False
    
    def _record_success(self):
        """Record a successful operation"""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info(f"Circuit breaker '{self.name}' CLOSED after recovery")
            
            elif self._state == CircuitState.CLOSED:
                self._failure_count = max(0, self._failure_count - 1)
    
    def _record_failure(self):
        """Record a failed operation"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' OPENED again after half-open failure")
            
            elif (self._state == CircuitState.CLOSED and 
                  self._failure_count >= self.config.failure_threshold):
                self._state = CircuitState.OPEN
                logger.error(f"Circuit breaker '{self.name}' OPENED after {self._failure_count} failures")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if not self._should_allow_request():
            raise CircuitBreakerOpenException(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Last failure: {time.time() - self._last_failure_time:.1f}s ago"
            )
        
        try:
            # Execute the function with timeout
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            self._record_success()
            logger.debug(f"Circuit breaker '{self.name}': Success ({execution_time:.2f}s)")
            return result
        
        except self.config.expected_exception as e:
            self._record_failure()
            logger.warning(f"Circuit breaker '{self.name}': Failure - {str(e)}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "time_since_last_failure": time.time() - self._last_failure_time if self._last_failure_time else None
        }

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class TextractCircuitBreaker(CircuitBreaker):
    """Specialized circuit breaker for textract operations"""
    
    def __init__(self, name: str = "textract"):
        config = CircuitBreakerConfig(
            failure_threshold=3,        # Open after 3 failures
            recovery_timeout=120.0,     # Wait 2 minutes before retry
            success_threshold=2,        # Need 2 successes to close
            timeout=60.0,               # 60 second timeout for textract
            expected_exception=(Exception,)  # All exceptions count as failures
        )
        super().__init__(name, config)

# Global circuit breakers
textract_circuit_breaker = TextractCircuitBreaker()

def circuit_breaker(breaker: CircuitBreaker):
    """Decorator to apply circuit breaker to a function"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator

def with_circuit_breaker(func: Callable) -> Callable:
    """Decorator for generic circuit breaker protection"""
    return circuit_breaker(textract_circuit_breaker)(func)

def with_textract_circuit_breaker(func: Callable) -> Callable:
    """Decorator specifically for textract operations"""
    return circuit_breaker(textract_circuit_breaker)(func)