#!/usr/bin/env python3
"""
Check Admin User Status
Tests if admin user exists and can be created
"""

import requests
import json
import time

BASE_URL = "https://determined-harmony-production.up.railway.app"
ADMIN_EMAIL = "admin@bearsystems.co.in"
ADMIN_PASSWORD = "Benzie1!Benzie1!Benzie1!Benzie1!"

def test_admin_creation():
    """Test if we can recreate the admin user."""
    print("🔧 TESTING ADMIN USER CREATION")
    print("=" * 50)
    
    # First, try to register the admin user (this might tell us if it exists)
    print("\n👤 Testing admin user registration...")
    
    admin_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "name": "System Administrator"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=admin_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   Admin registration status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 201:
            print("   ✅ Admin user created successfully!")
            print("   💡 This means admin user didn't exist before")
            
            # Now try to login with the newly created admin
            print("\n🔑 Testing login with newly created admin...")
            time.sleep(2)  # Give it a moment
            
            login_response = requests.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"   Login status: {login_response.status_code}")
            print(f"   Login response: {login_response.text}")
            
            if login_response.status_code == 200:
                print("   ✅ LOGIN SUCCESS after creation!")
                return True
            else:
                print("   ❌ Still can't login after creation")
                
        elif response.status_code == 409:
            print("   ⚠️ Admin user already exists")
            print("   💡 This means there's a password mismatch issue")
            
        elif response.status_code == 400:
            print("   ⚠️ Validation error in registration")
            try:
                error_data = response.json()
                print(f"   📄 Validation details: {json.dumps(error_data, indent=2)}")
            except:
                pass
                
        else:
            print(f"   ❌ Unexpected registration response: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Admin registration test failed: {str(e)}")
    
    return False

def test_case_sensitivity():
    """Test different email case variations."""
    print("\n📧 Testing email case sensitivity...")
    
    email_variations = [
        "admin@bearsystems.co.in",
        "Admin@bearsystems.co.in", 
        "ADMIN@BEARSYSTEMS.CO.IN",
        "admin@Bearsystems.co.in"
    ]
    
    for email in email_variations:
        print(f"\n   Testing: {email}")
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={"email": email, "password": ADMIN_PASSWORD},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ SUCCESS with: {email}")
                return email
            else:
                print(f"   ❌ Failed: {response.json().get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Error testing {email}: {str(e)}")
    
    return None

def main():
    """Run admin user debugging."""
    print("🚀 ADMIN USER DEBUGGING")
    print("=" * 50)
    
    # Test if we can create admin user
    admin_created = test_admin_creation()
    
    if not admin_created:
        # Test case sensitivity
        working_email = test_case_sensitivity()
        
        if working_email:
            print(f"\n✅ Found working email: {working_email}")
        else:
            print(f"\n❌ No email variation worked")
    
    print("\n" + "=" * 50)
    print("🎯 CONCLUSIONS:")
    
    if admin_created:
        print("✅ Admin user was missing from database - now created and working")
        print("💡 Root cause: Admin user creation didn't happen during app startup")
    else:
        print("❌ Admin user issue persists")
        print("💡 Possible causes:")
        print("   1. Password hashing algorithm mismatch")
        print("   2. Database/environment variable issues") 
        print("   3. Admin creation logic not running properly")
        print("\n🔧 IMMEDIATE FIX NEEDED:")
        print("   Check admin user creation in Railway startup logs")

if __name__ == "__main__":
    main()
