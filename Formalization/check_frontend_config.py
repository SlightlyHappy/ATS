"""
Test the actual API URL that the deployed frontend is using
"""
import requests
import re

def check_frontend_api_config():
    frontend_url = "https://hrtool-sable.vercel.app"
    
    print("🔍 CHECKING FRONTEND API CONFIGURATION")
    print("=" * 50)
    
    try:
        # Get the frontend HTML and JavaScript
        response = requests.get(frontend_url, timeout=10)
        print(f"✅ Frontend Status: {response.status_code}")
        
        # Look for any API URL references in the HTML/JS
        content = response.text
        
        # Search for environment variables or API URLs in the content
        api_patterns = [
            r'REACT_APP_API_URL["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'process\.env\.REACT_APP_API_URL',
            r'backend-production.*\.railway\.app',
            r'localhost:8000',
            r'http://localhost',
            r'baseURL["\']?\s*[:=]\s*["\']([^"\']+)["\']'
        ]
        
        print("\n📋 Searching for API configuration in frontend...")
        found_configs = []
        
        for pattern in api_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                for match in matches:
                    found_configs.append(f"Found: {match}")
                    print(f"✅ {pattern}: {match}")
        
        if not found_configs:
            print("⚠️  No obvious API URLs found in frontend HTML (this is normal for production builds)")
        
        # Check if there are any error messages in the HTML
        error_patterns = [
            r'Network Error',
            r'CORS',
            r'fetch.*failed',
            r'XMLHttpRequest.*error'
        ]
        
        print("\n🔍 Checking for error indicators...")
        for pattern in error_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"⚠️  Found: {pattern}")
            else:
                print(f"✅ No '{pattern}' found")
        
        # Test if we can fetch the main JS bundle and check for API config
        js_links = re.findall(r'src="([^"]*\.js[^"]*)"', content)
        
        if js_links:
            print(f"\n📦 Found {len(js_links)} JavaScript files")
            
            # Check the main JS file for API configuration
            for js_link in js_links[:2]:  # Check first 2 JS files
                if js_link.startswith('/'):
                    js_url = frontend_url + js_link
                else:
                    js_url = js_link
                
                try:
                    js_response = requests.get(js_url, timeout=5)
                    js_content = js_response.text
                    
                    # Look for API URL in JS
                    if 'backend-production' in js_content:
                        print(f"✅ Found Railway backend URL in {js_link}")
                    elif 'localhost:8000' in js_content:
                        print(f"❌ Found localhost URL in {js_link} - THIS IS THE PROBLEM!")
                    elif 'REACT_APP_API_URL' in js_content:
                        print(f"✅ Found REACT_APP_API_URL reference in {js_link}")
                    
                except Exception as e:
                    print(f"⚠️  Could not fetch {js_link}: {e}")
        
        print(f"\n🔧 Environment Check Complete")
        
    except Exception as e:
        print(f"❌ Error checking frontend: {e}")

if __name__ == "__main__":
    check_frontend_api_config()
