"""
Phase 3 Production Configuration
Enhanced production configuration with Redis clustering, auto-scaling,
and background task optimization.
"""
import os
from datetime import timedelta

class Phase3ProductionConfig:
    """Production configuration with Phase 3 enterprise features."""
    
    # =============================================================================
    # EXISTING PRODUCTION SETTINGS (Enhanced)
    # =============================================================================
    
    # Basic Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:pass@localhost/hrdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_timeout': 30,
        'pool_recycle': 300,
        'max_overflow': 0,
        'pool_pre_ping': True
    }
    
    # Enhanced Cache Configuration
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_KEY_PREFIX = 'hr_ats:'
    
    # Session Configuration
    SESSION_TYPE = 'redis'
    SESSION_REDIS = os.environ.get('REDIS_URL') or 'redis://localhost:6379/1'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'hr_session:'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Security Headers
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year
    
    # =============================================================================
    # PHASE 3 REDIS CLUSTER CONFIGURATION
    # =============================================================================
    
    # Redis Cluster Settings
    ENABLE_REDIS_CLUSTER = os.environ.get('ENABLE_REDIS_CLUSTER', 'false').lower() == 'true'
    REDIS_CLUSTER_NODES = os.environ.get('REDIS_CLUSTER_NODES', '').split(',') if os.environ.get('REDIS_CLUSTER_NODES') else []
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
    REDIS_MAX_CONNECTIONS = int(os.environ.get('REDIS_MAX_CONNECTIONS', '100'))
    REDIS_HEALTH_CHECK_INTERVAL = int(os.environ.get('REDIS_HEALTH_CHECK_INTERVAL', '30'))
    REDIS_CONNECTION_TIMEOUT = int(os.environ.get('REDIS_CONNECTION_TIMEOUT', '5'))
    REDIS_SOCKET_KEEPALIVE = os.environ.get('REDIS_SOCKET_KEEPALIVE', 'true').lower() == 'true'
    REDIS_CLUSTER_REQUIRE_FULL_COVERAGE = os.environ.get('REDIS_CLUSTER_REQUIRE_FULL_COVERAGE', 'false').lower() == 'true'
    
    # Cache Warming Configuration
    ENABLE_CACHE_WARMING = os.environ.get('ENABLE_CACHE_WARMING', 'true').lower() == 'true'
    CACHE_WARM_ON_STARTUP = os.environ.get('CACHE_WARM_ON_STARTUP', 'true').lower() == 'true'
    CACHE_WARM_STRATEGY = os.environ.get('CACHE_WARM_STRATEGY', 'critical_endpoints')
    CACHE_WARM_BATCH_SIZE = int(os.environ.get('CACHE_WARM_BATCH_SIZE', '50'))
    CACHE_WARM_MAX_TIME = int(os.environ.get('CACHE_WARM_MAX_TIME', '300'))
    
    # Cache Invalidation Configuration
    ENABLE_INTELLIGENT_INVALIDATION = os.environ.get('ENABLE_INTELLIGENT_INVALIDATION', 'true').lower() == 'true'
    CACHE_INVALIDATION_BATCH_SIZE = int(os.environ.get('CACHE_INVALIDATION_BATCH_SIZE', '100'))
    CACHE_CASCADE_INVALIDATION = os.environ.get('CACHE_CASCADE_INVALIDATION', 'true').lower() == 'true'
    
    # =============================================================================
    # PHASE 3 AUTO-SCALING CONFIGURATION
    # =============================================================================
    
    # Auto-Scaling Settings
    ENABLE_AUTO_SCALING = os.environ.get('ENABLE_AUTO_SCALING', 'false').lower() == 'true'
    AUTOSCALER_MIN_INSTANCES = int(os.environ.get('AUTOSCALER_MIN_INSTANCES', '1'))
    AUTOSCALER_MAX_INSTANCES = int(os.environ.get('AUTOSCALER_MAX_INSTANCES', '10'))
    AUTOSCALER_TARGET_CPU = float(os.environ.get('AUTOSCALER_TARGET_CPU', '70.0'))
    AUTOSCALER_TARGET_MEMORY = float(os.environ.get('AUTOSCALER_TARGET_MEMORY', '80.0'))
    AUTOSCALER_SCALE_UP_THRESHOLD = float(os.environ.get('AUTOSCALER_SCALE_UP_THRESHOLD', '80.0'))
    AUTOSCALER_SCALE_DOWN_THRESHOLD = float(os.environ.get('AUTOSCALER_SCALE_DOWN_THRESHOLD', '30.0'))
    AUTOSCALER_SCALE_UP_COOLDOWN = int(os.environ.get('AUTOSCALER_SCALE_UP_COOLDOWN', '300'))
    AUTOSCALER_SCALE_DOWN_COOLDOWN = int(os.environ.get('AUTOSCALER_SCALE_DOWN_COOLDOWN', '600'))
    
    # Predictive Scaling
    ENABLE_PREDICTIVE_SCALING = os.environ.get('ENABLE_PREDICTIVE_SCALING', 'true').lower() == 'true'
    PREDICTIVE_SCALING_WINDOW = int(os.environ.get('PREDICTIVE_SCALING_WINDOW', '15'))
    PREDICTIVE_SCALING_ACCURACY_THRESHOLD = float(os.environ.get('PREDICTIVE_SCALING_ACCURACY_THRESHOLD', '0.8'))
    
    # Load Balancing
    ENABLE_INTELLIGENT_LOAD_BALANCING = os.environ.get('ENABLE_INTELLIGENT_LOAD_BALANCING', 'true').lower() == 'true'
    LOAD_BALANCER_ALGORITHM = os.environ.get('LOAD_BALANCER_ALGORITHM', 'weighted_round_robin')
    CIRCUIT_BREAKER_FAILURE_THRESHOLD = int(os.environ.get('CIRCUIT_BREAKER_FAILURE_THRESHOLD', '5'))
    CIRCUIT_BREAKER_TIMEOUT = int(os.environ.get('CIRCUIT_BREAKER_TIMEOUT', '60'))
    
    # Cloud Provider Configuration
    PRIMARY_CLOUD_PROVIDER = os.environ.get('PRIMARY_CLOUD_PROVIDER', 'railway')
    SECONDARY_CLOUD_PROVIDER = os.environ.get('SECONDARY_CLOUD_PROVIDER', '')
    MULTI_CLOUD_FAILOVER_ENABLED = os.environ.get('MULTI_CLOUD_FAILOVER_ENABLED', 'false').lower() == 'true'
    
    # Railway-specific Configuration
    RAILWAY_PROJECT_ID = os.environ.get('RAILWAY_PROJECT_ID', '')
    RAILWAY_ENVIRONMENT_ID = os.environ.get('RAILWAY_ENVIRONMENT_ID', '')
    RAILWAY_SERVICE_ID = os.environ.get('RAILWAY_SERVICE_ID', '')
    RAILWAY_API_TOKEN = os.environ.get('RAILWAY_TOKEN', '')
    
    # =============================================================================
    # PHASE 3 BACKGROUND TASK CONFIGURATION
    # =============================================================================
    
    # Background Task Optimizer
    ENABLE_TASK_OPTIMIZER = os.environ.get('ENABLE_TASK_OPTIMIZER', 'true').lower() == 'true'
    MAX_BACKGROUND_TASKS = int(os.environ.get('MAX_BACKGROUND_TASKS', '20'))
    ENABLE_DYNAMIC_TASK_SCALING = os.environ.get('ENABLE_DYNAMIC_TASK_SCALING', 'true').lower() == 'true'
    ENABLE_TASK_LOAD_BALANCING = os.environ.get('ENABLE_TASK_LOAD_BALANCING', 'true').lower() == 'true'
    ENABLE_BATCH_PROCESSING = os.environ.get('ENABLE_BATCH_PROCESSING', 'true').lower() == 'true'
    
    # Worker Pool Configuration
    BACKGROUND_WORKER_LIMITS = {
        'cpu_intensive': int(os.environ.get('CPU_INTENSIVE_WORKERS', '6')),
        'io_intensive': int(os.environ.get('IO_INTENSIVE_WORKERS', '12')),
        'memory_intensive': int(os.environ.get('MEMORY_INTENSIVE_WORKERS', '3')),
        'general': int(os.environ.get('GENERAL_WORKERS', '8'))
    }
    
    # Task Priority Configuration
    ENABLE_PRIORITY_ESCALATION = os.environ.get('ENABLE_PRIORITY_ESCALATION', 'true').lower() == 'true'
    PRIORITY_ESCALATION_TIMEOUT = int(os.environ.get('PRIORITY_ESCALATION_TIMEOUT', '3600'))
    
    # Batch Processing Configuration
    BATCH_SIZE_LIMITS = {
        'analysis': int(os.environ.get('ANALYSIS_BATCH_SIZE', '5')),
        'notification': int(os.environ.get('NOTIFICATION_BATCH_SIZE', '15')),
        'cleanup': int(os.environ.get('CLEANUP_BATCH_SIZE', '25')),
        'default': int(os.environ.get('DEFAULT_BATCH_SIZE', '10'))
    }
    
    BATCH_TIMEOUT_SECONDS = int(os.environ.get('BATCH_TIMEOUT_SECONDS', '60'))
    BATCH_MAX_WAIT_TIME = int(os.environ.get('BATCH_MAX_WAIT_TIME', '120'))
    
    # Task Retry Configuration
    DEFAULT_TASK_MAX_RETRIES = int(os.environ.get('DEFAULT_TASK_MAX_RETRIES', '3'))
    DEFAULT_TASK_TIMEOUT = int(os.environ.get('DEFAULT_TASK_TIMEOUT', '300'))
    TASK_RETRY_BACKOFF_FACTOR = float(os.environ.get('TASK_RETRY_BACKOFF_FACTOR', '2.0'))
    
    # =============================================================================
    # PHASE 3 MONITORING AND LOGGING
    # =============================================================================
    
    # Enhanced Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    ENABLE_STRUCTURED_LOGGING = os.environ.get('ENABLE_STRUCTURED_LOGGING', 'true').lower() == 'true'
    LOG_FORMAT = os.environ.get('LOG_FORMAT', 'json')
    
    # Performance Monitoring
    ENABLE_PERFORMANCE_MONITORING = os.environ.get('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
    PERFORMANCE_METRICS_INTERVAL = int(os.environ.get('PERFORMANCE_METRICS_INTERVAL', '60'))
    METRICS_RETENTION_DAYS = int(os.environ.get('METRICS_RETENTION_DAYS', '30'))
    
    # Health Check Configuration
    HEALTH_CHECK_ENABLED = os.environ.get('HEALTH_CHECK_ENABLED', 'true').lower() == 'true'
    HEALTH_CHECK_INTERVAL = int(os.environ.get('HEALTH_CHECK_INTERVAL', '30'))
    HEALTH_CHECK_TIMEOUT = int(os.environ.get('HEALTH_CHECK_TIMEOUT', '10'))
    
    # Alert Configuration
    ENABLE_ALERTING = os.environ.get('ENABLE_ALERTING', 'false').lower() == 'true'
    ALERT_EMAIL_RECIPIENTS = os.environ.get('ALERT_EMAIL_RECIPIENTS', '').split(',') if os.environ.get('ALERT_EMAIL_RECIPIENTS') else []
    ALERT_WEBHOOK_URL = os.environ.get('ALERT_WEBHOOK_URL', '')
    
    # =============================================================================
    # PHASE 3 SECURITY ENHANCEMENTS
    # =============================================================================
    
    # Enhanced Security Settings
    ENABLE_RATE_LIMITING = os.environ.get('ENABLE_RATE_LIMITING', 'true').lower() == 'true'
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', '100'))
    RATE_LIMIT_BURST = int(os.environ.get('RATE_LIMIT_BURST', '200'))
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization', 'X-Requested-With']
    
    # API Security
    API_KEY_REQUIRED = os.environ.get('API_KEY_REQUIRED', 'false').lower() == 'true'
    API_RATE_LIMIT_PER_HOUR = int(os.environ.get('API_RATE_LIMIT_PER_HOUR', '1000'))
    
    # =============================================================================
    # PHASE 3 FEATURE FLAGS
    # =============================================================================
    
    # Feature Toggle Configuration
    FEATURE_FLAGS = {
        'redis_cluster': os.environ.get('FEATURE_REDIS_CLUSTER', 'false').lower() == 'true',
        'auto_scaling': os.environ.get('FEATURE_AUTO_SCALING', 'false').lower() == 'true',
        'predictive_scaling': os.environ.get('FEATURE_PREDICTIVE_SCALING', 'false').lower() == 'true',
        'background_optimization': os.environ.get('FEATURE_BACKGROUND_OPTIMIZATION', 'true').lower() == 'true',
        'intelligent_caching': os.environ.get('FEATURE_INTELLIGENT_CACHING', 'true').lower() == 'true',
        'multi_cloud_support': os.environ.get('FEATURE_MULTI_CLOUD', 'false').lower() == 'true',
        'advanced_monitoring': os.environ.get('FEATURE_ADVANCED_MONITORING', 'true').lower() == 'true',
        'batch_processing': os.environ.get('FEATURE_BATCH_PROCESSING', 'true').lower() == 'true',
        'circuit_breaker': os.environ.get('FEATURE_CIRCUIT_BREAKER', 'true').lower() == 'true',
        'load_balancing': os.environ.get('FEATURE_LOAD_BALANCING', 'true').lower() == 'true'
    }
    
    # =============================================================================
    # PHASE 3 INTEGRATION CONFIGURATION
    # =============================================================================
    
    # Phase 3 Services Configuration
    PHASE3_CONFIG = {
        'redis_cluster': {
            'enabled': ENABLE_REDIS_CLUSTER,
            'nodes': REDIS_CLUSTER_NODES,
            'password': REDIS_PASSWORD,
            'max_connections': REDIS_MAX_CONNECTIONS,
            'health_check_interval': REDIS_HEALTH_CHECK_INTERVAL,
            'connection_timeout': REDIS_CONNECTION_TIMEOUT,
            'socket_keepalive': REDIS_SOCKET_KEEPALIVE
        },
        'auto_scaler': {
            'enabled': ENABLE_AUTO_SCALING,
            'min_instances': AUTOSCALER_MIN_INSTANCES,
            'max_instances': AUTOSCALER_MAX_INSTANCES,
            'target_cpu_utilization': AUTOSCALER_TARGET_CPU,
            'target_memory_utilization': AUTOSCALER_TARGET_MEMORY,
            'enable_predictive_scaling': ENABLE_PREDICTIVE_SCALING,
            'prediction_window_minutes': PREDICTIVE_SCALING_WINDOW
        },
        'task_optimizer': {
            'enabled': ENABLE_TASK_OPTIMIZER,
            'max_concurrent_tasks': MAX_BACKGROUND_TASKS,
            'enable_dynamic_scaling': ENABLE_DYNAMIC_TASK_SCALING,
            'enable_batch_processing': ENABLE_BATCH_PROCESSING,
            'worker_limits': BACKGROUND_WORKER_LIMITS,
            'batch_size_limits': BATCH_SIZE_LIMITS
        }
    }
    
    # =============================================================================
    # DEVELOPMENT OVERRIDES (For local development)
    # =============================================================================
    
    @classmethod
    def get_development_overrides(cls):
        """Get development-specific configuration overrides."""
        return {
            # Disable enterprise features for local development
            'ENABLE_REDIS_CLUSTER': False,
            'ENABLE_AUTO_SCALING': False,
            'ENABLE_PREDICTIVE_SCALING': False,
            'ENABLE_MULTI_CLOUD': False,
            
            # Reduce resource limits for development
            'MAX_BACKGROUND_TASKS': 5,
            'BACKGROUND_WORKER_LIMITS': {
                'cpu_intensive': 2,
                'io_intensive': 3,
                'memory_intensive': 1,
                'general': 2
            },
            
            # Enable debug features
            'ENABLE_PERFORMANCE_MONITORING': True,
            'LOG_LEVEL': 'DEBUG',
            'HEALTH_CHECK_INTERVAL': 10
        }
    
    # =============================================================================
    # CONFIGURATION VALIDATION
    # =============================================================================
    
    @classmethod
    def validate_configuration(cls):
        """Validate Phase 3 configuration settings."""
        validation_errors = []
        
        # Validate Redis Cluster Configuration
        if cls.ENABLE_REDIS_CLUSTER:
            if not cls.REDIS_CLUSTER_NODES:
                validation_errors.append("Redis cluster enabled but no nodes specified")
            
            if not cls.REDIS_PASSWORD:
                validation_errors.append("Redis cluster enabled but no password specified")
        
        # Validate Auto-Scaling Configuration
        if cls.ENABLE_AUTO_SCALING:
            if cls.AUTOSCALER_MIN_INSTANCES >= cls.AUTOSCALER_MAX_INSTANCES:
                validation_errors.append("Auto-scaler min instances must be less than max instances")
            
            if not cls.RAILWAY_PROJECT_ID and cls.PRIMARY_CLOUD_PROVIDER == 'railway':
                validation_errors.append("Railway auto-scaling enabled but no project ID specified")
        
        # Validate Background Task Configuration
        if cls.ENABLE_TASK_OPTIMIZER:
            if cls.MAX_BACKGROUND_TASKS <= 0:
                validation_errors.append("Max background tasks must be greater than 0")
            
            total_workers = sum(cls.BACKGROUND_WORKER_LIMITS.values())
            if total_workers > cls.MAX_BACKGROUND_TASKS * 2:
                validation_errors.append("Total worker pool size exceeds reasonable limits")
        
        return validation_errors
    
    # =============================================================================
    # CONFIGURATION SUMMARY
    # =============================================================================
    
    @classmethod
    def get_configuration_summary(cls):
        """Get a summary of Phase 3 configuration for logging/debugging."""
        return {
            'phase3_features': {
                'redis_cluster': cls.ENABLE_REDIS_CLUSTER,
                'auto_scaling': cls.ENABLE_AUTO_SCALING,
                'predictive_scaling': cls.ENABLE_PREDICTIVE_SCALING,
                'task_optimization': cls.ENABLE_TASK_OPTIMIZER,
                'cache_warming': cls.ENABLE_CACHE_WARMING,
                'intelligent_invalidation': cls.ENABLE_INTELLIGENT_INVALIDATION
            },
            'resource_limits': {
                'max_background_tasks': cls.MAX_BACKGROUND_TASKS,
                'worker_pool_limits': cls.BACKGROUND_WORKER_LIMITS,
                'redis_max_connections': cls.REDIS_MAX_CONNECTIONS,
                'autoscaler_max_instances': cls.AUTOSCALER_MAX_INSTANCES
            },
            'monitoring': {
                'performance_monitoring': cls.ENABLE_PERFORMANCE_MONITORING,
                'health_checks': cls.HEALTH_CHECK_ENABLED,
                'alerting': cls.ENABLE_ALERTING,
                'structured_logging': cls.ENABLE_STRUCTURED_LOGGING
            }
        }


# =============================================================================
# ENVIRONMENT-SPECIFIC CONFIGURATIONS
# =============================================================================

class Phase3DevelopmentConfig(Phase3ProductionConfig):
    """Development configuration with Phase 3 features disabled or reduced."""
    
    # Override production settings for development
    DEBUG = True
    TESTING = False
    
    # Disable enterprise features
    ENABLE_REDIS_CLUSTER = False
    ENABLE_AUTO_SCALING = False
    ENABLE_PREDICTIVE_SCALING = False
    MULTI_CLOUD_FAILOVER_ENABLED = False
    
    # Reduce resource limits
    MAX_BACKGROUND_TASKS = 5
    BACKGROUND_WORKER_LIMITS = {
        'cpu_intensive': 2,
        'io_intensive': 3,
        'memory_intensive': 1,
        'general': 2
    }
    
    # Enable debug features
    LOG_LEVEL = 'DEBUG'
    HEALTH_CHECK_INTERVAL = 10
    PERFORMANCE_METRICS_INTERVAL = 30


class Phase3TestingConfig(Phase3ProductionConfig):
    """Testing configuration for Phase 3 features."""
    
    # Testing-specific settings
    TESTING = True
    DEBUG = True
    
    # Use in-memory databases
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    CACHE_TYPE = 'simple'
    SESSION_TYPE = 'filesystem'
    
    # Disable external services
    ENABLE_REDIS_CLUSTER = False
    ENABLE_AUTO_SCALING = False
    ENABLE_ALERTING = False
    
    # Minimal resource usage
    MAX_BACKGROUND_TASKS = 2
    BACKGROUND_WORKER_LIMITS = {
        'cpu_intensive': 1,
        'io_intensive': 1,
        'memory_intensive': 1,
        'general': 1
    }
    
    # Fast testing intervals
    HEALTH_CHECK_INTERVAL = 5
    PERFORMANCE_METRICS_INTERVAL = 10


# =============================================================================
# CONFIGURATION FACTORY
# =============================================================================

def get_phase3_config(environment='production'):
    """Get Phase 3 configuration based on environment."""
    config_map = {
        'production': Phase3ProductionConfig,
        'development': Phase3DevelopmentConfig,
        'testing': Phase3TestingConfig
    }
    
    config_class = config_map.get(environment, Phase3ProductionConfig)
    
    # Validate configuration
    validation_errors = config_class.validate_configuration()
    if validation_errors:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Phase 3 configuration validation errors: {validation_errors}")
    
    return config_class
