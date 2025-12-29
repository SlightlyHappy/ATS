"""
Test to simulate EXACT browser behavior for login
"""
import requests
import json

def simulate_browser_login():
    print("🔍 SIMULATING EXACT BROWSER LOGIN FLOW")
    print("=" * 50)
    
    frontend_url = "https://hrtool-sable.vercel.app"
    backend_url = "https://backend-production-7fe0.up.railway.app"
    
    # Step 1: Simulate visiting the login page first
    print("\n1️⃣ Simulating browser visiting login page...")
    session = requests.Session()
    
    try:
        # Visit the main page first (like a real browser)
        main_response = session.get(frontend_url, timeout=10)
        print(f"✅ Main page: {main_response.status_code}")
        
        # Visit the login page
        login_page_response = session.get(f"{frontend_url}/login", timeout=10)
        print(f"✅ Login page: {login_page_response.status_code}")
        
    except Exception as e:
        print(f"❌ Error visiting pages: {e}")
        return
    
    # Step 2: CORS Preflight (exact browser headers)
    print("\n2️⃣ Simulating CORS preflight...")
    try:
        preflight_headers = {
            "Host": "backend-production-7fe0.up.railway.app",
            "Origin": frontend_url,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
            "Referer": f"{frontend_url}/login",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        preflight_response = session.options(
            f"{backend_url}/api/auth/admin-login",
            headers=preflight_headers,
            timeout=10
        )
        
        print(f"✅ Preflight: {preflight_response.status_code}")
        
        # Check CORS headers
        cors_origin = preflight_response.headers.get('Access-Control-Allow-Origin')
        cors_methods = preflight_response.headers.get('Access-Control-Allow-Methods')
        cors_headers = preflight_response.headers.get('Access-Control-Allow-Headers')
        
        print(f"📋 CORS Origin: {cors_origin}")
        print(f"📋 CORS Methods: {cors_methods}")
        print(f"📋 CORS Headers: {cors_headers}")
        
        if cors_origin != frontend_url:
            print(f"❌ CORS Origin mismatch! Expected: {frontend_url}, Got: {cors_origin}")
            
    except Exception as e:
        print(f"❌ Preflight failed: {e}")
    
    # Step 3: Actual login request (exact browser behavior)
    print("\n3️⃣ Simulating actual login request...")
    try:
        login_headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Host": "backend-production-7fe0.up.railway.app",
            "Origin": frontend_url,
            "Pragma": "no-cache",
            "Referer": f"{frontend_url}/login",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        login_payload = {
            "username": "Admin",
            "password": "Admin1232048"
        }
        
        login_response = session.post(
            f"{backend_url}/api/auth/admin-login",
            headers=login_headers,
            json=login_payload,
            timeout=15
        )
        
        print(f"✅ Login Response: {login_response.status_code}")
        print(f"📋 Response Headers:")
        for key, value in login_response.headers.items():
            print(f"  {key}: {value}")
        
        if login_response.status_code == 200:
            print("🎉 Login successful!")
            response_data = login_response.json()
            print(f"📝 Success: {response_data.get('success')}")
            print(f"📝 Token: {response_data.get('token', 'No token')[:20]}...")
        else:
            print(f"❌ Login failed!")
            print(f"📝 Response: {login_response.text}")
            
    except requests.exceptions.ConnectTimeout:
        print("❌ Connection timeout - possible firewall/network issue")
    except requests.exceptions.ReadTimeout:
        print("❌ Read timeout - backend might be slow")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    simulate_browser_login()
