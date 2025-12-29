"""
Test upload directly to understand the error
"""
import requests
import json

def test_upload_error():
    print("🔍 TESTING UPLOAD ERROR WITH SPECIFIC FILE")
    print("=" * 50)
    
    backend_url = "https://backend-production-7fe0.up.railway.app"
    frontend_url = "https://hrtool-sable.vercel.app"
    
    # Step 1: Login first to get auth token
    print("\n1️⃣ Logging in to get auth token...")
    session = requests.Session()
    
    try:
        login_response = session.post(
            f"{backend_url}/api/auth/admin-login",
            headers={
                "Content-Type": "application/json",
                "Origin": frontend_url
            },
            json={
                "username": "Admin",
                "password": "Admin1232048"
            },
            timeout=15
        )
        
        print(f"✅ Login Response: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ Login failed!")
            print(f"📝 Response: {login_response.text}")
            return
        
        # Get the token
        login_data = login_response.json()
        token = login_data.get('token')
        print(f"✅ Got auth token: {token[:20]}...")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Step 2: Test upload with authentication
    print("\n2️⃣ Testing file upload...")
    try:
        # Prepare upload headers
        upload_headers = {
            "Authorization": f"Bearer {token}",
            "Origin": frontend_url,
            "Referer": f"{frontend_url}/app"
        }
        
        # Create AI settings
        ai_settings = {
            "provider": "ollama",
            "model": "llama3",
            "isConfigured": True
        }
        
        # Create form data
        upload_data = {
            'aiSettings': json.dumps(ai_settings)
        }
        
        # Create a simple test file
        test_file_content = b"Test Resume\nJohn Doe\nSoftware Engineer\nPython, JavaScript"
        files = {
            'files': ('test_resume.txt', test_file_content, 'text/plain')
        }
        
        upload_response = session.post(
            f"{backend_url}/api/upload",
            headers=upload_headers,
            data=upload_data,
            files=files,
            timeout=30
        )
        
        print(f"✅ Upload Response: {upload_response.status_code}")
        print(f"📋 Response Headers:")
        for key, value in upload_response.headers.items():
            print(f"  {key}: {value}")
        
        if upload_response.status_code == 200:
            print("🎉 Upload successful!")
            response_data = upload_response.json()
            print(f"📝 Results: {json.dumps(response_data, indent=2)}")
        else:
            print(f"❌ Upload failed!")
            print(f"📝 Response: {upload_response.text}")
            
            # Check if it's an authentication issue
            if upload_response.status_code == 401:
                print("🔐 Authentication issue detected!")
            elif upload_response.status_code == 403:
                print("🚫 Permission/trial limit issue detected!")
            elif upload_response.status_code == 400:
                print("📝 Bad request - check AI settings or file format!")
            elif upload_response.status_code == 500:
                print("💥 Server error - check backend logs!")
                
    except requests.exceptions.Timeout:
        print("❌ Upload timeout - backend may be slow or unresponsive")
    except Exception as e:
        print(f"❌ Upload error: {e}")

if __name__ == "__main__":
    test_upload_error()
