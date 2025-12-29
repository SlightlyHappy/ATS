"""
Comprehensive debugging test for Network Error on Vercel login
"""
import requests
import json

def debug_login_issue():
    frontend_url = "https://hrtool-sable.vercel.app"
    backend_url = "https://backend-production-7fe0.up.railway.app"
    
    print("🔍 DEBUGGING NETWORK ERROR - Comprehensive Test")
    print("=" * 60)
    
    # Test 1: Basic connectivity
    print("\n1️⃣ Testing basic connectivity...")
    try:
        frontend_resp = requests.get(frontend_url, timeout=10)
        print(f"✅ Frontend accessible: {frontend_resp.status_code}")
        
        backend_resp = requests.get(f"{backend_url}/api/health", timeout=10)
        print(f"✅ Backend health: {backend_resp.status_code}")
    except Exception as e:
        print(f"❌ Basic connectivity failed: {e}")
        return
    
    # Test 2: CORS preflight specifically for login endpoint
    print("\n2️⃣ Testing CORS preflight for login endpoint...")
    try:
        preflight_headers = {
            "Origin": frontend_url,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization"
        }
        
        preflight_resp = requests.options(
            f"{backend_url}/api/auth/admin-login", 
            headers=preflight_headers,
            timeout=10
        )
        
        print(f"✅ OPTIONS Response: {preflight_resp.status_code}")
        print("📋 CORS Headers:")
        for key, value in preflight_resp.headers.items():
            if 'access-control' in key.lower():
                print(f"  {key}: {value}")
                
    except Exception as e:
        print(f"❌ CORS preflight failed: {e}")
    
    # Test 3: Actual login request with exact browser headers
    print("\n3️⃣ Testing login with browser-like headers...")
    try:
        login_headers = {
            "Origin": frontend_url,
            "Referer": f"{frontend_url}/login",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site"
        }
        
        login_data = {
            "username": "Admin",
            "password": "Admin1232048"
        }
        
        login_resp = requests.post(
            f"{backend_url}/api/auth/admin-login",
            json=login_data,
            headers=login_headers,
            timeout=15
        )
        
        print(f"✅ Login Response: {login_resp.status_code}")
        print(f"📋 Response Headers:")
        for key, value in login_resp.headers.items():
            if 'access-control' in key.lower() or key.lower() in ['content-type', 'server']:
                print(f"  {key}: {value}")
        
        if login_resp.status_code == 200:
            print("🎉 Login successful with browser headers!")
            resp_data = login_resp.json()
            print(f"📝 Token received: {resp_data.get('token', 'No token')[:20]}...")
        else:
            print(f"❌ Login failed: {login_resp.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - possible network issue")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Login request failed: {e}")
    
    # Test 4: Check if there are any SSL/TLS issues
    print("\n4️⃣ Testing SSL/TLS configuration...")
    try:
        import ssl
        import socket
        
        # Test SSL connection to backend
        context = ssl.create_default_context()
        with socket.create_connection(("backend-production-7fe0.up.railway.app", 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname="backend-production-7fe0.up.railway.app") as ssock:
                print(f"✅ SSL connection successful")
                print(f"📝 SSL version: {ssock.version()}")
                
    except Exception as e:
        print(f"❌ SSL test failed: {e}")
    
    # Test 5: Check Railway backend logs endpoint
    print("\n5️⃣ Testing Railway backend debug endpoint...")
    try:
        debug_resp = requests.get(f"{backend_url}/api/debug", timeout=10)
        print(f"✅ Debug endpoint: {debug_resp.status_code}")
        if debug_resp.status_code == 200:
            debug_data = debug_resp.json()
            print(f"📝 Backend environment: {debug_data.get('environment_variables', {}).get('RAILWAY_ENVIRONMENT', 'unknown')}")
            print(f"📝 Python version: {debug_data.get('python_version', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Debug endpoint failed: {e}")
    
    # Test 6: Test from different origin to isolate CORS issue
    print("\n6️⃣ Testing from different origin...")
    try:
        alt_headers = {
            "Origin": "https://httpbin.org",  # Different origin
            "Content-Type": "application/json"
        }
        
        alt_resp = requests.post(
            f"{backend_url}/api/auth/admin-login",
            json=login_data,
            headers=alt_headers,
            timeout=10
        )
        
        print(f"✅ Different origin response: {alt_resp.status_code}")
        if alt_resp.status_code != 200:
            print(f"📝 Expected CORS rejection: {alt_resp.text}")
        
    except Exception as e:
        print(f"❌ Different origin test failed: {e}")

if __name__ == "__main__":
    debug_login_issue()
