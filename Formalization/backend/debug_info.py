#!/usr/bin/env python3
"""
Backend Debug Information Script
Run this to see what environment variables are needed and what's happening
"""

import os
import sys
import json
from datetime import datetime

def print_debug_header():
    print("=" * 60)
    print("BACKEND DEBUG INFORMATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print()

def check_environment_variables():
    print("ENVIRONMENT VARIABLES CHECK:")
    print("-" * 40)
    
    required_vars = [
        ("FLASK_ENV", "Should be 'production' for Railway"),
        ("FLASK_APP", "Should be 'app.py' or 'start.py'"),
        ("PORT", "Railway sets this automatically"),
        ("DATABASE_URL", "If using database"),
        ("SUPABASE_URL", "If using Supabase"),
        ("SUPABASE_ANON_KEY", "If using Supabase"),
        ("SUPABASE_SERVICE_ROLE_KEY", "If using Supabase (admin operations)"),
        ("OLLAMA_BASE_URL", "For AI processing"),
        ("SECRET_KEY", "Flask secret key for sessions"),
    ]
    
    for var_name, description in required_vars:
        value = os.getenv(var_name)
        status = "✓ SET" if value else "✗ MISSING"
        if value and len(value) > 50:
            display_value = value[:20] + "..." + value[-10:]
        else:
            display_value = value or "Not set"
        
        print(f"{var_name:25} {status:10} - {description}")
        print(f"{'':25} Value: {display_value}")
        print()

def check_file_structure():
    print("FILE STRUCTURE CHECK:")
    print("-" * 40)
    
    required_files = [
        "app.py",
        "requirements.txt",
        "Dockerfile",
        "railway.toml",
    ]
    
    for file_name in required_files:
        exists = os.path.exists(file_name)
        status = "✓ EXISTS" if exists else "✗ MISSING"
        print(f"{file_name:20} {status}")
    
    print()

def check_dependencies():
    print("DEPENDENCIES CHECK:")
    print("-" * 40)
    
    try:
        with open("requirements.txt", "r") as f:
            requirements = f.read()
        print("Requirements.txt content:")
        for line in requirements.split('\n')[:10]:  # Show first 10 lines
            if line.strip():
                print(f"  {line.strip()}")
        print("...")
    except FileNotFoundError:
        print("✗ requirements.txt not found!")
    
    print()

def check_imports():
    print("IMPORT CHECK:")
    print("-" * 40)
    
    critical_imports = [
        "flask",
        "flask_cors",
        "requests",
        "python-dotenv",
    ]
    
    for module in critical_imports:
        try:
            __import__(module.replace("-", "_"))
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module} - {str(e)}")
    
    print()

def check_railway_specific():
    print("RAILWAY SPECIFIC CHECK:")
    print("-" * 40)
    
    # Check if we're running on Railway
    railway_env = os.getenv("RAILWAY_ENVIRONMENT")
    if railway_env:
        print(f"✓ Running on Railway (Environment: {railway_env})")
    else:
        print("✗ Not detected as Railway environment")
    
    # Check Railway service info
    service_name = os.getenv("RAILWAY_SERVICE_NAME")
    if service_name:
        print(f"✓ Service name: {service_name}")
    
    # Check Railway deployment info
    deployment_id = os.getenv("RAILWAY_DEPLOYMENT_ID")
    if deployment_id:
        print(f"✓ Deployment ID: {deployment_id}")
    
    print()

def main():
    print_debug_header()
    check_environment_variables()
    check_file_structure()
    check_dependencies()
    check_imports()
    check_railway_specific()
    
    print("NEXT STEPS:")
    print("-" * 40)
    print("1. Check Railway deployment logs for errors")
    print("2. Verify all required environment variables are set in Railway dashboard")
    print("3. Ensure Dockerfile builds successfully")
    print("4. Check if the app starts without errors")
    print("5. Verify the health endpoint responds")
    print()
    print("To access this debug info via web:")
    print("Add a route in app.py: @app.route('/debug')")

if __name__ == "__main__":
    main()
