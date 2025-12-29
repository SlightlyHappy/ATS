"""
AI Provider Setup Script
========================

Helper script to configure and test multiple AI providers for the RAG engine.
"""

import os
import sys
import time
import logging
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from hr_legal.ai_config import AIProviderConfig, AIRoutingConfig
from hr_legal.rag_engine import EnhancedRAGEngine

logger = logging.getLogger(__name__)

class AISetupManager:
    """Manager for setting up and testing AI providers."""
    
    def __init__(self):
        self.rag_engine = None
        self.available_providers = []
        self.setup_status = {}
    
    def check_environment_variables(self) -> Dict[str, bool]:
        """Check which AI provider API keys are available."""
        env_status = {
            'OPENAI_API_KEY': bool(os.getenv('OPENAI_API_KEY')),
            'ANTHROPIC_API_KEY': bool(os.getenv('ANTHROPIC_API_KEY')),
            'GEMINI_API_KEY': bool(os.getenv('GEMINI_API_KEY')),
            'TOGETHER_API_KEY': bool(os.getenv('TOGETHER_API_KEY'))
        }
        
        print("\\n🔑 API Key Status:")
        print("=" * 40)
        for key, available in env_status.items():
            status = "✅ Available" if available else "❌ Missing"
            print(f"{key}: {status}")
        
        return env_status
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Check which AI provider libraries are installed."""
        deps_status = {}
        
        # Check OpenAI
        try:
            import openai
            deps_status['openai'] = True
        except ImportError:
            deps_status['openai'] = False
        
        # Check Anthropic
        try:
            import anthropic
            deps_status['anthropic'] = True
        except ImportError:
            deps_status['anthropic'] = False
        
        # Check Google Generative AI
        try:
            import google.generativeai
            deps_status['google-generativeai'] = True
        except ImportError:
            deps_status['google-generativeai'] = False
        
        # Check requests (for Together AI)
        try:
            import requests
            deps_status['requests'] = True
        except ImportError:
            deps_status['requests'] = False
        
        # Check Ollama (always available if server is running)
        deps_status['ollama'] = self._test_ollama_connection()
        
        print("\\n📦 Dependencies Status:")
        print("=" * 40)
        for dep, available in deps_status.items():
            status = "✅ Installed" if available else "❌ Missing"
            print(f"{dep}: {status}")
        
        return deps_status
    
    def _test_ollama_connection(self) -> bool:
        """Test connection to Ollama server."""
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=300)  # Increased from 5 to 30 seconds
            return response.status_code == 200
        except:
            return False
    
    def setup_rag_engine_with_providers(self, performance_profile: str = 'balanced') -> bool:
        """Setup RAG engine with available AI providers."""
        try:
            print(f"\\n🚀 Setting up RAG engine with '{performance_profile}' profile...")
            
            # Get available providers for the selected profile
            providers = AIProviderConfig.get_providers_for_profile(performance_profile)
            
            if not providers:
                print("❌ No AI providers available. Please configure API keys.")
                return False
            
            # Initialize RAG engine with smart routing
            self.rag_engine = EnhancedRAGEngine(
                auto_initialize=False,
                enable_smart_routing=True
            )
            
            # Setup multiple providers
            success = self.rag_engine.setup_multi_provider_ai(providers)
            
            if success:
                print(f"✅ Successfully configured {len(providers)} AI providers")
                for provider in providers:
                    print(f"   • {provider['provider_type']} - {provider['model']}")
                
                # Initialize the RAG engine
                if self.rag_engine.initialize():
                    print("✅ RAG engine initialized successfully")
                    return True
                else:
                    print("❌ RAG engine initialization failed")
                    return False
            else:
                print("❌ Failed to setup multi-provider AI")
                return False
                
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def test_providers(self) -> Dict[str, Dict[str, Any]]:
        """Test all configured AI providers."""
        if not self.rag_engine or not self.rag_engine.multi_ai_processor:
            print("❌ RAG engine not properly configured")
            return {}
        
        print("\\n🧪 Testing AI Providers:")
        print("=" * 40)
        
        test_results = {}
        test_prompt = "What is employment law? Respond with a brief explanation."
        
        for provider_key, provider in self.rag_engine.multi_ai_processor.providers.items():
            print(f"\\nTesting {provider_key}...")
            
            try:
                start_time = time.time()
                response = provider.generate_response(test_prompt, format_json=False)
                response_time = time.time() - start_time
                
                test_results[provider_key] = {
                    'status': 'success',
                    'response_time': response_time,
                    'response_length': len(response.get('response', '')),
                    'error': None
                }
                
                print(f"   ✅ Success ({response_time:.2f}s)")
                
            except Exception as e:
                test_results[provider_key] = {
                    'status': 'failed',
                    'response_time': None,
                    'response_length': 0,
                    'error': str(e)
                }
                print(f"   ❌ Failed: {e}")
        
        return test_results
    
    def test_smart_routing(self) -> bool:
        """Test intelligent routing with different query complexities."""
        if not self.rag_engine:
            print("❌ RAG engine not configured")
            return False
        
        print("\\n🎯 Testing Smart Routing:")
        print("=" * 40)
        
        # Test queries of different complexities
        test_queries = {
            'simple': "What is HR?",
            'medium': "What are the key employment laws in India that HR professionals should know?",
            'complex': "Provide a comprehensive analysis of the compliance requirements under the Industrial Disputes Act, 1947, including dispute resolution mechanisms, notice periods, and penalties for non-compliance."
        }
        
        try:
            from hr_legal.config import LegalQueryContext, AgenticRAGConfig
            
            for complexity, query in test_queries.items():
                print(f"\\nTesting {complexity} query...")
                print(f"Query: {query}")
                
                # Create query context and config
                query_context = LegalQueryContext(
                    query=query,
                    user_id="test_user",
                    session_id="test_session"
                )
                
                config = AgenticRAGConfig(
                    retrieval_depth=3,
                    similarity_threshold=0.7,
                    enable_caching=False  # Disable for testing
                )
                
                start_time = time.time()
                response = self.rag_engine.query(query_context, config)
                response_time = time.time() - start_time
                
                print(f"   ✅ Processed in {response_time:.2f}s")
                print(f"   Confidence: {response.metadata.confidence_score:.2f}")
                print(f"   Response length: {len(response.content)} chars")
                
            return True
            
        except Exception as e:
            print(f"❌ Smart routing test failed: {e}")
            return False
    
    def print_setup_instructions(self):
        """Print setup instructions for missing providers."""
        print("\\n📋 Setup Instructions:")
        print("=" * 50)
        
        instructions = AIProviderConfig.get_setup_instructions()
        env_status = self.check_environment_variables()
        
        for provider, instruction in instructions.items():
            if provider == 'openai' and not env_status.get('OPENAI_API_KEY'):
                print(f"\\n🔧 OpenAI Setup:{instruction}")
            elif provider == 'anthropic' and not env_status.get('ANTHROPIC_API_KEY'):
                print(f"\\n🔧 Anthropic Setup:{instruction}")
            elif provider == 'gemini' and not env_status.get('GEMINI_API_KEY'):
                print(f"\\n🔧 Google Gemini Setup:{instruction}")
            elif provider == 'together' and not env_status.get('TOGETHER_API_KEY'):
                print(f"\\n🔧 Together AI Setup:{instruction}")
            elif provider == 'ollama':
                print(f"\\n🔧 Ollama Setup:{instruction}")
    
    def get_recommendations(self) -> List[str]:
        """Get recommendations based on available providers."""
        env_status = self.check_environment_variables()
        recommendations = []
        
        if not any(env_status.values()):
            recommendations.append("🚨 No API keys configured. Start with Ollama for local testing.")
            recommendations.append("💡 For production, set up at least OpenAI or Gemini API keys.")
        
        if env_status.get('GEMINI_API_KEY'):
            recommendations.append("✨ Gemini Pro detected - excellent for cost-effective queries.")
        
        if env_status.get('OPENAI_API_KEY'):
            recommendations.append("✨ OpenAI detected - great balanced performance.")
        
        if env_status.get('ANTHROPIC_API_KEY'):
            recommendations.append("✨ Claude detected - excellent for legal reasoning.")
        
        if not env_status.get('OPENAI_API_KEY') and not env_status.get('ANTHROPIC_API_KEY'):
            recommendations.append("💡 Consider adding OpenAI or Anthropic for better legal analysis.")
        
        return recommendations

def main():
    """Main setup function."""
    print("🤖 AI Provider Setup for Legal RAG Engine")
    print("=" * 50)
    
    # Import time here to avoid issues
    import time
    
    setup_manager = AISetupManager()
    
    # Check environment and dependencies
    env_status = setup_manager.check_environment_variables()
    deps_status = setup_manager.check_dependencies()
    
    # Print recommendations
    recommendations = setup_manager.get_recommendations()
    if recommendations:
        print("\\n💡 Recommendations:")
        print("=" * 40)
        for rec in recommendations:
            print(rec)
    
    # Ask user for performance profile
    print("\\n🎯 Performance Profiles:")
    print("1. speed_optimized - Fastest responses")
    print("2. quality_optimized - Best quality responses") 
    print("3. cost_optimized - Lowest cost")
    print("4. balanced - Good balance of all factors")
    
    profile_choice = input("\\nSelect profile (1-4) or press Enter for balanced: ").strip()
    profile_map = {'1': 'speed_optimized', '2': 'quality_optimized', '3': 'cost_optimized', '4': 'balanced'}
    profile = profile_map.get(profile_choice, 'balanced')
    
    # Setup RAG engine
    if setup_manager.setup_rag_engine_with_providers(profile):
        # Test providers
        test_results = setup_manager.test_providers()
        
        if test_results:
            # Test smart routing
            setup_manager.test_smart_routing()
            
            # Print final status
            print("\\n🎉 Setup Complete!")
            print("=" * 40)
            print(f"✅ RAG engine configured with {len(test_results)} providers")
            print(f"✅ Smart routing enabled with '{profile}' profile")
            
            successful_providers = [k for k, v in test_results.items() if v['status'] == 'success']
            print(f"✅ {len(successful_providers)} providers tested successfully")
            
            return True
    
    # If setup failed, show instructions
    setup_manager.print_setup_instructions()
    
    return False

if __name__ == "__main__":
    main()
