"""
Test upload with proper PDF filename
"""
import requests
import json

def test_pdf_upload():
    print("🔍 TESTING PDF UPLOAD WITH PROPER FILENAME")
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
        
        if login_response.status_code != 200:
            print(f"❌ Login failed!")
            return
        
        token = login_response.json().get('token')
        print(f"✅ Got auth token")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Step 2: Test the problematic filename
    print("\n2️⃣ Testing problematic filename...")
    problematic_filename = "CV_(Archana H Vishwakarma)_compressed (1).pdf"
    
    # Test the allowed_file function logic
    has_dot = '.' in problematic_filename
    if has_dot:
        extension = problematic_filename.rsplit('.', 1)[1].lower()
        allowed_extensions = {'pdf', 'docx', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
        is_allowed = extension in allowed_extensions
        
        print(f"📝 Filename: {problematic_filename}")
        print(f"📝 Has dot: {has_dot}")
        print(f"📝 Extension: '{extension}'")
        print(f"📝 Is allowed: {is_allowed}")
        print(f"📝 Allowed extensions: {allowed_extensions}")
    
    # Step 3: Test upload with problematic filename
    try:
        upload_headers = {
            "Authorization": f"Bearer {token}",
            "Origin": frontend_url
        }
        
        ai_settings = {
            "provider": "ollama",
            "model": "llama3",
            "isConfigured": True
        }
        
        upload_data = {
            'aiSettings': json.dumps(ai_settings)
        }
        
        # Create a test PDF content
        test_pdf_content = b"%PDF-1.4\nTest PDF content\nJohn Doe\nSoftware Engineer"
        files = {
            'files': (problematic_filename, test_pdf_content, 'application/pdf')
        }
        
        upload_response = session.post(
            f"{backend_url}/api/upload",
            headers=upload_headers,
            data=upload_data,
            files=files,
            timeout=30
        )
        
        print(f"\n3️⃣ Upload Response: {upload_response.status_code}")
        
        if upload_response.status_code == 200:
            print("🎉 Upload successful!")
            response_data = upload_response.json()
            print(f"📝 Results: {json.dumps(response_data, indent=2)}")
        else:
            print(f"❌ Upload failed!")
            print(f"📝 Response: {upload_response.text}")
                
    except Exception as e:
        print(f"❌ Upload error: {e}")

if __name__ == "__main__":
    test_pdf_upload()
