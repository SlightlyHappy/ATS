#!/usr/bin/env python3
"""
Enhanced Configuration Management for Advanced Agentic HR ATS System
Railway-optimized configuration with comprehensive AI, RAG, and ML support
"""

import os
from typing import Dict, Any, Optional, List

class Config:
    """Enhanced configuration management for advanced Railway deployment"""
    
    def __init__(self):
        """Initialize configuration with environment variables"""
        self.load_config()
        
    def load_config(self):
        """Load configuration from environment variables"""
        
        # Flask Configuration
        self.FLASK_ENV = os.getenv('FLASK_ENV', 'production')
        self.SECRET_KEY = os.getenv('SECRET_KEY', self.generate_secret_key())
        self.DEBUG = self.FLASK_ENV == 'development'
        
        # Railway Configuration
        self.PORT = int(os.getenv('PORT', 8000))
        self.RAILWAY_ENVIRONMENT = os.getenv('RAILWAY_ENVIRONMENT')
        self.RAILWAY_SERVICE_NAME = os.getenv('RAILWAY_SERVICE_NAME')
        
        # Supabase Configuration (EXISTING PERSISTENT STORAGE)
        self.SUPABASE_URL = os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        self.SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY') or os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        self.SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET')
        
        # ==========================================
        # ADVANCED AI CONFIGURATION
        # ==========================================
        
        # Primary AI Provider (Ollama) - Optimized for 32GB/32CPU Railway Pro
        self.OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen2.5:14b')  # 14B for 32GB RAM
        self.OLLAMA_FALLBACK_MODEL = os.getenv('OLLAMA_FALLBACK_MODEL', 'qwen2.5:7b')  # 7B fallback
        
        # Enhanced AI Timeouts for Railway Pro (32 CPU, 32GB RAM)
        self.AI_TIMEOUT = int(os.getenv('AI_TIMEOUT', 900))  # 15 minutes for resume analysis
        self.OLLAMA_BATCH_TIMEOUT = int(os.getenv('OLLAMA_BATCH_TIMEOUT', 1800))  # 30 minutes for batch
        self.OLLAMA_SIMPLE_TIMEOUT = int(os.getenv('OLLAMA_SIMPLE_TIMEOUT', 180))  # 3 minutes for simple queries
        self.AI_MAX_RETRIES = int(os.getenv('AI_MAX_RETRIES', 3))
        
        # AI-First Pipeline Configuration
        self.ENABLE_AUTO_AI_PROCESSING = os.getenv('ENABLE_AUTO_AI_PROCESSING', 'true').lower() == 'true'
        self.DEFAULT_JOB_REQUIREMENTS = os.getenv('DEFAULT_JOB_REQUIREMENTS', '{"title": "General Position", "required_skills": []}')
        
        # Multi-Provider AI Configuration
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
        self.ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307')
        
        # AI Provider Priority (for 32GB/32CPU setup)
        self.AI_PROVIDER_PRIORITY = ['openai', 'anthropic', 'ollama']  # Ollama as guaranteed fallback
        
        # ==========================================
        # AGENTIC AI SYSTEM CONFIGURATION
        # ==========================================
        
        # Agent Configuration
        self.ENABLE_AGENTIC_ANALYSIS = os.getenv('ENABLE_AGENTIC_ANALYSIS', 'true').lower() == 'true'
        self.AGENT_TIMEOUT = int(os.getenv('AGENT_TIMEOUT', 60))  # per agent
        self.AGENT_MAX_CONCURRENT = int(os.getenv('AGENT_MAX_CONCURRENT', 4))
        
        # Market Analysis Configuration
        self.ENABLE_MARKET_ANALYSIS = os.getenv('ENABLE_MARKET_ANALYSIS', 'true').lower() == 'true'
        self.MARKET_DATA_REFRESH_HOURS = int(os.getenv('MARKET_DATA_REFRESH_HOURS', 24))
        
        # Realistic Scoring Framework
        self.SCORING_DISTRIBUTION = {
            'exceptional': 0.05,  # Top 5%
            'above_average': 0.20,  # Top 25%
            'average': 0.50,  # Middle 50%
            'below_average': 0.20,  # Bottom 25%
            'poor': 0.05  # Bottom 5%
        }
        
        # ==========================================
        # RAG SYSTEM CONFIGURATION
        # ==========================================
        
        # FAISS Vector Store Configuration
        self.FAISS_INDEX_PATH = os.getenv('FAISS_INDEX_PATH', '/app/faiss_indexes')
        self.EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        self.EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', 384))
        self.FAISS_INDEX_TYPE = os.getenv('FAISS_INDEX_TYPE', 'IndexFlatIP')
        
        # Legal Knowledge Base Configuration
        self.LEGAL_KNOWLEDGE_PATH = os.getenv('LEGAL_KNOWLEDGE_PATH', '/app/legal_knowledge')
        self.ENABLE_HR_LEGAL = os.getenv('ENABLE_HR_LEGAL', 'true').lower() == 'true'
        self.LEGAL_RESPONSE_MAX_LENGTH = int(os.getenv('LEGAL_RESPONSE_MAX_LENGTH', 2000))
        
        # RAG Engine Configuration
        self.RAG_RETRIEVAL_TOP_K = int(os.getenv('RAG_RETRIEVAL_TOP_K', 5))
        self.RAG_SIMILARITY_THRESHOLD = float(os.getenv('RAG_SIMILARITY_THRESHOLD', 0.7))
        self.RAG_CONTEXT_WINDOW = int(os.getenv('RAG_CONTEXT_WINDOW', 4000))
        
        # ==========================================
        # MEMORY & PERFORMANCE CONFIGURATION
        # ==========================================
        
        # Railway Memory Optimization (8GB total)
        self.MAX_MEMORY_USAGE_GB = float(os.getenv('MAX_MEMORY_USAGE_GB', 7.5))
        self.OLLAMA_MEMORY_LIMIT_GB = float(os.getenv('OLLAMA_MEMORY_LIMIT_GB', 5.0))
        self.FAISS_MEMORY_LIMIT_MB = int(os.getenv('FAISS_MEMORY_LIMIT_MB', 512))
        
        # Caching Configuration
        self.ENABLE_REDIS_CACHE = os.getenv('REDIS_URL') is not None
        self.REDIS_URL = os.getenv('REDIS_URL')
        self.CACHE_EXPIRATION_HOURS = int(os.getenv('CACHE_EXPIRATION_HOURS', 24))
        
        # File Processing Configuration
        self.MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 50 * 1024 * 1024))  # 50MB
        self.ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
        self.UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
        self.PROCESSED_FOLDER = os.getenv('PROCESSED_FOLDER', '/tmp/processed')
        
        # Security Configuration
        self.RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
        self.RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', 100))
        self.RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', 3600))  # 1 hour
        
        # Trial Configuration
        self.TRIAL_RESUME_LIMIT = int(os.getenv('TRIAL_RESUME_LIMIT', 100))
        self.TRIAL_LEGAL_QUERIES_LIMIT = int(os.getenv('TRIAL_LEGAL_QUERIES_LIMIT', 50))
        
        # Performance Configuration
        self.MAX_CONCURRENT_PROCESSING = int(os.getenv('MAX_CONCURRENT_PROCESSING', 2))
        self.MEMORY_WARNING_THRESHOLD = float(os.getenv('MEMORY_WARNING_THRESHOLD', 0.8))
        self.ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'false').lower() == 'true'
        self.LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'logs/app.log')
        
        # Frontend Configuration
        self.FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://hrtool-sable.vercel.app')
        self.CORS_ORIGINS = self.get_cors_origins()
        
        # Validate critical configuration
        self.validate_config()
        
    def generate_secret_key(self) -> str:
        """Generate a secure secret key if not provided"""
        import secrets
        return secrets.token_urlsafe(32)
        
    def get_cors_origins(self) -> list:
        """Get CORS origins from environment"""
        origins = [self.FRONTEND_URL, "http://localhost:3000"]
        
        # Add additional origins if specified
        additional_origins = os.getenv('ADDITIONAL_CORS_ORIGINS', '')
        if additional_origins:
            origins.extend(additional_origins.split(','))
            
        return origins
        
    def validate_config(self):
        """Validate required configuration settings"""
        errors = []
        
        # Skip validation in testing mode
        if os.getenv('TESTING') == 'true':
            return
        
        # Check Supabase configuration (required for production)
        if not self.SUPABASE_URL:
            errors.append("SUPABASE_URL is required")
        if not self.SUPABASE_ANON_KEY:
            errors.append("SUPABASE_ANON_KEY is required")
            
        # Check AI configuration
        if not self.OLLAMA_URL and not self.OPENAI_API_KEY:
            errors.append("Either OLLAMA_URL or OPENAI_API_KEY must be configured")
            
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        # Check Supabase configuration
        if not self.SUPABASE_URL:
            errors.append("SUPABASE_URL is required")
        if not self.SUPABASE_ANON_KEY:
            errors.append("SUPABASE_ANON_KEY is required")
            
        # Check AI configuration
        if not self.OLLAMA_URL and not self.OPENAI_API_KEY:
            errors.append("Either OLLAMA_URL or OPENAI_API_KEY must be configured")
            
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
            
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI provider configuration"""
        return {
            'ollama': {
                'url': self.OLLAMA_URL,
                'model': self.OLLAMA_MODEL,
                'timeout': self.AI_TIMEOUT,
                'enabled': bool(self.OLLAMA_URL)
            },
            'openai': {
                'api_key': self.OPENAI_API_KEY,
                'model': self.OPENAI_MODEL,
                'timeout': self.AI_TIMEOUT,
                'enabled': bool(self.OPENAI_API_KEY)
            },
            'max_retries': self.AI_MAX_RETRIES
        }
        
    def get_supabase_config(self) -> Dict[str, str]:
        """Get Supabase configuration"""
        return {
            'url': self.SUPABASE_URL,
            'anon_key': self.SUPABASE_ANON_KEY,
            'service_key': self.SUPABASE_SERVICE_KEY,
            'jwt_secret': self.SUPABASE_JWT_SECRET
        }
        
    def get_flask_config(self) -> Dict[str, Any]:
        """Get Flask application configuration"""
        return {
            'SECRET_KEY': self.SECRET_KEY,
            'DEBUG': self.DEBUG,
            'MAX_CONTENT_LENGTH': self.MAX_FILE_SIZE,
            'UPLOAD_FOLDER': self.UPLOAD_FOLDER,
            'PROCESSED_FOLDER': self.PROCESSED_FOLDER
        }
        
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return {
            'rate_limit_enabled': self.RATE_LIMIT_ENABLED,
            'rate_limit_requests': self.RATE_LIMIT_REQUESTS,
            'rate_limit_window': self.RATE_LIMIT_WINDOW,
            'memory_warning_threshold': self.MEMORY_WARNING_THRESHOLD
        }
        
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.FLASK_ENV == 'production'
        
    def is_railway(self) -> bool:
        """Check if running on Railway"""
        return bool(self.RAILWAY_ENVIRONMENT)
        
    def __repr__(self):
        """String representation of configuration"""
        return f"<Config env={self.FLASK_ENV} port={self.PORT} railway={self.is_railway()}>"

# Global configuration instance
config = Config()
