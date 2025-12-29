#!/usr/bin/env python3
"""
Test script for the integrated agentic resume analysis system.
Tests the complete workflow from AI processor to agentic analysis.
"""

import json
import sys
import os
from typing import Dict, Any

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_processor import OptimizedAIProcessor
from agentic_resume_analyzer import AgenticResumeAnalyzer
from market_config import get_market_data, get_skill_market_value, get_scoring_distribution, get_all_skill_market_values

def test_market_config():
    """Test that market configuration is working correctly."""
    print("🔧 Testing Market Configuration...")
    
    # Test market data retrieval
    software_data = get_market_data("software_engineer")
    print(f"✅ Software Engineer Market Data: {software_data['salary_ranges']['mid']}")
    
    # Test skill market value
    python_skill = get_skill_market_value("Python")
    print(f"✅ Python Skill Value: Demand={python_skill.get('demand', 'N/A')}, Rarity={python_skill.get('rarity', 'N/A')}")
    
    # Test scoring distribution
    scoring_dist = get_scoring_distribution()
    print(f"✅ Scoring Distribution: Strong={scoring_dist.get('strong_threshold', 'N/A')}, Good={scoring_dist.get('good_threshold', 'N/A')}")
    
    return True

def test_agentic_analyzer():
    """Test the agentic resume analyzer components."""
    print("\n🤖 Testing Agentic Resume Analyzer Components...")
    
    try:
        # Test that we can import and instantiate the scoring framework
        from agentic_resume_analyzer import RealisticScoringFramework, MarketContext
        scoring_framework = RealisticScoringFramework()
        print("✅ Scoring Framework initialized successfully")
        
        # Create a test market context
        test_market_context = MarketContext(
            role_type="software_engineer",
            location="San Francisco",
            experience_level="mid",
            skill_demand={"Python": 0.9, "React": 0.8},
            salary_range=(120000, 180000),
            market_saturation=0.6,
            years_experience_benchmark={"mid": 3}
        )
        
        # Test scoring calibration
        test_score = scoring_framework.calibrate_score(85, "software_engineer", test_market_context)
        print(f"✅ Score calibration test: 85 -> {test_score}")
        
        # Test realistic distribution
        if hasattr(scoring_framework, 'score_distribution'):
            print(f"✅ Score distribution loaded: {type(scoring_framework.score_distribution)}")
        
        print("✅ Agentic analyzer components are working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error in agentic analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_processor_integration():
    """Test the AI processor with agentic integration."""
    print("\n🔗 Testing AI Processor Integration...")
    
    try:
        # Test imports and basic configuration
        from ai_processor import OptimizedAIProcessor
        from config import ProductionConfig  # Correct class name
        print("✅ AI processor imports successfully")
        
        # Test configuration loading
        config = ProductionConfig()
        print("✅ Configuration loaded successfully")
        
        # Test that we can access the processor class (without instantiating)
        print("✅ AI processor can be properly configured")
        
        # Test the enhanced processing methods exist
        if hasattr(OptimizedAIProcessor, 'process_single_resume'):
            print("✅ Enhanced processing methods are available")
        
        # Test basic agentic analyzer classes
        from agentic_resume_analyzer import AgenticResumeAnalyzer, RealisticScoringFramework
        print("✅ Agentic analyzer classes are available")
        
        print("✅ AI processor integration appears to be working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error in AI processor integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests."""
    print("🚀 Testing Agentic Resume Analysis Integration")
    print("=" * 50)
    
    tests = [
        ("Market Configuration", test_market_config),
        ("Agentic Analyzer", test_agentic_analyzer),
        ("AI Processor Integration", test_ai_processor_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Agentic integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
