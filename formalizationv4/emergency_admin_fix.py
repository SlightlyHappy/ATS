#!/usr/bin/env python3
"""
EMERGENCY ADMIN USER CREATION
Creates the admin user directly - to be run on Railway
"""

import requests
import json

BASE_URL = "https://determined-harmony-production.up.railway.app"

def create_admin_via_api():
    """Create admin user by calling the Railway API directly."""
    print("🚨 EMERGENCY ADMIN USER CREATION")
    print("=" * 50)
    
    # First, let's try a direct database fix by triggering admin creation
    print("\n1. Triggering admin creation via Railway...")
    
    # We'll create a script that Railway can execute
    railway_command = '''
import os
import sys
sys.path.append('/app')

from app import create_app, db
from app.models import User
from app.services.auth_manager import auth_manager

app = create_app()
with app.app_context():
    admin_email = "admin@bearsystems.co.in"
    admin_password = "Benzie1!Benzie1!Benzie1!Benzie1!"
    
    # Delete existing admin if any (in case there's a corrupted one)
    existing = User.query.filter_by(email=admin_email).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        print(f"Deleted existing admin: {admin_email}")
    
    # Create fresh admin user
    admin = User(
        email=admin_email,
        username="admin",
        password_hash=auth_manager.hash_password(admin_password),
        first_name="System",
        last_name="Administrator", 
        is_admin=True,
        is_active=True,
        credits_balance=10000
    )
    
    db.session.add(admin)
    db.session.commit()
    print(f"✅ Admin user created successfully: {admin_email}")
    
    # Verify creation
    verify_admin = User.query.filter_by(email=admin_email).first()
    if verify_admin:
        print(f"✅ Admin user verified in database")
        print(f"   ID: {verify_admin.id}")
        print(f"   Email: {verify_admin.email}")
        print(f"   Is Admin: {verify_admin.is_admin}")
        print(f"   Is Active: {verify_admin.is_active}")
    else:
        print("❌ Admin user verification failed")
'''
    
    print("💡 RAILWAY FIX COMMAND:")
    print("Run this command on Railway:")
    print("=" * 50)
    print("npx @railway/cli run 'python3 -c \"" + railway_command.replace('\n', '\\n').replace('"', '\\"') + "\"'")
    print("=" * 50)
    
    # Alternative: Create a temporary file for Railway
    print("\n💡 ALTERNATIVE: Create fix_admin.py and run on Railway:")
    with open('fix_admin.py', 'w') as f:
        f.write(railway_command)
    
    print("Created fix_admin.py - upload this to Railway and run:")
    print("npx @railway/cli run 'python3 fix_admin.py'")
    
    # Test login after fix
    print("\n🔍 After running the fix, test login with:")
    print(f"Email: admin@bearsystems.co.in")
    print(f"Password: Benzie1!Benzie1!Benzie1!Benzie1!")

def test_login_after_fix():
    """Test login after the fix is applied."""
    print("\n🧪 Testing login after fix...")
    
    login_data = {
        "email": "admin@bearsystems.co.in",
        "password": "Benzie1!Benzie1!Benzie1!Benzie1!"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Login test status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ LOGIN SUCCESS! Admin user is now working!")
            login_data = response.json()
            print(f"🎫 Token received: {login_data.get('access_token', 'N/A')[:20]}...")
        else:
            print(f"❌ Login still failing: {response.text}")
            
    except Exception as e:
        print(f"❌ Login test error: {str(e)}")

if __name__ == "__main__":
    create_admin_via_api()
    test_login_after_fix()
