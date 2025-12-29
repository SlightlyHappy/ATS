import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # JWT Configuration - Critical for Auth
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or os.environ.get('SECRET_KEY') or 'jwt-dev-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_HOURS', 24)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_DAYS', 30)))
    JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 24))
    JWT_REFRESH_EXPIRATION_DAYS = int(os.environ.get('JWT_REFRESH_EXPIRATION_DAYS', 30))
    
    # Password and Security Configuration
    PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH', 8))
    SESSION_TIMEOUT_MINUTES = int(os.environ.get('SESSION_TIMEOUT_MINUTES', 480))  # 8 hours
    
    # Database Configuration - Railway specific
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'postgresql://localhost/resumeai_dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DATABASE_POOL_SIZE', 5)),
        'pool_recycle': int(os.environ.get('DATABASE_POOL_RECYCLE_TIME', 3600)),
        'pool_pre_ping': False,  # Disable pre_ping to avoid threading issues
        'max_overflow': int(os.environ.get('DATABASE_MAX_CONNECTIONS', 8)) - int(os.environ.get('DATABASE_POOL_SIZE', 5)),
        'pool_timeout': int(os.environ.get('DATABASE_CONNECTION_TIMEOUT', 30)),
        'echo': False,  # Disable SQL echo for production
        'connect_args': {
            "sslmode": "require" if os.environ.get('DATABASE_URL') and 'railway' in os.environ.get('DATABASE_URL', '') else "disable",
            "application_name": "ResumeAI_Production"
        }
    }
    
    # Ollama Configuration
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_URL') or 'http://localhost:11434'
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL') or 'qwen2.5:7b'
    OLLAMA_TIMEOUT = int(os.environ.get('AI_TIMEOUT', 300))
    
    # Agent Configuration
    MAX_CONCURRENT_AGENTS = int(os.environ.get('MAX_CONCURRENT_AI_REQUESTS', 4))
    AGENT_TIMEOUT = int(os.environ.get('AI_TIMEOUT_SECONDS', 60))
    ANALYSIS_CACHE_TTL = int(os.environ.get('CACHE_TTL', 300))
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_FILE_SIZE', 52428800))  # Default 50MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    PROCESSED_FOLDER = os.environ.get('PROCESSED_FOLDER') or 'processed'
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
    ALLOWED_ARCHIVE_EXTENSIONS = {'zip'}
    
    # Resume Storage Configuration
    RESUME_STORAGE_PATH = os.environ.get('RESUME_STORAGE_PATH') or 'uploads/resumes'
    BATCH_STORAGE_PATH = os.environ.get('BATCH_STORAGE_PATH') or 'uploads/batches'
    MAX_RESUME_TEXT_LENGTH = int(os.environ.get('MAX_RESUME_TEXT_LENGTH', 1000000))  # 1MB text
    RESUME_FILE_RETENTION_DAYS = int(os.environ.get('RESUME_FILE_RETENTION_DAYS', 90))
    
    # Analysis Storage Configuration
    ANALYSIS_RESULT_COMPRESSION = os.environ.get('ANALYSIS_RESULT_COMPRESSION', 'true').lower() == 'true'
    MAX_ANALYSIS_RESULT_SIZE = int(os.environ.get('MAX_ANALYSIS_RESULT_SIZE', 10485760))  # 10MB JSON
    
    # Queue Configuration
    MAX_CONCURRENT_QUEUE_JOBS = int(os.environ.get('MAX_CONCURRENT_QUEUE_JOBS', 3))
    QUEUE_PROCESSING_INTERVAL = int(os.environ.get('QUEUE_PROCESSING_INTERVAL', 5))  # seconds
    MAX_QUEUE_RETRIES = int(os.environ.get('MAX_QUEUE_RETRIES', 3))
    ESTIMATED_ANALYSIS_TIME = int(os.environ.get('ESTIMATED_ANALYSIS_TIME', 120))  # seconds per analysis
    
    # Credit System Configuration
    DEFAULT_USER_CREDITS = int(os.environ.get('DEFAULT_USER_CREDITS', 10))
    ADMIN_UNLIMITED_CREDITS = os.environ.get('ADMIN_UNLIMITED_CREDITS', 'true').lower() == 'true'
    CREDIT_COST_PER_ANALYSIS = int(os.environ.get('CREDIT_COST_PER_ANALYSIS', 1))
    CREDIT_COST_PER_LEGAL_QUERY = int(os.environ.get('CREDIT_COST_PER_LEGAL_QUERY', 2))
    
    # Legal RAG Configuration
    LEGAL_RAG_ENABLED = os.environ.get('LEGAL_RAG_ENABLED', 'true').lower() == 'true'
    LEGAL_DOCS_PATH = os.environ.get('LEGAL_DOCS_PATH', 'legal_documents')
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    LEGAL_EMBEDDING_MODEL = os.environ.get('LEGAL_EMBEDDING_MODEL', 'all-mpnet-base-v2')
    
    # RAG Processing Configuration
    RAG_CHUNK_SIZE = int(os.environ.get('RAG_CHUNK_SIZE', 512))
    RAG_CHUNK_OVERLAP = int(os.environ.get('RAG_CHUNK_OVERLAP', 50))
    RAG_TOP_K = int(os.environ.get('RAG_TOP_K', 5))
    RAG_SIMILARITY_THRESHOLD = float(os.environ.get('RAG_SIMILARITY_THRESHOLD', 0.7))
    
    # Vector Database Configuration
    USE_POSTGRES_VECTORS = os.environ.get('USE_POSTGRES_VECTORS', 'true').lower() == 'true'
    VECTOR_DB_PATH = os.environ.get('VECTOR_DB_PATH', 'vector_db')
    
    # Legal Query Configuration
    MAX_CONTEXT_LENGTH = int(os.environ.get('MAX_CONTEXT_LENGTH', 4000))
    LEGAL_RESPONSE_TIMEOUT = int(os.environ.get('LEGAL_RESPONSE_TIMEOUT', 180))
    ENABLE_QUERY_CACHING = os.environ.get('ENABLE_QUERY_CACHING', 'true').lower() == 'true'
    QUERY_CACHE_TTL = int(os.environ.get('QUERY_CACHE_TTL', 3600))  # 1 hour
    
    # Knowledge Base Update Configuration
    AUTO_UPDATE_ON_DEPLOY = os.environ.get('AUTO_UPDATE_ON_DEPLOY', 'true').lower() == 'true'
    ENABLE_INCREMENTAL_UPDATES = os.environ.get('ENABLE_INCREMENTAL_UPDATES', 'true').lower() == 'true'
    UPDATE_CHECK_INTERVAL_HOURS = int(os.environ.get('UPDATE_CHECK_INTERVAL_HOURS', 24))
    
    # Caching Configuration
    CACHE_TYPE = 'simple'  # Use simple cache for Railway deployment
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_TTL', 300))
    
    # API Configuration
    API_RATE_LIMIT = f"{os.environ.get('RATE_LIMIT_REQUESTS', 100)} per hour"
    
    # CORS Configuration
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://hrtool-sable.vercel.app')
    ADDITIONAL_CORS_ORIGINS = os.environ.get('ADDITIONAL_CORS_ORIGINS', '').split(',')
    
    # Railway specific
    PORT = int(os.environ.get('PORT', 8000))
    
    # Health Check Configuration
    HEALTH_CHECK_TIMEOUT = int(os.environ.get('HEALTH_CHECK_TIMEOUT', 10))
    SIMPLE_HEALTH_ONLY = os.environ.get('SIMPLE_HEALTH_ONLY', 'false').lower() == 'true'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration optimized for Railway deployment."""
    DEBUG = False
    TESTING = False
    ENV = 'production'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline';"
    }
    
    # Performance optimizations
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year for static files
    
    # Enhanced logging for production
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'true').lower() == 'true'
    
    # AI Service Optimizations for Railway resource limits
    MAX_CONCURRENT_AGENTS = int(os.environ.get('MAX_CONCURRENT_AI_REQUESTS', 3))  # Conservative
    AGENT_TIMEOUT = int(os.environ.get('AI_TIMEOUT_SECONDS', 45))  # Shorter timeout
    ANALYSIS_CACHE_TTL = int(os.environ.get('CACHE_TTL', 600))  # Longer cache
    
    # File handling optimizations for Railway storage
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_FILE_SIZE', 25*1024*1024))  # 25MB for Railway
    ENABLE_FILE_CLEANUP = True
    FILE_CLEANUP_INTERVAL_HOURS = int(os.environ.get('FILE_CLEANUP_INTERVAL_HOURS', 12))
    
    # Queue management for Railway memory limits
    QUEUE_HIGH_PRIORITY_THRESHOLD = int(os.environ.get('QUEUE_HIGH_PRIORITY_THRESHOLD', 5))
    MAX_QUEUE_SIZE = int(os.environ.get('MAX_QUEUE_SIZE', 50))
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_HEADERS_ENABLED = True
    
    # Production monitoring
    MONITORING_ENABLED = True
    ERROR_THRESHOLD_PER_HOUR = int(os.environ.get('ERROR_THRESHOLD_PER_HOUR', 50))
    PERFORMANCE_MONITORING = True
    
    # Railway-specific production settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DATABASE_POOL_SIZE', 12)),
        'pool_recycle': int(os.environ.get('DATABASE_POOL_RECYCLE_TIME', 3600)),
        'pool_pre_ping': True,
        'max_overflow': int(os.environ.get('DATABASE_MAX_CONNECTIONS', 12)) - int(os.environ.get('DATABASE_POOL_SIZE', 12)),
        'pool_timeout': int(os.environ.get('DATABASE_CONNECTION_TIMEOUT', 45)),
        'echo': False  # Disable SQL echo in production
    }
    
    # File cleanup settings
    ENABLE_FILE_CLEANUP = True
    FILE_CLEANUP_INTERVAL_HOURS = int(os.environ.get('FILE_CLEANUP_INTERVAL_HOURS', 24))
    
    # Auto-scaling settings
    AUTO_SCALE_QUEUE_THRESHOLD = int(os.environ.get('AUTO_SCALE_QUEUE_THRESHOLD', 10))
    AUTO_SCALE_CPU_THRESHOLD = int(os.environ.get('AUTO_SCALE_CPU_THRESHOLD', 80))
    
    # Backup settings
    ENABLE_AUTOMATED_BACKUPS = os.environ.get('ENABLE_AUTOMATED_BACKUPS', 'true').lower() == 'true'
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', 30))

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'production_optimized': 'app.config.production_optimized.ProductionOptimizedConfig',  # New optimized config
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config_class(config_name):
    """Get configuration class, handling string imports for optimized configs."""
    config_obj = config.get(config_name)
    
    if isinstance(config_obj, str):
        # Handle string import for optimized configs
        module_path, class_name = config_obj.rsplit('.', 1)
        from importlib import import_module
        module = import_module(module_path)
        return getattr(module, class_name)
    
    return config_obj or config['default']
