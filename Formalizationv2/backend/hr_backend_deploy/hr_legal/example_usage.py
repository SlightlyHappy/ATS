"""
Example Usage of Enhanced RAG Engine
===================================

This example demonstrates how to use the enhanced RAG engine with 
multiple AI providers and intelligent routing.
"""

import os
import sys
import logging
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from hr_legal.rag_engine import EnhancedRAGEngine
from hr_legal.ai_config import AIProviderConfig
from hr_legal.config import LegalQueryContext, AgenticRAGConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_basic_ai_providers():
    """Setup basic AI providers for demonstration."""
    
    # Example provider configurations
    providers = [
        {
            'provider_type': 'ollama',
            'model': 'qwen2.5:7b',
            'api_key': None,
            'kwargs': {'base_url': 'http://localhost:11434'}
        }
    ]
    
    # Add external providers if API keys are available
    if os.getenv('GEMINI_API_KEY'):
        providers.append({
            'provider_type': 'gemini',
            'model': 'gemini-pro',
            'api_key': os.getenv('GEMINI_API_KEY')
        })
    
    if os.getenv('OPENAI_API_KEY'):
        providers.extend([
            {
                'provider_type': 'openai',
                'model': 'gpt-3.5-turbo',
                'api_key': os.getenv('OPENAI_API_KEY')
            },
            {
                'provider_type': 'openai',
                'model': 'gpt-4o',
                'api_key': os.getenv('OPENAI_API_KEY')
            }
        ])
    
    if os.getenv('ANTHROPIC_API_KEY'):
        providers.append({
            'provider_type': 'anthropic',
            'model': 'claude-3-sonnet-20240229',
            'api_key': os.getenv('ANTHROPIC_API_KEY')
        })
    
    return providers

def demonstrate_smart_routing():
    """Demonstrate intelligent AI provider routing."""
    
    print("🤖 Enhanced RAG Engine with Smart AI Routing")
    print("=" * 50)
    
    try:
        # Initialize RAG engine with smart routing
        rag_engine = EnhancedRAGEngine(
            auto_initialize=False,
            enable_smart_routing=True
        )
        
        # Setup AI providers
        providers = setup_basic_ai_providers()
        print(f"\\n📡 Setting up {len(providers)} AI providers...")
        
        success = rag_engine.setup_multi_provider_ai(providers)
        if not success:
            print("❌ Failed to setup AI providers")
            return
        
        for provider in providers:
            print(f"   ✅ {provider['provider_type']} - {provider['model']}")
        
        # Initialize the RAG engine
        print("\\n🔧 Initializing RAG engine...")
        if not rag_engine.initialize():
            print("❌ Failed to initialize RAG engine")
            return
        
        print("✅ RAG engine initialized successfully")
        
        # Test queries with different complexities
        test_queries = [
            {
                'query': "What is employment law?",
                'complexity': 'simple',
                'description': 'Simple query - should use fast provider'
            },
            {
                'query': "Explain the key provisions of the Industrial Disputes Act 1947 regarding layoffs and retrenchments.",
                'complexity': 'medium',
                'description': 'Medium complexity - should use balanced provider'
            },
            {
                'query': "Provide a comprehensive legal analysis of compliance requirements under the Factories Act 1948, including safety protocols, working hours regulations, and penalty frameworks for violations.",
                'complexity': 'complex',
                'description': 'Complex query - should use high-quality provider'
            }
        ]
        
        print("\\n🎯 Testing Smart Routing with Different Query Complexities:")
        print("=" * 60)
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\\n{i}. {test_case['description']}")
            print(f"   Query: {test_case['query'][:80]}...")
            
            # Create query context
            query_context = LegalQueryContext(
                query=test_case['query'],
                user_id="demo_user",
                session_id="demo_session"
            )
            
            # Create configuration
            config = AgenticRAGConfig(
                retrieval_depth=5,
                similarity_threshold=0.7,
                enable_caching=True,
                response_validation=True
            )
            
            try:
                # Process query
                response = rag_engine.query(query_context, config)
                
                print(f"   ✅ Processed successfully")
                print(f"   ⏱️  Response time: {response.metadata.processing_time:.2f}s")
                print(f"   🎯 Confidence: {response.metadata.confidence_score:.2f}")
                print(f"   📝 Response length: {len(response.content)} chars")
                
                # Show first 200 characters of response
                preview = response.content[:200].replace('\\n', ' ')
                print(f"   💬 Preview: {preview}...")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        
        # Show system status
        print("\\n📊 System Status:")
        print("=" * 30)
        status = rag_engine.get_enhanced_system_status()
        
        print(f"✅ Initialized: {status['is_initialized']}")
        print(f"📚 Documents loaded: {status['system_info']['total_documents']}")
        print(f"🔄 Total queries: {status['engine_stats']['total_queries']}")
        print(f"✅ Successful: {status['engine_stats']['successful_queries']}")
        print(f"⚡ Avg response time: {status['engine_stats']['average_query_time']:.2f}s")
        
        # AI provider stats
        ai_stats = status['ai_providers']
        print(f"🧠 Smart routing: {ai_stats['smart_routing_enabled']}")
        print(f"🔀 Provider switches: {status['enhanced_stats']['ai_routing_stats']['provider_switches']}")
        
        # Cache performance
        cache_stats = status['enhanced_stats']['cache_performance']
        print(f"💾 Cache hit rate: {cache_stats['cache_hit_rate']:.2%}")
        
        print("\\n🎉 Demonstration completed successfully!")
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()

def demonstrate_performance_profiles():
    """Demonstrate different performance profiles."""
    
    print("\\n🏃 Performance Profile Comparison")
    print("=" * 40)
    
    profiles = ['speed_optimized', 'quality_optimized', 'cost_optimized', 'balanced']
    
    for profile in profiles:
        print(f"\\n📈 Profile: {profile}")
        providers = AIProviderConfig.get_providers_for_profile(profile)
        
        if providers:
            print(f"   Providers ({len(providers)}):")
            for provider in providers:
                print(f"      • {provider['provider_type']} - {provider['model']}")
        else:
            print("   ❌ No providers available for this profile")

def main():
    """Main demonstration function."""
    
    # Check available providers
    print("🔍 Checking Available AI Providers...")
    available_providers = AIProviderConfig.get_available_providers()
    
    if not available_providers:
        print("⚠️  No AI providers configured!")
        print("\\n📋 Setup Instructions:")
        instructions = AIProviderConfig.get_setup_instructions()
        
        print("\\n🔧 Quick Setup (choose one):")
        print("1. Local Ollama: ollama pull qwen2.5:7b && ollama serve")
        print("2. Gemini API: Set GEMINI_API_KEY environment variable")
        print("3. OpenAI API: Set OPENAI_API_KEY environment variable")
        print("4. Anthropic API: Set ANTHROPIC_API_KEY environment variable")
        
        return
    
    print(f"✅ Found {len(available_providers)} available providers:")
    for provider in available_providers:
        print(f"   • {provider['provider_type']} - {provider['model']}")
    
    # Demonstrate performance profiles
    demonstrate_performance_profiles()
    
    # Demonstrate smart routing
    demonstrate_smart_routing()

if __name__ == "__main__":
    main()
