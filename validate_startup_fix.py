#!/usr/bin/env python3
"""
Validation script to check startup.sh configuration and Docker files.
This script validates that the startup.sh fix should resolve the deployment error.
"""

import os
import stat

def check_startup_sh():
    """Check if startup.sh exists and is executable"""
    startup_path = "startup.sh"
    
    if not os.path.exists(startup_path):
        return False, "startup.sh file not found"
    
    # Check if file is executable
    file_stat = os.stat(startup_path)
    if not (file_stat.st_mode & stat.S_IEXEC):
        return False, "startup.sh is not executable"
    
    # Check shebang
    with open(startup_path, 'r') as f:
        first_line = f.readline().strip()
        if not first_line.startswith('#!/bin/bash'):
            return False, "startup.sh missing proper shebang"
    
    return True, "startup.sh is valid and executable"

def check_dockerfile():
    """Check Dockerfile startup.sh configuration"""
    dockerfile_path = "Dockerfile"
    
    with open(dockerfile_path, 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check if startup.sh is copied with absolute path
    if 'COPY startup.sh /app/startup.sh' not in content:
        issues.append("Dockerfile doesn't copy startup.sh to /app/startup.sh")
    
    # Check if it's made executable
    if 'chmod +x /app/startup.sh' not in content:
        issues.append("Dockerfile doesn't make startup.sh executable")
    
    # Check if CMD uses absolute path
    if '"/app/startup.sh"' not in content:
        issues.append("Dockerfile CMD doesn't use absolute path for startup.sh")
    
    if issues:
        return False, "; ".join(issues)
    
    return True, "Dockerfile startup.sh configuration is correct"

def check_docker_compose():
    """Check docker-compose.yml startup.sh configuration"""
    compose_path = "docker-compose.yml"
    
    with open(compose_path, 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check if celery-worker uses absolute path for startup.sh
    if 'command: ["/app/startup.sh", "celery", "-A", "app_full.celery", "worker"' not in content:
        issues.append("celery-worker doesn't use absolute path for startup.sh")
    
    # Check if celery-beat uses absolute path for startup.sh
    if 'command: ["/app/startup.sh", "celery", "-A", "app_full.celery", "beat"' not in content:
        issues.append("celery-beat doesn't use absolute path for startup.sh")
    
    if issues:
        return False, "; ".join(issues)
    
    return True, "docker-compose.yml startup.sh configuration is correct"

def main():
    """Run all validation checks"""
    print("🔍 Validating startup.sh fix...")
    print("=" * 50)
    
    checks = [
        ("startup.sh file", check_startup_sh),
        ("Dockerfile", check_dockerfile),
        ("docker-compose.yml", check_docker_compose)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            passed, message = check_func()
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {check_name}: {message}")
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"❌ ERROR {check_name}: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All checks passed! The startup.sh fix should resolve the deployment error.")
        print("📝 Next steps:")
        print("   1. Build images: docker-compose build")
        print("   2. Start services: docker-compose up -d")
        print("   3. Check health: docker-compose ps")
    else:
        print("❌ Some checks failed. Please fix the issues above before deployment.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())