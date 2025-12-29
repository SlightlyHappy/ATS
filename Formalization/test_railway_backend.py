#!/usr/bin/env python3
"""
Test script to check Railway backend connectivity and configuration
"""

import requests
import json
import sys
from datetime import datetime

def test_backend_connectivity():
    """Test if the Railway backend is accessible"""
    
    # Backend URL from your configuration
    backend_url = "https://backend-production-7fe0.up.railway.app"
    
    print("="*60)
    print("🔍 RAILWAY BACKEND CONNECTIVITY TEST")
    print("="*60)
    print(f"⏰ Test started at: {datetime.now()}")
    print(f"🌐 Testing backend URL: {backend_url}")
    print()
    
    tests = [
        {
            "name": "Health Check",
            "endpoint": "/health",
            "expected_status": 200
        },
        {
            "name": "API Status",
            "endpoint": "/api/health",
            "expected_status": 200
        },
        {
            "name": "Root Endpoint",
            "endpoint": "/",
            "expected_status": 200
        },
        {
            "name": "Resume List",
            "endpoint": "/api/resumes",
            "expected_status": [200, 401]  # May require auth
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"🧪 Testing {test['name']}...")
        
        try:
            url = f"{backend_url}{test['endpoint']}"
            print(f"   📡 Making request to: {url}")
            
            response = requests.get(url, timeout=30)
            
            # Check if status code matches expected
            expected = test['expected_status']
            if isinstance(expected, list):
                success = response.status_code in expected
            else:
                success = response.status_code == expected
            
            result = {
                "test": test['name'],
                "url": url,
                "status_code": response.status_code,
                "success": success,
                "response_time": response.elapsed.total_seconds(),
                "headers": dict(response.headers),
                "body_preview": response.text[:200] if response.text else "No body"
            }
            
            if success:
                print(f"   ✅ SUCCESS - Status: {response.status_code}")
                print(f"   ⚡ Response time: {result['response_time']:.2f}s")
            else:
                print(f"   ❌ FAILED - Expected: {expected}, Got: {response.status_code}")
                print(f"   📄 Response: {response.text[:100]}...")
            
            results.append(result)
            
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ CONNECTION ERROR: {str(e)}")
            results.append({
                "test": test['name'],
                "url": f"{backend_url}{test['endpoint']}",
                "error": "Connection Error",
                "details": str(e),
                "success": False
            })
            
        except requests.exceptions.Timeout as e:
            print(f"   ⏰ TIMEOUT ERROR: {str(e)}")
            results.append({
                "test": test['name'],
                "url": f"{backend_url}{test['endpoint']}",
                "error": "Timeout Error",
                "details": str(e),
                "success": False
            })
            
        except Exception as e:
            print(f"   ❌ UNEXPECTED ERROR: {str(e)}")
            results.append({
                "test": test['name'],
                "url": f"{backend_url}{test['endpoint']}",
                "error": "Unexpected Error",
                "details": str(e),
                "success": False
            })
        
        print()
    
    # Summary
    print("="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    successful_tests = sum(1 for r in results if r.get('success', False))
    total_tests = len(results)
    
    print(f"✅ Successful tests: {successful_tests}/{total_tests}")
    print(f"❌ Failed tests: {total_tests - successful_tests}/{total_tests}")
    print()
    
    if successful_tests == 0:
        print("🚨 CRITICAL: Backend is completely inaccessible!")
        print("   Possible issues:")
        print("   1. Railway service is down or not deployed")
        print("   2. Incorrect URL configuration")
        print("   3. Network connectivity issues")
        print("   4. Backend failed to start properly")
    elif successful_tests < total_tests:
        print("⚠️ WARNING: Backend is partially accessible")
        print("   Some endpoints are working, others are not")
    else:
        print("🎉 SUCCESS: All backend endpoints are accessible!")
    
    print()
    print("="*60)
    print("📋 DETAILED RESULTS")
    print("="*60)
    
    for result in results:
        print(f"\n🧪 {result['test']}:")
        print(f"   URL: {result['url']}")
        
        if result.get('success'):
            print(f"   Status: ✅ {result['status_code']}")
            print(f"   Response Time: {result.get('response_time', 'N/A')}s")
        else:
            if 'error' in result:
                print(f"   Status: ❌ {result['error']}")
                print(f"   Details: {result['details']}")
            else:
                print(f"   Status: ❌ {result['status_code']}")
                print(f"   Preview: {result.get('body_preview', 'N/A')}")
    
    return results

if __name__ == "__main__":
    try:
        results = test_backend_connectivity()
        
        # Exit with error code if all tests failed
        if not any(r.get('success', False) for r in results):
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test script error: {e}")
        sys.exit(1)
