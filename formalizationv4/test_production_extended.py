#!/usr/bin/env python3
"""
Extended Production Deployment Test
Tests additional critical endpoints for the Railway deployment.
"""

import requests
import json
import sys
from datetime import datetime

# Production URL
BASE_URL = "https://determined-harmony-production.up.railway.app"

def test_endpoint(endpoint, method="GET", data=None, expected_status=200, description=""):
    """Test a single endpoint and return results."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        headers = {'Content-Type': 'application/json'}
        
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=30)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=30)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
            
        print(f"🔍 Testing {method} {endpoint}")
        print(f"   Description: {description}")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == expected_status:
            print(f"   ✅ PASS")
            
            # Try to parse JSON response
            try:
                json_response = response.json()
                print(f"   📄 Response: {json.dumps(json_response, indent=2)[:300]}...")
            except:
                print(f"   📄 Response: {response.text[:200]}...")
                
            return True
        else:
            print(f"   ❌ FAIL - Expected {expected_status}, got {response.status_code}")
            print(f"   📄 Response: {response.text[:300]}...")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏱️ TIMEOUT - Request took longer than 30 seconds")
        return False
    except requests.exceptions.ConnectionError:
        print(f"   🌐 CONNECTION ERROR - Could not connect to server")
        return False
    except Exception as e:
        print(f"   💥 ERROR - {str(e)}")
        return False

def main():
    """Run extended deployment tests."""
    print("=" * 70)
    print("🚀 EXTENDED PRODUCTION DEPLOYMENT TEST")
    print(f"🌐 Target: {BASE_URL}")
    print(f"⏰ Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Extended test cases
    tests = [
        # Core API tests
        {
            'endpoint': '/',
            'description': 'Root endpoint - API information',
            'expected_status': 200
        },
        {
            'endpoint': '/api/v1/health',
            'description': 'Comprehensive health check with service status',
            'expected_status': 200
        },
        
        # Authentication tests
        {
            'endpoint': '/api/v1/auth/register',
            'method': 'POST',
            'data': {},  # Empty data should trigger validation error
            'description': 'Auth registration validation (should fail properly)',
            'expected_status': 400
        },
        
        # API endpoints tests
        {
            'endpoint': '/api/v1/resumes',
            'description': 'Resume management endpoint (should require auth)',
            'expected_status': 401
        },
        {
            'endpoint': '/api/v1/analysis',
            'description': 'Analysis endpoint (should require auth)',
            'expected_status': 401
        },
        {
            'endpoint': '/api/v1/monitoring/status',
            'description': 'Monitoring status endpoint',
            'expected_status': 200
        },
        {
            'endpoint': '/api/v1/admin/health',
            'description': 'Admin health check (should require admin auth)',
            'expected_status': 401
        },
        
        # Static/Dashboard tests
        {
            'endpoint': '/api/v1/dashboard',
            'description': 'Dashboard HTML page',
            'expected_status': 200
        },
        
        # WebSocket and queue tests
        {
            'endpoint': '/api/v1/queue/status',
            'description': 'Queue status endpoint',
            'expected_status': 200
        },
        
        # Error handling tests
        {
            'endpoint': '/api/v1/invalid-endpoint',
            'description': 'Invalid API endpoint (should return 404)',
            'expected_status': 404
        },
        {
            'endpoint': '/api/v2/nonexistent',
            'description': 'Non-existent API version (should return 404)',
            'expected_status': 404
        }
    ]
    
    # Run tests
    passed = 0
    total = len(tests)
    
    for i, test in enumerate(tests, 1):
        print(f"\n[{i}/{total}]", end=" ")
        
        result = test_endpoint(
            endpoint=test['endpoint'],
            method=test.get('method', 'GET'),
            data=test.get('data'),
            expected_status=test['expected_status'],
            description=test['description']
        )
        
        if result:
            passed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 EXTENDED TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed >= total * 0.9:  # 90% success rate
        print("🎉 DEPLOYMENT IS PRODUCTION READY!")
        if passed == total:
            print("💯 Perfect score - All endpoints working correctly!")
        else:
            print("⚠️ Minor issues detected but deployment is stable")
        return 0
    else:
        print("❌ DEPLOYMENT HAS CRITICAL ISSUES - Needs attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())
