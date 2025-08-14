#!/usr/bin/env python3
"""
Health check utilities for all service components
"""
import os
import sys
import redis
import time
import logging
import subprocess
from celery import Celery
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_redis():
    """Check Redis connectivity and basic operations"""
    try:
        redis_url = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
        r = redis.from_url(redis_url, socket_timeout=5, socket_connect_timeout=5)
        
        # Test basic operations
        r.ping()
        test_key = f"health_check_{int(time.time())}"
        r.set(test_key, "ok", ex=10)
        value = r.get(test_key)
        r.delete(test_key)
        
        if value != b"ok":
            raise Exception("Redis read/write test failed")
            
        # Check memory usage
        info = r.info()
        memory_usage = info.get('used_memory', 0)
        max_memory = info.get('maxmemory', 0)
        
        memory_pct = (memory_usage / max_memory * 100) if max_memory > 0 else 0
        
        logger.info(f"Redis OK - Memory: {memory_pct:.1f}%")
        return True, {"memory_usage_percent": memory_pct}
        
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False, {"error": str(e)}

def check_celery_worker():
    """Check if Celery workers are active and responsive"""
    try:
        celery = Celery(
            'health_check',
            broker=os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
            backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
        )
        
        # Get active workers
        inspect = celery.control.inspect()
        active_workers = inspect.active()
        
        if not active_workers:
            return False, {"error": "No active Celery workers found"}
        
        # Check worker stats
        stats = inspect.stats() or {}
        worker_count = len(active_workers)
        
        logger.info(f"Celery workers OK - {worker_count} active workers")
        return True, {
            "active_workers": worker_count,
            "worker_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Celery worker health check failed: {e}")
        return False, {"error": str(e)}

def check_celery_beat():
    """Check if Celery beat scheduler is running"""
    try:
        # Check if celery beat process is running
        result = subprocess.run(
            ['pgrep', '-f', 'celery.*beat'], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return False, {"error": "Celery beat process not found"}
        
        # Try to connect to Celery to check scheduled tasks
        celery = Celery(
            'health_check',
            broker=os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
            backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
        )
        
        inspect = celery.control.inspect()
        scheduled = inspect.scheduled() or {}
        
        logger.info("Celery beat OK")
        return True, {"scheduled_tasks": len(scheduled)}
        
    except Exception as e:
        logger.error(f"Celery beat health check failed: {e}")
        return False, {"error": str(e)}

def check_disk_space():
    """Check disk space in temp directory"""
    try:
        import shutil
        
        temp_usage = shutil.disk_usage('/tmp')
        total_gb = temp_usage.total / (1024**3)
        used_gb = (temp_usage.total - temp_usage.free) / (1024**3)
        free_gb = temp_usage.free / (1024**3)
        used_pct = (used_gb / total_gb) * 100
        
        # Warning if over 80%, critical if over 90%
        status = "ok"
        if used_pct > 90:
            status = "critical"
        elif used_pct > 80:
            status = "warning"
        
        logger.info(f"Disk space OK - {used_pct:.1f}% used ({free_gb:.1f}GB free)")
        return True, {
            "total_gb": round(total_gb, 2),
            "used_gb": round(used_gb, 2),
            "free_gb": round(free_gb, 2),
            "used_percent": round(used_pct, 1),
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Disk space check failed: {e}")
        return False, {"error": str(e)}

def main():
    """Main health check function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python health_checks.py <redis|celery-worker|celery-beat|disk|all>")
        sys.exit(1)
    
    check_type = sys.argv[1].lower()
    
    checks = {
        'redis': check_redis,
        'celery-worker': check_celery_worker,
        'celery-beat': check_celery_beat,
        'disk': check_disk_space
    }
    
    if check_type == 'all':
        results = {}
        overall_healthy = True
        
        for name, check_func in checks.items():
            healthy, data = check_func()
            results[name] = {"healthy": healthy, "data": data}
            if not healthy:
                overall_healthy = False
        
        print(f"Overall health: {'HEALTHY' if overall_healthy else 'UNHEALTHY'}")
        for name, result in results.items():
            status = "✓" if result["healthy"] else "✗"
            print(f"{status} {name}: {result['data']}")
        
        sys.exit(0 if overall_healthy else 1)
    
    elif check_type in checks:
        healthy, data = checks[check_type]()
        status = "HEALTHY" if healthy else "UNHEALTHY"
        print(f"{check_type}: {status} - {data}")
        sys.exit(0 if healthy else 1)
    
    else:
        print(f"Unknown check type: {check_type}")
        sys.exit(1)

if __name__ == '__main__':
    main()