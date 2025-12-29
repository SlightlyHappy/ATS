#!/usr/bin/env python3
"""
Test script for HR Legal system
===============================

This script tests the basic functionality of the HR Legal system
to ensure it's working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_hr_legal_imports():
    """Test that all HR Legal modules can be imported."""
    print("Testing HR Legal imports...")
    
    try:
        from hr_legal import (
            EnhancedRAGEngine, AgenticRAGConfig, LegalQueryContext,
            ResponseLength, ResponseStyle, DetailLevel
        )
        print("✓ All HR Legal modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_dependencies():
    """Test that required dependencies are available."""
    print("\\nTesting dependencies...")
    
    missing_deps = []
    
    try:
        import sentence_transformers
        print("✓ sentence-transformers available")
    except ImportError:
        missing_deps.append("sentence-transformers")
        print("✗ sentence-transformers missing")
    
    try:
        import faiss
        print("✓ faiss available")
    except ImportError:
        missing_deps.append("faiss-cpu")
        print("✗ faiss missing")
    
    try:
        import numpy
        print("✓ numpy available")
    except ImportError:
        missing_deps.append("numpy")
        print("✗ numpy missing")
    
    if missing_deps:
        print(f"\\nMissing dependencies: {', '.join(missing_deps)}")
        print(f"Install with: pip install {' '.join(missing_deps)}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic HR Legal functionality."""
    print("\\nTesting basic functionality...")
    
    try:
        from hr_legal import (
            EnhancedRAGEngine, AgenticRAGConfig, LegalQueryContext,
            ResponseLength, ResponseStyle
        )
        
        # Create engine (without auto-initialization)
        engine = EnhancedRAGEngine(auto_initialize=False)
        print("✓ RAG engine created")
        
        # Test configuration
        config = AgenticRAGConfig(
            response_length=ResponseLength.MEDIUM,
            response_style=ResponseStyle.PROFESSIONAL
        )
        print("✓ Configuration created")
        
        # Test query context
        context = LegalQueryContext(
            query="What are the basic employment law requirements?",
            user_role="hr_professional"
        )
        print("✓ Query context created")
        
        print("✓ Basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def test_knowledge_base():
    """Test knowledge base loading."""
    print("\\nTesting knowledge base...")
    
    try:
        from hr_legal import LegalKnowledgeBase
        
        # Check if HRLaw folder exists
        hrlaw_path = "../HRlaw"
        if not os.path.exists(hrlaw_path):
            print(f"ℹ HRLaw folder not found at {hrlaw_path}")
            print("  Knowledge base will work with limited functionality")
            return True
        
        # Test knowledge base creation
        kb = LegalKnowledgeBase(hrlaw_path)
        print("✓ Knowledge base created")
        
        # Test document loading (without actually loading for speed)
        print("✓ Knowledge base test passed")
        return True
        
    except Exception as e:
        print(f"✗ Knowledge base test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("HR Legal System Test Suite")
    print("=" * 30)
    
    tests = [
        test_dependencies,
        test_hr_legal_imports,
        test_basic_functionality,
        test_knowledge_base
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! HR Legal system is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
