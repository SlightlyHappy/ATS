#!/usr/bin/env python3
"""
Test authentication fix
Quick test to verify authentication error handling
"""

import requests
import json

# Production URL  
BASE_URL = "https://determined-harmony-production.up.railway.app"

def test_auth_endpoints():
    """Test the problematic authentication endpoints."""
    
    endpoints_to_test = [
        '/api/v1/resumes',
        '/api/v1/analysis', 
        '/api/v1/admin/health'
    ]
    
    print("Testing authentication error handling...")
    print("=" * 50)
    
    for endpoint in endpoints_to_test:
        url = f"{BASE_URL}{endpoint}"
        
        try:
            # Test without any auth headers
            response = requests.get(url, timeout=10)
            
            print(f"Endpoint: {endpoint}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 401:
                print("✅ CORRECT - Returns 401 Unauthorized")
                try:
                    json_resp = response.json()
                    print(f"Response: {json.dumps(json_resp, indent=2)}")
                except:
                    print(f"Response: {response.text[:200]}")
            elif response.status_code == 500:
                print("❌ ERROR - Returns 500 Internal Server Error")
                print(f"Response: {response.text[:200]}")
            else:
                print(f"⚠️ UNEXPECTED - Returns {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
            print("-" * 30)
            
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            print("-" * 30)

if __name__ == "__main__":
    test_auth_endpoints()
