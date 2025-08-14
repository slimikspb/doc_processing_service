#!/usr/bin/env python3
"""
Simple health check script that doesn't depend on complex imports
Used for Docker health checks to avoid startup hang issues
"""
import sys
import os
import subprocess

def check_celery_worker():
    """Simple check if celery worker process is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'celery.*worker'], 
                              capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def check_celery_beat():
    """Simple check if celery beat process is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'celery.*beat'], 
                              capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def main():
    """Simple health check for Docker"""
    if len(sys.argv) < 2:
        print("Usage: python simple_health_check.py <celery-worker|celery-beat>")
        sys.exit(1)
    
    check_type = sys.argv[1].lower()
    
    if check_type == 'celery-worker':
        healthy = check_celery_worker()
    elif check_type == 'celery-beat':
        healthy = check_celery_beat()
    else:
        print(f"Unknown check type: {check_type}")
        sys.exit(1)
    
    if healthy:
        print(f"{check_type}: HEALTHY")
        sys.exit(0)
    else:
        print(f"{check_type}: UNHEALTHY")
        sys.exit(1)

if __name__ == '__main__':
    main()