#!/usr/bin/env python3
"""
Test script to verify frontend-backend connection after deployment fix
"""

import requests
import json
from datetime import datetime

def test_deployment_connection():
    """Test the connection between deployed frontend and backend"""
    
    frontend_url = "https://hrtool-abb96zaoy-rishabh-kankashs-projects.vercel.app"
    backend_url = "https://backend-production-7fe0.up.railway.app"
    
    print("="*70)
    print("🔍 DEPLOYMENT CONNECTION TEST")
    print("="*70)
    print(f"⏰ Test started at: {datetime.now()}")
    print(f"🌐 Frontend URL: {frontend_url}")
    print(f"🔧 Backend URL: {backend_url}")
    print()
    
    # Test 1: Backend connectivity
    print("🧪 Testing Backend Connectivity...")
    try:
        response = requests.get(f"{backend_url}/api/health", timeout=30)
        print(f"   ✅ Backend Status: {response.status_code}")
        if response.status_code == 503:
            print("   ⚠️ Backend AI services not fully initialized (normal)")
        elif response.status_code == 200:
            print("   🎉 Backend fully operational")
    except Exception as e:
        print(f"   ❌ Backend Error: {e}")
    
    print()
    
    # Test 2: Frontend accessibility
    print("🧪 Testing Frontend Accessibility...")
    try:
        response = requests.get(frontend_url, timeout=30)
        print(f"   ✅ Frontend Status: {response.status_code}")
        if response.status_code == 200:
            print("   🎉 Frontend deployed successfully")
    except Exception as e:
        print(f"   ❌ Frontend Error: {e}")
    
    print()
    
    # Test 3: CORS configuration
    print("🧪 Testing CORS Configuration...")
    try:
        headers = {
            'Origin': frontend_url,
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        response = requests.options(f"{backend_url}/api/health", headers=headers, timeout=30)
        print(f"   ✅ CORS Preflight Status: {response.status_code}")
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        print(f"   📋 CORS Headers: {cors_headers}")
        
    except Exception as e:
        print(f"   ❌ CORS Test Error: {e}")
    
    print()
    print("="*70)
    print("📋 NEXT STEPS")
    print("="*70)
    print("1. 🌐 Open your frontend URL in a browser:")
    print(f"   {frontend_url}")
    print()
    print("2. 🔍 Check browser developer console for any errors:")
    print("   - Press F12 to open developer tools")
    print("   - Go to Console tab")
    print("   - Look for any red error messages")
    print()
    print("3. 🔄 If you still see connection issues:")
    print("   - Clear browser cache (Ctrl+Shift+Del)")
    print("   - Try incognito/private browsing mode")
    print("   - Wait 2-3 more minutes for complete deployment")
    print()
    print("4. ✅ Expected behavior:")
    print("   - No more 'port 8000' error messages")
    print("   - App should load without backend connection errors")
    print("   - File upload should work (may need authentication)")

if __name__ == "__main__":
    test_deployment_connection()
