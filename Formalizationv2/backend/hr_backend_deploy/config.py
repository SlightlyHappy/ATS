"""
Enhanced Production Configuration
Optimized for high-volume resume processing with multi-provider AI support
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class AIProvider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    TOGETHER = "together"

@dataclass
class AIProviderConfig:
    """Configuration for AI providers"""
    provider_type: str
    model: str
    api_key: str = None
    base_url: str = None
    max_tokens: int = 2000
    temperature: float = 0.1
    timeout: int = 600
    retry_attempts: int = 3
    retry_delay: float = 1.0

class EnhancedConfig:
    """Enhanced configuration for Railway deployment with advanced features"""
    
    # Server Configuration
    PORT = int(os.getenv('PORT', 8000))
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    SECRET_KEY = os.getenv('SECRET_KEY', 'hr-resume-screening-flask-secret-key-2025-temp')
    
    # Memory Management
    MAX_MEMORY_CACHE_SIZE = int(os.getenv('MAX_MEMORY_CACHE_SIZE', 50))
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1))
    MAX_CONCURRENT_PROCESSING = int(os.getenv('MAX_CONCURRENT_PROCESSING', 1))
    MEMORY_WARNING_THRESHOLD = float(os.getenv('MEMORY_WARNING_THRESHOLD', 0.8))
    
    # File Processing
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))  # 16MB
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 10485760))  # 10MB
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
    PROCESSED_FOLDER = os.getenv('PROCESSED_FOLDER', '/tmp/processed')
    
    # AI Configuration - Multi-Provider Support
    DEFAULT_AI_PROVIDER = os.getenv('DEFAULT_AI_PROVIDER', 'ollama')
    AI_PROVIDERS = {
        'ollama': AIProviderConfig(
            provider_type='ollama',
            model=os.getenv('OLLAMA_MODEL', 'qwen2.5:7b'),
            base_url=os.getenv('OLLAMA_URL', 'http://localhost:11434'),
            timeout=int(os.getenv('AI_TIMEOUT', 600))
        ),
        'openai': AIProviderConfig(
            provider_type='openai',
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            api_key=os.getenv('OPENAI_API_KEY'),
            timeout=300
        ),
        'gemini': AIProviderConfig(
            provider_type='gemini',
            model=os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'),
            api_key=os.getenv('GEMINI_API_KEY'),
            timeout=300
        ),
        'anthropic': AIProviderConfig(
            provider_type='anthropic',
            model=os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
            api_key=os.getenv('ANTHROPIC_API_KEY'),
            timeout=300
        ),
        'together': AIProviderConfig(
            provider_type='together',
            model=os.getenv('TOGETHER_MODEL', 'meta-llama/Llama-3.2-3B-Instruct-Turbo'),
            api_key=os.getenv('TOGETHER_API_KEY'),
            timeout=300
        )
    }
    
    # Advanced AI Features
    ENABLE_AGENTIC_ANALYSIS = os.getenv('ENABLE_AGENTIC_ANALYSIS', 'true').lower() == 'true'
    ENABLE_MARKET_SCORING = os.getenv('ENABLE_MARKET_SCORING', 'true').lower() == 'true'
    ENABLE_BATCH_PROCESSING = os.getenv('ENABLE_BATCH_PROCESSING', 'true').lower() == 'true'
    BATCH_ANALYSIS_THRESHOLD = int(os.getenv('BATCH_ANALYSIS_THRESHOLD', 5))
    
    # Storage Configuration
    ENABLE_PERSISTENT_STORAGE = os.getenv('ENABLE_PERSISTENT_STORAGE', 'true').lower() == 'true'
    ENABLE_DISK_CACHE = os.getenv('ENABLE_DISK_CACHE', 'true').lower() == 'true'
    COMPRESS_PROCESSED_FILES = os.getenv('COMPRESS_PROCESSED_FILES', 'true').lower() == 'true'
    MAX_FILE_AGE_HOURS = int(os.getenv('MAX_FILE_AGE_HOURS', 24))
    
    # Security Configuration
    BCRYPT_LOG_ROUNDS = int(os.getenv('BCRYPT_LOG_ROUNDS', 12))
    JWT_EXPIRATION_DELTA = int(os.getenv('JWT_EXPIRATION_DELTA', 7200))
    ENABLE_RATE_LIMITING = os.getenv('ENABLE_RATE_LIMITING', 'true').lower() == 'true'
    ENABLE_SECURITY_HEADERS = os.getenv('ENABLE_SECURITY_HEADERS', 'true').lower() == 'true'
    
    # Trial System
    DEFAULT_TRIAL_LIMIT = int(os.getenv('DEFAULT_TRIAL_LIMIT', 100))
    DEFAULT_TRIAL_DAYS = int(os.getenv('DEFAULT_TRIAL_DAYS', 30))
    
    # HR Legal System
    HR_LEGAL_ENABLED = os.getenv('HR_LEGAL_ENABLED', 'true').lower() == 'true'
    LEGAL_KNOWLEDGE_PATH = os.getenv('LEGAL_KNOWLEDGE_PATH', '/app/legal_knowledge')
    
    # Email Configuration
    ENABLE_EMAIL_TEMPLATES = os.getenv('ENABLE_EMAIL_TEMPLATES', 'true').lower() == 'true'
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    
    # CORS Configuration
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://hrtool-sable.vercel.app')
    ALLOWED_ORIGINS = [
        FRONTEND_URL,
        'http://localhost:3000',  # Development
        'http://localhost:5000'   # Development
    ]
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', '/tmp/logs/application.log')
    ENABLE_STRUCTURED_LOGGING = os.getenv('ENABLE_STRUCTURED_LOGGING', 'true').lower() == 'true'
    
    # Performance Monitoring
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
    ENABLE_HEALTH_CHECKS = os.getenv('ENABLE_HEALTH_CHECKS', 'true').lower() == 'true'
    
    # Market-Based Scoring Configuration
    SCORING_DISTRIBUTION = {
        'exceptional': 0.05,  # Top 5% - scores 85-95
        'excellent': 0.15,    # Next 15% - scores 75-84
        'good': 0.30,         # Next 30% - scores 65-74
        'average': 0.35,      # Next 35% - scores 50-64
        'below_average': 0.15 # Bottom 15% - scores 30-49
    }
    
    MARKET_ADJUSTMENTS = {
        'high_demand_skills': 5,     # Boost for in-demand skills
        'experience_premium': 3,     # Boost for relevant experience
        'education_bonus': 2,        # Boost for relevant education
        'certification_bonus': 4,    # Boost for relevant certifications
        'location_penalty': -2,      # Penalty for location mismatch
        'overqualified_penalty': -3  # Penalty for being overqualified
    }
    
    EXPERIENCE_BENCHMARKS = {
        'junior': {'min_years': 0, 'max_years': 2, 'score_range': (40, 65)},
        'mid': {'min_years': 2, 'max_years': 5, 'score_range': (55, 80)},
        'senior': {'min_years': 5, 'max_years': 10, 'score_range': (70, 90)},
        'lead': {'min_years': 8, 'max_years': 15, 'score_range': (75, 95)},
        'executive': {'min_years': 10, 'max_years': None, 'score_range': (80, 95)}
    }
    
    @classmethod
    def get_model_for_volume(cls, resume_count: int) -> str:
        """Select optimal model based on processing volume"""
        if resume_count >= 20:
            return 'qwen2.5:3b'  # Faster for bulk processing
        return 'qwen2.5:7b'     # Better accuracy for smaller batches
    
    @classmethod
    def get_ai_provider_config(cls, provider_name: str = None) -> AIProviderConfig:
        """Get AI provider configuration"""
        if not provider_name:
            provider_name = cls.DEFAULT_AI_PROVIDER
        
        return cls.AI_PROVIDERS.get(provider_name, cls.AI_PROVIDERS['ollama'])
    
    @classmethod
    def get_fallback_providers(cls) -> List[str]:
        """Get list of fallback providers in order of preference"""
        primary = cls.DEFAULT_AI_PROVIDER
        all_providers = list(cls.AI_PROVIDERS.keys())
        
        # Remove primary from list and put it first
        if primary in all_providers:
            all_providers.remove(primary)
        
        return [primary] + all_providers

# Create global config instance
config = EnhancedConfig()
