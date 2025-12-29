#!/usr/bin/env python3
"""
Deployment verification script to ensure eventlet conflicts are resolved.
Run this before deploying to catch configuration issues early.
"""

import sys
import os
import subprocess
import importlib.util

def check_eventlet_status():
    """Check if eventlet is installed and configured properly."""
    print("🔍 Checking eventlet configuration...")
    
    # Check if eventlet is installed
    eventlet_installed = importlib.util.find_spec("eventlet") is not None
    
    if eventlet_installed:
        print("❌ ISSUE: eventlet is still installed")
        print("   This will cause Gunicorn to auto-detect and use eventlet worker")
        print("   Solution: Run 'pip uninstall eventlet' before deployment")
        return False
    else:
        print("✅ GOOD: eventlet is not installed")
        return True

def check_gunicorn_config():
    """Check Gunicorn configuration files."""
    print("\n🔍 Checking Gunicorn configuration...")
    
    config_files = ['Procfile', 'start.py']
    issues = []
    
    for config_file in config_files:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                content = f.read()
                
            if 'eventlet' in content and '--worker-class eventlet' in content:
                issues.append(f"{config_file} still uses eventlet worker")
            elif 'gthread' in content or 'sync' in content:
                print(f"✅ GOOD: {config_file} uses non-eventlet worker")
            else:
                issues.append(f"{config_file} worker class unclear")
    
    if issues:
        print("❌ ISSUES found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        return True

def check_flask_socketio_config():
    """Check Flask-SocketIO configuration."""
    print("\n🔍 Checking Flask-SocketIO configuration...")
    
    # Check wsgi files
    wsgi_files = ['wsgi_clean.py', 'app/__init__.py']
    configured = False
    
    for wsgi_file in wsgi_files:
        if os.path.exists(wsgi_file):
            with open(wsgi_file, 'r') as f:
                content = f.read()
                
            if "async_mode='threading'" in content:
                print(f"✅ GOOD: {wsgi_file} configures threading mode")
                configured = True
            elif "FLASK_SOCKETIO_ASYNC_MODE" in content:
                print(f"✅ GOOD: {wsgi_file} sets threading environment variable")
                configured = True
    
    if not configured:
        print("❌ ISSUE: Flask-SocketIO threading mode not configured")
        return False
    
    return True

def check_requirements():
    """Check requirements.txt for eventlet."""
    print("\n🔍 Checking requirements.txt...")
    
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            content = f.read()
        
        if 'eventlet==' in content and not content.count('# eventlet=='):
            print("❌ ISSUE: eventlet is still listed in requirements.txt")
            return False
        elif '# eventlet==' in content:
            print("✅ GOOD: eventlet is commented out in requirements.txt")
            return True
        else:
            print("✅ GOOD: eventlet not found in requirements.txt")
            return True
    else:
        print("⚠️ WARNING: requirements.txt not found")
        return True

def main():
    """Run all deployment checks."""
    print("🚀 Deployment Configuration Verification")
    print("=" * 50)
    
    checks = [
        check_eventlet_status,
        check_gunicorn_config,
        check_flask_socketio_config,
        check_requirements
    ]
    
    all_passed = True
    
    for check in checks:
        try:
            if not check():
                all_passed = False
        except Exception as e:
            print(f"❌ ERROR in check: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ Deployment should resolve eventlet conflicts")
        print("🚀 Ready for Railway deployment with gthread workers")
        return 0
    else:
        print("❌ DEPLOYMENT ISSUES FOUND!")
        print("🔧 Fix the issues above before deploying")
        print("💡 The RLock errors should be resolved once these are fixed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
