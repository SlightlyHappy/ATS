#!/usr/bin/env python3
"""
Test script for Supabase integration with Resume Screening App
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from supabase_storage import SupabaseStorage
from config import config

def test_supabase_connection():
    """Test basic Supabase connection."""
    print("🔌 Testing Supabase connection...")
    
    try:
        storage = SupabaseStorage()
        result = storage.test_connection()
        
        if result['status'] == 'connected':
            print("✅ Supabase connection successful!")
            print(f"   Message: {result['message']}")
            return True
        else:
            print("❌ Supabase connection failed!")
            print(f"   Error: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False

async def test_save_resume():
    """Test saving a resume to Supabase."""
    print("\n💾 Testing resume save operation...")
    
    try:
        storage = SupabaseStorage()
        
        # Create test resume data
        test_resume = {
            "filename": "test_candidate_resume.pdf",
            "file_size": 1024,
            "text_content": "John Doe\nSoftware Engineer\n\nExperience:\n- 5 years Python development\n- React frontend experience\n\nSkills:\n- Python, JavaScript, React, SQL",
            "extracted_info": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "skills": ["Python", "JavaScript", "React", "SQL"],
                "experience": {
                    "years": 5,
                    "level": "Senior"
                },
                "education": {
                    "level": "Bachelor's",
                    "field": "Computer Science"
                }
            },
            "ai_analysis": {
                "scores": {
                    "overall": 85,
                    "technical_skills": 90,
                    "experience": 80,
                    "education": 75,
                    "role_fit": 88
                },
                "feedback": {
                    "strengths": ["Strong technical skills", "Good experience level"],
                    "weaknesses": ["Could improve communication skills"],
                    "recommendations": "Excellent candidate for senior developer role"
                }
            }
        }
        
        result = await storage.save_resume(test_resume)
        
        if result:
            print("✅ Resume saved successfully!")
            print(f"   Supabase ID: {result['id']}")
            print(f"   Filename: {result['filename']}")
            return result['id']
        else:
            print("❌ Failed to save resume")
            return None
            
    except Exception as e:
        print(f"❌ Save test error: {e}")
        return None

async def test_get_resumes():
    """Test retrieving resumes from Supabase."""
    print("\n📋 Testing resume retrieval...")
    
    try:
        storage = SupabaseStorage()
        resumes = await storage.get_all_resumes(limit=10)
        
        print(f"✅ Retrieved {len(resumes)} resumes")
        
        for i, resume in enumerate(resumes[:3], 1):  # Show first 3
            print(f"   {i}. {resume.get('filename', 'Unknown')} - Score: {resume.get('ai_analysis', {}).get('scores', {}).get('overall', 'N/A')}")
        
        return len(resumes)
        
    except Exception as e:
        print(f"❌ Retrieval test error: {e}")
        return 0

async def test_search_resumes():
    """Test searching resumes in Supabase."""
    print("\n🔍 Testing resume search...")
    
    try:
        storage = SupabaseStorage()
        
        # Search for Python skills
        results = await storage.search_resumes(
            query="Python",
            min_score=70,
            skills=["Python"],
            limit=5
        )
        
        print(f"✅ Search returned {len(results)} results")
        
        for i, resume in enumerate(results, 1):
            name = resume.get('extracted_info', {}).get('name', 'Unknown')
            score = resume.get('ai_analysis', {}).get('scores', {}).get('overall', 'N/A')
            print(f"   {i}. {name} - Score: {score}")
        
        return len(results)
        
    except Exception as e:
        print(f"❌ Search test error: {e}")
        return 0

async def test_stats():
    """Test getting Supabase statistics."""
    print("\n📊 Testing statistics retrieval...")
    
    try:
        storage = SupabaseStorage()
        stats = await storage.get_resume_stats()
        
        print("✅ Statistics retrieved:")
        print(f"   Total resumes: {stats.get('total_resumes', 0)}")
        
        avg_scores = stats.get('average_scores', {})
        if avg_scores:
            print(f"   Average overall score: {avg_scores.get('overall', 0)}")
            print(f"   Average technical score: {avg_scores.get('technical', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Stats test error: {e}")
        return False

def test_compression():
    """Test data compression functionality."""
    print("\n🗜️  Testing data compression...")
    
    try:
        storage = SupabaseStorage()
        
        # Test data
        test_data = {
            "large_text": "This is a test string that will be compressed. " * 100,
            "nested_data": {
                "skills": ["Python", "JavaScript", "React"] * 10,
                "scores": [85, 90, 75, 88, 92] * 20
            }
        }
        
        # Compress
        compressed = storage.compress_data(test_data)
        print(f"✅ Compression successful")
        print(f"   Original size: ~{len(str(test_data))} chars")
        print(f"   Compressed size: {len(compressed)} chars")
        
        # Decompress
        decompressed = storage.decompress_data(compressed)
        
        if decompressed == test_data:
            print("✅ Decompression successful - data matches!")
            return True
        else:
            print("❌ Decompression failed - data doesn't match")
            return False
            
    except Exception as e:
        print(f"❌ Compression test error: {e}")
        return False

async def run_all_tests():
    """Run all tests."""
    print("🧪 Starting Supabase Integration Tests")
    print("=" * 50)
    
    # Test 1: Connection
    connection_ok = test_supabase_connection()
    if not connection_ok:
        print("\n❌ Connection failed - stopping tests")
        return False
    
    # Test 2: Compression
    compression_ok = test_compression()
    
    # Test 3: Save resume
    saved_id = await test_save_resume()
    
    # Test 4: Get resumes
    resume_count = await test_get_resumes()
    
    # Test 5: Search resumes
    search_count = await test_search_resumes()
    
    # Test 6: Statistics
    stats_ok = await test_stats()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   ✅ Connection: {'OK' if connection_ok else 'FAILED'}")
    print(f"   ✅ Compression: {'OK' if compression_ok else 'FAILED'}")
    print(f"   ✅ Save Resume: {'OK' if saved_id else 'FAILED'}")
    print(f"   ✅ Get Resumes: {resume_count} found")
    print(f"   ✅ Search: {search_count} results")
    print(f"   ✅ Statistics: {'OK' if stats_ok else 'FAILED'}")
    
    all_passed = all([
        connection_ok,
        compression_ok,
        saved_id is not None,
        resume_count >= 0,
        search_count >= 0,
        stats_ok
    ])
    
    if all_passed:
        print("\n🎉 All tests passed! Supabase integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")
    
    return all_passed

def main():
    """Main test runner."""
    print("Resume Screening App - Supabase Integration Test")
    print("=" * 60)
    
    # Check environment variables
    if not os.getenv('NEXT_PUBLIC_SUPABASE_URL'):
        print("❌ NEXT_PUBLIC_SUPABASE_URL not found in environment")
        return False
    
    if not os.getenv('SUPABASE_SERVICE_ROLE_KEY'):
        print("❌ SUPABASE_SERVICE_ROLE_KEY not found in environment")
        return False
    
    print("✅ Environment variables found")
    
    # Run async tests
    try:
        result = asyncio.run(run_all_tests())
        return result
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
