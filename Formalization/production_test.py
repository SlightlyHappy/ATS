"""
Comprehensive production readiness test for the HR Screening App
Tests Frontend (Vercel) → Backend (Railway) → Database (Supabase) stack
"""
import requests
import json

def test_production_stack():
    """Test the complete production stack"""
    print("🚀 PRODUCTION STACK TEST")
    print("=" * 60)
    
    # URLs
    frontend_url = "https://hrtool-5xtis8hnu-rishabh-kankashs-projects.vercel.app"
    backend_url = "https://backend-production-7fe0.up.railway.app"
    
    # Test 1: Frontend Accessibility
    print("\n1️⃣ Testing Frontend (Vercel)...")
    try:
        frontend_response = requests.get(frontend_url, timeout=10)
        if frontend_response.status_code in [200, 401]:  # 401 is expected for auth-required apps
            print("✅ Frontend is accessible")
        else:
            print(f"❌ Frontend issue: {frontend_response.status_code}")
    except Exception as e:
        print(f"❌ Frontend error: {e}")
    
    # Test 2: Backend Health
    print("\n2️⃣ Testing Backend (Railway)...")
    try:
        health_response = requests.get(f"{backend_url}/api/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ Backend is healthy")
        else:
            print(f"❌ Backend health issue: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Backend error: {e}")
    
    # Test 3: Authentication Flow
    print("\n3️⃣ Testing Authentication...")
    try:
        login_data = {
            "username": "Admin",
            "password": "Admin1232048"
        }
        headers = {
            "Origin": frontend_url,
            "Content-Type": "application/json"
        }
        
        login_response = requests.post(
            f"{backend_url}/api/auth/admin-login", 
            json=login_data, 
            headers=headers,
            timeout=10
        )
        
        if login_response.status_code == 200:
            print("✅ Authentication working")
            token = login_response.json().get('token')
            
            # Test 4: Protected Endpoint
            print("\n4️⃣ Testing Protected Endpoints...")
            auth_headers = {
                "Authorization": f"Bearer {token}",
                "Origin": frontend_url,
                "Content-Type": "application/json"
            }
            
            resumes_response = requests.get(
                f"{backend_url}/api/resumes", 
                headers=auth_headers,
                timeout=10
            )
            
            if resumes_response.status_code == 200:
                print("✅ Protected endpoints working")
            else:
                print(f"❌ Protected endpoint issue: {resumes_response.status_code}")
                
        else:
            print(f"❌ Authentication failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
    
    # Test 5: CORS Configuration
    print("\n5️⃣ Testing CORS...")
    try:
        cors_headers = {
            "Origin": frontend_url,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization"
        }
        
        cors_response = requests.options(
            f"{backend_url}/api/auth/admin-login",
            headers=cors_headers,
            timeout=10
        )
        
        if cors_response.status_code == 200:
            allowed_origin = cors_response.headers.get('Access-Control-Allow-Origin')
            if frontend_url in allowed_origin or '*' in allowed_origin:
                print("✅ CORS properly configured")
            else:
                print(f"❌ CORS issue: Origin not allowed ({allowed_origin})")
        else:
            print(f"❌ CORS preflight failed: {cors_response.status_code}")
            
    except Exception as e:
        print(f"❌ CORS error: {e}")
    
    # Test 6: Environment Configuration
    print("\n6️⃣ Testing Environment Configuration...")
    try:
        debug_response = requests.get(f"{backend_url}/api/debug", timeout=10)
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            env_vars = debug_data.get('environment_variables', {})
            
            # Check for production indicators
            railway_env = env_vars.get('RAILWAY_ENVIRONMENT')
            if railway_env:
                print(f"✅ Railway environment: {railway_env}")
            else:
                print("⚠️  Railway environment not detected")
                
            # Check Supabase configuration
            supabase_url = env_vars.get('SUPABASE_URL')
            if supabase_url and 'supabase.co' in supabase_url:
                print("✅ Supabase configured")
            else:
                print("⚠️  Supabase configuration unclear")
                
        else:
            print(f"❌ Debug endpoint failed: {debug_response.status_code}")
            
    except Exception as e:
        print(f"❌ Environment check error: {e}")
    
    print(f"\n🎯 PRODUCTION STACK TEST COMPLETE")
    print("=" * 60)
    print("✅ If all tests passed, your app is production-ready!")
    print("📱 Frontend URL:", frontend_url)
    print("🔧 Backend URL:", backend_url)

if __name__ == "__main__":
    test_production_stack()
