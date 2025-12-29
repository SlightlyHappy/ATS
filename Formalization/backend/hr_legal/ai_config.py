"""
AI Provider Configuration
========================

Configuration for multiple AI providers with performance profiles
and intelligent routing capabilities.
"""

import os
from typing import Dict, List, Any

class AIProviderConfig:
    """Configuration for AI providers."""
    
    # Default provider configurations
    DEFAULT_PROVIDERS = [
        {
            'provider_type': 'gemini',
            'model': 'gemini-pro',
            'api_key': os.getenv('GEMINI_API_KEY'),
            'priority': 'speed',
            'description': 'Fast and cost-effective for simple queries'
        },
        {
            'provider_type': 'openai',
            'model': 'gpt-3.5-turbo',
            'api_key': os.getenv('OPENAI_API_KEY'),
            'priority': 'balanced',
            'description': 'Balanced performance for medium complexity'
        },
        {
            'provider_type': 'openai',
            'model': 'gpt-4o',
            'api_key': os.getenv('OPENAI_API_KEY'),
            'priority': 'quality',
            'description': 'High quality for complex legal analysis'
        },
        {
            'provider_type': 'anthropic',
            'model': 'claude-3-sonnet-20240229',
            'api_key': os.getenv('ANTHROPIC_API_KEY'),
            'priority': 'quality',
            'description': 'Excellent for legal reasoning and analysis'
        },
        {
            'provider_type': 'ollama',
            'model': 'qwen2.5:7b',
            'api_key': None,
            'kwargs': {'base_url': 'http://localhost:11434'},
            'priority': 'fallback',
            'description': 'Local fallback when APIs are unavailable'
        },
        {
            'provider_type': 'ollama',
            'model': 'qwen2.5:7b',
            'api_key': None,
            'kwargs': {'base_url': 'http://localhost:11434'},
            'priority': 'quality',
            'description': 'Better local model for complex legal reasoning'
        }
    ]
    
    # Performance profiles for different use cases
    PERFORMANCE_PROFILES = {
        'speed_optimized': {
            'description': 'Optimized for fastest response times',
            'preferred_providers': ['gemini_gemini-pro', 'openai_gpt-3.5-turbo'],
            'complexity_routing': {
                'simple': 'gemini_gemini-pro',
                'medium': 'openai_gpt-3.5-turbo',
                'complex': 'openai_gpt-4o'
            }
        },
        'quality_optimized': {
            'description': 'Optimized for highest quality legal responses',
            'preferred_providers': ['anthropic_claude-3-sonnet-20240229', 'openai_gpt-4o', 'ollama_qwen2.5:7b'],
            'complexity_routing': {
                'simple': 'openai_gpt-3.5-turbo',
                'medium': 'anthropic_claude-3-sonnet-20240229',
                'complex': 'openai_gpt-4o'
            }
        },
        'cost_optimized': {
            'description': 'Optimized for lowest cost with good quality',
            'preferred_providers': ['gemini_gemini-pro', 'ollama_llama3.1:8b', 'ollama_qwen2.5:7b'],
            'complexity_routing': {
                'simple': 'gemini_gemini-pro',
                'medium': 'ollama_llama3.1:8b',
                'complex': 'openai_gpt-3.5-turbo'
            }
        },
        'balanced': {
            'description': 'Balanced approach across all factors',
            'preferred_providers': ['openai_gpt-3.5-turbo', 'gemini_gemini-pro', 'anthropic_claude-3-sonnet-20240229'],
            'complexity_routing': {
                'simple': 'gemini_gemini-pro',
                'medium': 'openai_gpt-3.5-turbo',
                'complex': 'anthropic_claude-3-sonnet-20240229'
            }
        },
        'legal_optimized': {
            'description': 'Optimized specifically for legal reasoning and compliance',
            'preferred_providers': ['anthropic_claude-3-sonnet-20240229', 'openai_gpt-4o', 'ollama_qwen2.5:7b'],
            'complexity_routing': {
                'simple': 'anthropic_claude-3-sonnet-20240229',
                'medium': 'anthropic_claude-3-sonnet-20240229',
                'complex': 'openai_gpt-4o'
            },
            'special_instructions': {
                'use_legal_terminology': True,
                'cite_sources': True,
                'include_disclaimers': True,
                'structured_analysis': True
            }
        }
    }
    
    @classmethod
    def get_available_providers(cls) -> List[Dict[str, Any]]:
        """Get list of available providers with valid API keys."""
        available = []
        
        for provider in cls.DEFAULT_PROVIDERS:
            if provider['provider_type'] == 'ollama':
                # Ollama doesn't need API key
                available.append(provider)
            elif provider['api_key']:
                # Only include providers with valid API keys
                available.append(provider)
        
        return available
    
    @classmethod
    def get_providers_for_profile(cls, profile_name: str) -> List[Dict[str, Any]]:
        """Get provider configurations for a specific performance profile."""
        if profile_name not in cls.PERFORMANCE_PROFILES:
            profile_name = 'balanced'
        
        profile = cls.PERFORMANCE_PROFILES[profile_name]
        available_providers = cls.get_available_providers()
        
        # Filter providers based on profile preferences
        preferred_providers = []
        for provider in available_providers:
            provider_key = f"{provider['provider_type']}_{provider['model']}"
            if provider_key in profile['preferred_providers']:
                preferred_providers.append(provider)
        
        # If no preferred providers available, return all available
        return preferred_providers if preferred_providers else available_providers
    
    @classmethod
    def validate_provider_config(cls, provider_config: Dict[str, Any]) -> bool:
        """Validate a provider configuration."""
        required_fields = ['provider_type', 'model']
        
        # Check required fields
        for field in required_fields:
            if field not in provider_config:
                return False
        
        # Check API key requirement for external providers
        if provider_config['provider_type'] != 'ollama':
            if not provider_config.get('api_key'):
                return False
        
        return True
    
    @classmethod
    def get_setup_instructions(cls) -> Dict[str, str]:
        """Get setup instructions for each provider type."""
        return {
            'openai': """
            1. Get API key from https://platform.openai.com/api-keys
            2. Set environment variable: OPENAI_API_KEY=your_api_key
            3. Install: pip install openai
            """,
            'anthropic': """
            1. Get API key from https://console.anthropic.com/
            2. Set environment variable: ANTHROPIC_API_KEY=your_api_key
            3. Install: pip install anthropic
            """,
            'gemini': """
            1. Get API key from https://makersuite.google.com/app/apikey
            2. Set environment variable: GEMINI_API_KEY=your_api_key
            3. Install: pip install google-generativeai
            """,
            'together': """
            1. Get API key from https://api.together.xyz/settings/api-keys
            2. Set environment variable: TOGETHER_API_KEY=your_api_key
            3. Install: pip install together
            """,
            'ollama': """
            1. Install Ollama from https://ollama.ai/
            2. Run: ollama pull qwen2.5:7b
            3. Start server: ollama serve
            """
        }

class AIRoutingConfig:
    """Configuration for intelligent AI routing."""
    
    # Query complexity thresholds
    COMPLEXITY_THRESHOLDS = {
        'word_count': {
            'simple': (0, 50),
            'medium': (51, 200),
            'complex': (201, float('inf'))
        },
        'legal_terms': {
            'simple': (0, 1),
            'medium': (2, 4),
            'complex': (5, float('inf'))
        },
        'technical_terms': {
            'simple': (0, 1),
            'medium': (2, 3),
            'complex': (4, float('inf'))
        }
    }
    
    # Comprehensive legal keywords for complexity analysis
    LEGAL_KEYWORDS = [
        # Core legal terms
        'law', 'legal', 'court', 'regulation', 'compliance', 'statute', 
        'act', 'section', 'clause', 'provision', 'amendment', 'jurisdiction',
        'precedent', 'case law', 'litigation', 'contract', 'agreement',
        
        # Employment & HR specific
        'employment', 'labor', 'hr', 'human resources', 'workplace',
        'discrimination', 'harassment', 'termination', 'hiring', 'firing',
        'equal opportunity', 'ada', 'fmla', 'overtime', 'wages',
        'benefits', 'leave', 'accommodation', 'disability', 'pregnancy',
        'whistleblower', 'retaliation', 'at-will', 'wrongful termination',
        
        # Policy & compliance
        'policy', 'procedure', 'handbook', 'code of conduct', 'ethics',
        'safety', 'osha', 'workers compensation', 'unemployment',
        'background check', 'drug testing', 'confidentiality',
        'non-disclosure', 'non-compete', 'intellectual property',
        
        # Legal processes
        'lawsuit', 'claim', 'grievance', 'investigation', 'arbitration',
        'mediation', 'settlement', 'liability', 'damages', 'penalty',
        'fine', 'enforcement', 'audit', 'review', 'appeal'
    ]
    
    # Technical keywords for complexity analysis
    TECHNICAL_KEYWORDS = [
        'procedure', 'process', 'analysis', 'detailed', 'comprehensive',
        'implementation', 'framework', 'methodology', 'assessment',
        'evaluation', 'documentation', 'specification', 'requirement'
    ]
    
    # Caching configuration
    CACHE_CONFIG = {
        'response_cache_ttl': 1800,  # 30 minutes
        'vector_cache_ttl': 3600,    # 1 hour
        'ai_cache_ttl': 900,         # 15 minutes
        'max_cache_size': 1000       # Maximum cached items
    }
    
    # Fallback configuration
    FALLBACK_CONFIG = {
        'max_retries': 3,
        'retry_delay': 2.0,
        'fallback_providers': ['ollama_qwen2.5:7b'],  # Always available fallback
        'error_response_template': """
        I apologize, but I'm experiencing technical difficulties processing your legal query.
        
        This may be due to:
        • Temporary API service issues
        • Network connectivity problems
        • High system load
        
        Please try:
        • Rephrasing your question
        • Trying again in a few minutes
        • Using simpler language
        • Breaking complex queries into smaller parts
        
        For urgent legal matters, please consult with a qualified legal professional.
        """
    }
