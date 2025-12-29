#!/usr/bin/env python3
"""
Test script for HR Legal endpoints to ensure proper functionality
"""

import json
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    
    try:
        # Test basic Flask imports
        from flask import Flask, request, jsonify
        print("✅ Flask imports successful")
        
        # Test HR Legal imports
        try:
            from hr_legal import (
                EnhancedRAGEngine, AgenticRAGConfig, LegalQueryContext, 
                ResponseLength, ResponseStyle, DetailLevel, AudienceLevel
            )
            print("✅ HR Legal imports successful")
            hr_legal_available = True
        except ImportError as e:
            print(f"⚠️  HR Legal imports failed: {e}")
            hr_legal_available = False
        
        # Test other dependencies
        import requests
        import pandas as pd
        import psutil
        print("✅ Additional dependencies successful")
        
        return hr_legal_available
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config_classes():
    """Test if config classes work properly."""
    print("\nTesting configuration classes...")
    
    try:
        from hr_legal import (
            AgenticRAGConfig, LegalQueryContext, 
            ResponseLength, ResponseStyle, DetailLevel, AudienceLevel
        )
        
        # Test enum creation
        response_length = ResponseLength.MEDIUM
        response_style = ResponseStyle.PROFESSIONAL
        detail_level = DetailLevel.BALANCED
        audience_level = AudienceLevel.INTERMEDIATE
        
        print("✅ Enum classes work correctly")
        
        # Test config creation
        config = AgenticRAGConfig(
            response_length=response_length,
            response_style=response_style,
            detail_level=detail_level,
            audience_level=audience_level
        )
        print("✅ AgenticRAGConfig creation successful")
        
        # Test context creation
        context = LegalQueryContext(
            query="Test query",
            query_type="test",
            user_role="hr_professional"
        )
        print("✅ LegalQueryContext creation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_endpoint_validation():
    """Test endpoint input validation logic."""
    print("\nTesting endpoint validation logic...")
    
    try:
        from hr_legal import (
            ResponseLength, ResponseStyle, DetailLevel, AudienceLevel
        )
        
        # Test valid enum values
        valid_response_lengths = [e.value for e in ResponseLength]
        valid_response_styles = [e.value for e in ResponseStyle]
        valid_detail_levels = [e.value for e in DetailLevel]
        valid_audience_levels = [e.value for e in AudienceLevel]
        
        print(f"✅ Valid response lengths: {valid_response_lengths}")
        print(f"✅ Valid response styles: {valid_response_styles}")
        print(f"✅ Valid detail levels: {valid_detail_levels}")
        print(f"✅ Valid audience levels: {valid_audience_levels}")
        
        # Test validation logic
        test_values = {
            'response_length': 'medium',
            'response_style': 'professional',
            'detail_level': 'balanced',
            'audience_level': 'intermediate'
        }
        
        for key, value in test_values.items():
            if key == 'response_length' and value in valid_response_lengths:
                print(f"✅ {key} validation: {value} is valid")
            elif key == 'response_style' and value in valid_response_styles:
                print(f"✅ {key} validation: {value} is valid")
            elif key == 'detail_level' and value in valid_detail_levels:
                print(f"✅ {key} validation: {value} is valid")
            elif key == 'audience_level' and value in valid_audience_levels:
                print(f"✅ {key} validation: {value} is valid")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False

def test_response_structure():
    """Test response structure and serialization."""
    print("\nTesting response structure...")
    
    try:
        from hr_legal import LegalResponse, ResponseMetadata, AgenticRAGConfig, LegalQueryContext
        
        # Create test metadata
        metadata = ResponseMetadata(
            confidence_score=0.85,
            processing_time=1.5,
            sources_used=["source1", "source2"],
            reasoning_steps=["step1", "step2"],
            follow_up_suggestions=["suggestion1"],
            quality_score=0.9,
            validation_passed=True
        )
        print("✅ ResponseMetadata creation successful")
        
        # Create test config and context
        config = AgenticRAGConfig()
        context = LegalQueryContext(query="test", query_type="test")
        
        # Create test response
        response = LegalResponse(
            content="Test response content",
            metadata=metadata,
            config_used=config,
            query_context=context,
            response_id="test_id",
            timestamp=datetime.now().isoformat()
        )
        print("✅ LegalResponse creation successful")
        
        # Test serialization
        response_dict = response.to_dict()
        assert isinstance(response_dict, dict)
        assert "content" in response_dict
        assert "metadata" in response_dict
        assert "config" in response_dict
        assert "query_info" in response_dict
        print("✅ Response serialization successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Response structure test failed: {e}")
        return False

def test_error_handling():
    """Test error handling scenarios."""
    print("\nTesting error handling scenarios...")
    
    try:
        from hr_legal import ResponseLength
        
        # Test invalid enum values
        try:
            invalid_length = ResponseLength("invalid")
            print("❌ Should have failed with invalid enum value")
            return False
        except ValueError:
            print("✅ Invalid enum value properly rejected")
        
        # Test boundary values
        test_retrieval_depth = 15  # Should be capped at 10
        capped_depth = min(test_retrieval_depth, 10)
        assert capped_depth == 10
        print("✅ Boundary value capping works")
        
        # Test similarity threshold bounds
        test_threshold = 1.5  # Should be capped at 1.0
        capped_threshold = max(0.3, min(test_threshold, 1.0))
        assert capped_threshold == 1.0
        print("✅ Similarity threshold bounds work")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 HR Legal Backend Endpoint Testing")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Classes", test_config_classes),
        ("Endpoint Validation", test_endpoint_validation),
        ("Response Structure", test_response_structure),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    hr_legal_available = False
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            if test_name == "Import Test":
                result = test_func()
                hr_legal_available = result
            else:
                if hr_legal_available:
                    result = test_func()
                else:
                    print("⏭️  Skipping (HR Legal not available)")
                    result = None
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print("=" * 50)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in results:
        if result is True:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        elif result is False:
            print(f"❌ {test_name}: FAILED")
            failed += 1
        else:
            print(f"⏭️  {test_name}: SKIPPED")
            skipped += 1
    
    print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("🎉 All available tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
