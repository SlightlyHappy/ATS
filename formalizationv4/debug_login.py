#!/usr/bin/env python3
"""
Debug Login Authentication Issue
Tests the exact login flow to identify where it's failing
"""

import requests
import json
import sys

# Production URL
BASE_URL = "https://determined-harmony-production.up.railway.app"

# Admin credentials
ADMIN_EMAIL = "admin@bearsystems.co.in"
ADMIN_PASSWORD = "Benzie1!Benzie1!Benzie1!Benzie1!"

def test_login_flow():
    """Test the complete login flow step by step."""
    
    print("🔍 DEBUGGING LOGIN AUTHENTICATION ISSUE")
    print("=" * 60)
    
    # Step 1: Test basic connectivity
    print("\n📡 Step 1: Testing basic connectivity...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"   Root endpoint status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Basic connectivity OK")
        else:
            print(f"   ❌ Basic connectivity failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Connection failed: {str(e)}")
        return False
    
    # Step 2: Test health endpoint
    print("\n🏥 Step 2: Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=10)
        print(f"   Health endpoint status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health check OK")
            print(f"   📊 Health data: {json.dumps(health_data, indent=2)}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check error: {str(e)}")
    
    # Step 3: Test login endpoint structure
    print("\n🔐 Step 3: Testing login endpoint with invalid data...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={},  # Empty data to test validation
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        print(f"   Login endpoint (empty data) status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 400:
            print("   ✅ Login endpoint exists and validates input")
        else:
            print(f"   ⚠️ Unexpected response for empty data: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Login endpoint test failed: {str(e)}")
    
    # Step 4: Test actual login with admin credentials
    print(f"\n🔑 Step 4: Testing actual admin login...")
    print(f"   Email: {ADMIN_EMAIL}")
    print(f"   Password: {'*' * len(ADMIN_PASSWORD)}")
    
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   Login attempt status: {response.status_code}")
        print(f"   Response headers: {dict(response.headers)}")
        print(f"   Response body: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ LOGIN SUCCESS!")
            try:
                login_response = response.json()
                print(f"   🎫 Login response: {json.dumps(login_response, indent=2)}")
                
                # Extract token if present
                if 'access_token' in login_response:
                    token = login_response['access_token']
                    print(f"   🔐 Token received: {token[:20]}...")
                    return token
                else:
                    print("   ⚠️ No access_token in response")
                    
            except json.JSONDecodeError:
                print("   ⚠️ Response is not valid JSON")
                
        elif response.status_code == 401:
            print("   ❌ LOGIN FAILED - 401 Unauthorized")
            try:
                error_data = response.json()
                print(f"   📄 Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   📄 Raw error: {response.text}")
                
        else:
            print(f"   ❌ LOGIN FAILED - Unexpected status: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Login request failed: {str(e)}")
        return False
    
    return False

def test_user_registration():
    """Test if we can register a new user (to check if the system is working)."""
    print("\n👤 Step 5: Testing user registration (system validation)...")
    
    test_user_data = {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "name": "Test User"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=test_user_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   Registration test status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code in [200, 201]:
            print("   ✅ Registration system working")
        elif response.status_code == 400:
            print("   ✅ Registration validates input (expected)")
        elif response.status_code == 409:
            print("   ✅ User already exists (system working)")
        else:
            print(f"   ⚠️ Unexpected registration response: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Registration test failed: {str(e)}")

def test_admin_endpoints():
    """Test admin-specific endpoints to see if admin user exists."""
    print("\n👑 Step 6: Testing admin endpoints...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/admin/health",
            timeout=10
        )
        
        print(f"   Admin health status: {response.status_code}")
        
        if response.status_code == 401:
            print("   ✅ Admin endpoint requires authentication (expected)")
        elif response.status_code == 403:
            print("   ⚠️ Admin endpoint returns 403 (forbidden)")
        else:
            print(f"   ⚠️ Unexpected admin endpoint response: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Admin endpoint test failed: {str(e)}")

def main():
    """Run complete debugging tests."""
    
    print("🚀 Starting comprehensive login debugging...")
    
    # Test the complete flow
    token = test_login_flow()
    test_user_registration()
    test_admin_endpoints()
    
    print("\n" + "=" * 60)
    print("🔍 DEBUGGING SUMMARY")
    print("=" * 60)
    
    if token:
        print("✅ Login successful - token received")
    else:
        print("❌ Login failed - investigating possible causes:")
        print("   1. Admin user might not exist in database")
        print("   2. Password hashing mismatch")
        print("   3. Database connection issues")
        print("   4. Environment variables not set correctly")
        print("   5. Authentication logic errors")
    
    print("\n💡 NEXT STEPS:")
    print("   1. Check Railway logs for detailed error messages")
    print("   2. Verify admin user creation in database")
    print("   3. Check environment variables on Railway")
    print("   4. Review authentication flow in auth_manager.py")

if __name__ == "__main__":
    main()
