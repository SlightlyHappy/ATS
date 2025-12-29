"""
Test script for local development and validation
"""

import os
import sys
import asyncio
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from supabase_manager import supabase_manager
from file_processor import file_processor
from ai_analyzer import ai_analyzer
from auth_utils import auth_manager

async def test_supabase_connection():
    """Test Supabase database connection"""
    print("🔍 Testing Supabase connection...")
    try:
        health = await supabase_manager.check_database_health()
        print(f"✅ Supabase Status: {health['status']}")
        return True
    except Exception as e:
        print(f"❌ Supabase Error: {str(e)}")
        return False

async def test_admin_auth():
    """Test admin authentication"""
    print("🔍 Testing admin authentication...")
    try:
        result = await supabase_manager.verify_admin_credentials("admin", "admin123")
        if result['success']:
            print("✅ Admin authentication working")
            return True
        else:
            print(f"❌ Admin auth failed: {result['error']}")
            return False
    except Exception as e:
        print(f"❌ Admin auth error: {str(e)}")
        return False

def test_file_processor():
    """Test file processing capabilities"""
    print("🔍 Testing file processor...")
    try:
        # Test with a simple text file (simulate PDF content)
        test_content = b"Test resume content for John Doe. Python developer with 5 years experience."
        result = file_processor.validate_file(test_content, "test.txt")
        print(f"✅ File processor validation: {result['valid']}")
        return True
    except Exception as e:
        print(f"❌ File processor error: {str(e)}")
        return False

async def test_ai_analyzer():
    """Test AI analyzer"""
    print("🔍 Testing AI analyzer...")
    try:
        health = await ai_analyzer.check_ai_service_health()
        print(f"✅ AI Analyzer Status: {health['status']}")
        
        # Test mock analysis
        sample_text = "John Doe, Software Engineer with Python and JavaScript experience"
        result = await ai_analyzer.analyze_resume(sample_text)
        if result['success']:
            print("✅ AI analysis working (mock mode)")
            return True
        else:
            print(f"❌ AI analysis failed: {result['error']}")
            return False
    except Exception as e:
        print(f"❌ AI analyzer error: {str(e)}")
        return False

def test_auth_manager():
    """Test authentication manager"""
    print("🔍 Testing authentication manager...")
    try:
        # Test token generation and verification
        token = auth_manager.generate_token("test_user_id", "test@example.com", "user")
        verification = auth_manager.verify_token(token)
        
        if verification['valid']:
            print("✅ JWT token generation and verification working")
            return True
        else:
            print(f"❌ Token verification failed: {verification['error']}")
            return False
    except Exception as e:
        print(f"❌ Auth manager error: {str(e)}")
        return False

async def run_all_tests():
    """Run all system tests"""
    print("🚀 Starting HR Resume Screening Backend Tests")
    print("=" * 50)
    
    tests = [
        ("Supabase Connection", test_supabase_connection()),
        ("Admin Authentication", test_admin_auth()),
        ("File Processor", test_file_processor()),
        ("AI Analyzer", test_ai_analyzer()),
        ("Auth Manager", test_auth_manager())
    ]
    
    results = []
    for test_name, test_coro in tests:
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All systems operational! Ready for deployment.")
    else:
        print("⚠️  Some systems need attention before deployment.")
    
    return passed == len(results)

if __name__ == "__main__":
    print("HR Resume Screening Backend - System Test")
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Supabase URL: {os.getenv('SUPABASE_URL', 'Not set')}")
    print("")
    
    # Run tests
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🚀 System ready! You can now:")
        print("1. Deploy to Railway")
        print("2. Start local development with: python app.py")
        print("3. Test API endpoints")
    else:
        print("\n🔧 Please fix the failing tests before deployment")
    
    sys.exit(0 if success else 1)
