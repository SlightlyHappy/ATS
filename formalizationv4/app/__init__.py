from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_socketio import SocketIO
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

# Ensure Flask-SocketIO uses threading mode (must be set early)
if not os.environ.get('FLASK_SOCKETIO_ASYNC_MODE'):
    os.environ['FLASK_SOCKETIO_ASYNC_MODE'] = 'threading'

# Import compatibility patches first
try:
    from app.compatibility_patch import apply_sqlalchemy_patches
    apply_sqlalchemy_patches()
except ImportError:
    # Patches not available, continue without them
    pass

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='threading',  # Explicitly force threading mode
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25
)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_app(config_name=None):
    """Application factory pattern with enhanced error handling."""
    # Apply early fixes for common deployment issues
    import warnings
    warnings.filterwarnings('ignore', category=FutureWarning, module='transformers')
    warnings.filterwarnings('ignore', message='.*ALL_PRETRAINED_CONFIG_ARCHIVE_MAP.*')
    
    # Fix transformers auto configuration issues that can cause eventlet problems
    try:
        import transformers.models.auto.configuration_auto
        if hasattr(transformers.models.auto.configuration_auto, 'ALL_PRETRAINED_CONFIG_ARCHIVE_MAP'):
            # Prevent the problematic lazy loading that conflicts with eventlet
            pass
    except ImportError:
        pass
    except Exception:
        # Ignore any transformer-related errors during startup
        pass
    
    # Handle potential Flask context issues with eventlet
    from flask import has_app_context, has_request_context
    
    # Early logging setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s [%(name)s]: %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info('='*50)
    logger.info('STARTING FLASK APPLICATION INITIALIZATION')
    logger.info('='*50)
    
    # Create Flask app with error protection
    try:
        app = Flask(__name__)
        logger.info('Flask app instance created')
    except Exception as e:
        logger.error(f'Failed to create Flask instance: {str(e)}')
        raise
    
    # Load configuration with error handling
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    logger.info(f'Loading configuration for environment: {config_name}')
    
    try:
        from app.config import get_config_class
        config_class = get_config_class(config_name)
        app.config.from_object(config_class)
        logger.info(f'Configuration loaded successfully: {config_name}')
        
        # Log optimization status
        if 'optimized' in config_name.lower():
            logger.info('🚀 PRODUCTION OPTIMIZED CONFIGURATION ACTIVE')
            logger.info('✓ Enhanced database pooling enabled')
            logger.info('✓ Performance monitoring configured')
            logger.info('✓ Advanced caching settings applied')
        
        # Log key configuration values (without sensitive data)
        logger.info(f'Database URI configured: {bool(app.config.get("SQLALCHEMY_DATABASE_URI"))}')
        logger.info(f'Upload folder: {app.config.get("UPLOAD_FOLDER")}')
        logger.info(f'Secret key configured: {bool(app.config.get("SECRET_KEY"))}')
        
    except Exception as e:
        logger.error(f'Failed to load configuration: {str(e)}')
        # Fallback to regular config mapping
        try:
            from app.config import config
            app.config.from_object(config[config_name])
            logger.warning(f'Loaded fallback configuration: {config_name}')
        except Exception as fallback_error:
            logger.error(f'Fallback configuration also failed: {str(fallback_error)}')
            raise
    
    # Initialize extensions with production safety
    logger.info('Initializing Flask extensions...')
    
    # Set production mode flag
    is_production = app.config.get('ENV') == 'production' or os.environ.get('RAILWAY_ENVIRONMENT')
    
    try:
        # Initialize core extensions first
        db.init_app(app)
        logger.info('✓ SQLAlchemy initialized')
        
        # Expose database connection pool for Phase 2 integration checks
        try:
            app.db_pool = db.get_engine(app).pool
            logger.info('✓ Database connection pool exposed on app.db_pool')
        except Exception as e:
            logger.warning(f'Could not expose database pool: {str(e)}')
        
        migrate.init_app(app, db)
        logger.info('✓ Flask-Migrate initialized')
        
        cache.init_app(app)
        logger.info('✓ Flask-Cache initialized')
        
        limiter.init_app(app)
        logger.info('✓ Flask-Limiter initialized')
        
        # Initialize SocketIO with production-optimized settings
        try:
            if is_production:
                # Production: Use threading for stability
                socketio.init_app(app, 
                    cors_allowed_origins="*",
                    async_mode='threading',
                    logger=False,  # Reduce noise in production logs
                    engineio_logger=False
                )
                logger.info('✓ SocketIO initialized with threading mode (production)')
            else:
                # Development: More verbose logging
                socketio.init_app(app, 
                    cors_allowed_origins="*",
                    async_mode='threading',
                    logger=True,
                    engineio_logger=True
                )
                logger.info('✓ SocketIO initialized with threading mode (development)')
                
        except Exception as socket_error:
            logger.warning(f'SocketIO initialization issue: {str(socket_error)}')
            # Minimal fallback for production stability
            socketio.init_app(app, 
                cors_allowed_origins="*",
                async_mode='threading',
                manage_session=False,
                logger=False,
                engineio_logger=False
            )
            logger.info('✓ SocketIO initialized with minimal fallback mode')
            
    except Exception as e:
        logger.error(f'Failed to initialize extensions: {str(e)}')
        import traceback
        logger.error(f'Traceback: {traceback.format_exc()}')
        raise
        logger.error(f'Failed to initialize extensions: {str(e)}')
        raise
    
    # Initialize WebSocket service
    logger.info('Initializing WebSocket service...')
    try:
        from app.services.websocket_service import WebSocketService
        websocket_service = WebSocketService(socketio)
        websocket_service.register_handlers()
        
        # Store websocket service in app config for access by other services
        app.websocket_service = websocket_service
        logger.info('✓ WebSocket service initialized')
    except Exception as e:
        logger.error(f'Failed to initialize WebSocket service: {str(e)}')
        raise
    
    # Configure CORS for Railway deployment
    logger.info('Configuring CORS...')
    cors_origins = [
        "http://localhost:3000", 
        "https://*.railway.app",
        "https://hrt-bearsystems.vercel.app"  # New frontend URL
    ]
    
    # Add frontend URL and additional origins from config
    if app.config.get('FRONTEND_URL'):
        cors_origins.append(app.config['FRONTEND_URL'])
        logger.info(f'Added frontend URL to CORS: {app.config["FRONTEND_URL"]}')
    
    additional_origins = app.config.get('ADDITIONAL_CORS_ORIGINS', [])
    if additional_origins:
        cors_origins.extend([origin.strip() for origin in additional_origins if origin.strip()])
        logger.info(f'Added additional CORS origins: {additional_origins}')
    
    logger.info(f'CORS origins configured: {cors_origins}')
    
    try:
        CORS(app, resources={
            r"/api/*": {
                "origins": cors_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True
            }
        })
        logger.info('✓ CORS configured successfully')
    except Exception as e:
        logger.error(f'Failed to configure CORS: {str(e)}')
        raise
    
    # Initialize enhanced services (Phase 1 Optimizations)
    logger.info('Initializing enhanced services...')
    try:
        # Initialize enhanced cache service
        from app.services.enhanced_cache_service import enhanced_cache
        enhanced_cache.init_app(app)
        app.enhanced_cache = enhanced_cache
        logger.info('✓ Enhanced cache service initialized')
        
        # Initialize performance monitoring service
        from app.services.performance_monitoring_service import performance_monitor
        performance_monitor.init_app(app)
        app.performance_monitor = performance_monitor
        logger.info('✓ Performance monitoring service initialized')
        
        logger.info('✓ All enhanced services initialized successfully')
    except Exception as e:
        logger.error(f'Failed to initialize enhanced services: {str(e)}')
        # Don't raise - these are optimizations that shouldn't break the app
        logger.warning('Continuing without enhanced services...')

    # Initialize Phase 2 Load-Aware Processing System
    logger.info('Initializing Phase 2 Load-Aware Processing System...')
    try:
        from app.phase2_integration import integrate_phase2_services
        phase2_success = integrate_phase2_services(app)
        if phase2_success:
            logger.info('✅ Phase 2 Load-Aware Processing System initialized successfully')
        else:
            logger.warning('⚠️ Phase 2 system initialization incomplete - continuing with reduced functionality')
    except Exception as e:
        logger.error(f'Failed to initialize Phase 2 system: {str(e)}')
        logger.warning('Continuing without Phase 2 load-aware processing...')

    # Register blueprints
    logger.info('Registering blueprints...')
    try:
        from app.api import api_bp
        from app.api.auth import auth_bp
        from app.api.queue import queue_bp
        from app.api.websocket import websocket_bp
        from app.api.sales import sales_bp
        from app.api.admin import admin_bp
        from app.api.monitoring import monitoring_bp
        from app.api.pipeline import pipeline_bp
        from app.api.communication import communication_bp
        from app.api.legal import legal_bp
        from app.api.batch import batch_bp  # New batch API blueprint
        from app.api.optimization_report import optimization_bp  # New optimization report blueprint
        
        # Expose Batch API service handle for Phase 2 integration checks
        try:
            app.batch_api = batch_bp
            logger.info('✓ Batch API service exposed on app.batch_api')
        except Exception as e:
            logger.warning(f'Could not expose Batch API service: {str(e)}')
        
        logger.info('✓ All blueprints imported successfully')
        
        # Register auth blueprint first (it has its own prefix)
        app.register_blueprint(auth_bp)  # Auth routes now at /api/v1/auth
        logger.info('✓ Auth blueprint registered at /api/v1/auth')
        
        # Register API blueprint (main API routes)
        app.register_blueprint(api_bp, url_prefix='/api/v1')
        logger.info('✓ API blueprint registered at /api/v1')
        
        # Register batch API blueprint (new optimization feature)
        app.register_blueprint(batch_bp, url_prefix='/api/v1/batch')
        logger.info('✓ Batch API blueprint registered at /api/v1/batch')
        
        app.register_blueprint(queue_bp, url_prefix='/api/v1/queue')
        logger.info('✓ Queue blueprint registered at /api/v1/queue')
        
        app.register_blueprint(websocket_bp, url_prefix='/api/v1/websocket')
        logger.info('✓ WebSocket blueprint registered at /api/v1/websocket')
        
        app.register_blueprint(pipeline_bp, url_prefix='/api/v1/pipeline')
        logger.info('✓ Pipeline blueprint registered at /api/v1/pipeline')
        
        app.register_blueprint(communication_bp)  # Already has prefix in blueprint definition
        logger.info('✓ Communication blueprint registered at /api/v1/communication')
        
        app.register_blueprint(legal_bp)  # Already has prefix in blueprint definition
        logger.info('✓ Legal blueprint registered at /api/legal')
        
        app.register_blueprint(sales_bp)  # Already has prefix in blueprint definition
        logger.info('✓ Sales blueprint registered')
        
        app.register_blueprint(admin_bp)  # Already has prefix in blueprint definition
        logger.info('✓ Admin blueprint registered')
        
        app.register_blueprint(monitoring_bp)  # Already has prefix in blueprint definition
        logger.info('✓ Monitoring blueprint registered')
        
        # Register optimization report blueprint (new Phase 1 feature)
        app.register_blueprint(optimization_bp)
        logger.info('✓ Optimization report blueprint registered at /api/v1/optimization')
        
    except Exception as e:
        logger.error(f'Failed to register blueprints: {str(e)}')
        raise
    
    # Add root route handler
    @app.route('/')
    def root_handler():
        """Root endpoint - redirect to API info."""
        return {
            'message': 'HR Consultancy ATS Backend API',
            'version': '1.3',
            'status': 'online',
            'api_base': '/api/v1',
            'endpoints': {
                'api_info': '/api/v1',
                'health': '/api/v1/health',
                'auth': '/api/v1/auth',
                'documentation': '/api/v1/dashboard'
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    @app.route('/health')
    def root_health():
        """Simple health check at root level."""
        return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
    
    logger.info('✓ Root routes registered')
    
    # Initialize error handling system
    logger.info('Initializing error handling system...')
    try:
        from app.services.error_handler import production_logger
        production_logger.init_app(app)
        logger.info('✓ Error handling system initialized')
    except Exception as e:
        logger.error(f'Failed to initialize error handling system: {str(e)}')
        raise

    # Initialize authentication manager
    logger.info('Initializing authentication manager...')
    try:
        from app.services.auth_manager import auth_manager
        auth_manager.init_app(app)
        logger.info('✓ Authentication manager initialized')
    except Exception as e:
        logger.error(f'Failed to initialize authentication manager: {str(e)}')
        raise

    # Initialize analytics middleware for enhanced monitoring
    logger.info('Initializing analytics middleware...')
    try:
        from app.services.analytics_middleware import analytics_middleware
        analytics_middleware.init_app(app)
        logger.info('✓ Analytics middleware initialized')
    except Exception as e:
        logger.error(f'Failed to initialize analytics middleware: {str(e)}')
        raise
    
    # Configure logging for Railway deployment
    logger.info('Configuring application logging...')
    if not app.debug and not app.testing:
        # Railway uses stdout/stderr for logging
        log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
        logger.info(f'Setting log level to: {log_level}')
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        
        # Also create file logger if LOG_TO_FILE is enabled
        if app.config.get('LOG_TO_FILE', 'true').lower() == 'true':
            if not os.path.exists('logs'):
                os.makedirs('logs', exist_ok=True)
                logger.info('Created logs directory')
            
            try:
                file_handler = RotatingFileHandler(
                    app.config.get('LOG_FILE_PATH', 'logs/app.log'), 
                    maxBytes=10240000,  # 10MB
                    backupCount=10
                )
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
                ))
                file_handler.setLevel(log_level)
                app.logger.addHandler(file_handler)
                logger.info('✓ File logging configured')
            except Exception as e:
                logger.warning(f'Failed to setup file logging: {str(e)}')
        
        app.logger.setLevel(log_level)
        app.logger.info('ResumeAI Pro startup - Railway deployment')
        logger.info('✓ Production logging configured')
    else:
        logger.info('Development mode - using default logging')
    
    # Create upload and processed directories
    logger.info('Creating required directories...')
    upload_folder = app.config['UPLOAD_FOLDER']
    processed_folder = app.config.get('PROCESSED_FOLDER', 'processed')
    resume_storage = app.config.get('RESUME_STORAGE_PATH', 'uploads/resumes')
    batch_storage = app.config.get('BATCH_STORAGE_PATH', 'uploads/batches')
    
    directories = [upload_folder, processed_folder, resume_storage, batch_storage, 'logs']
    for folder in directories:
        try:
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
                logger.info(f'✓ Created directory: {folder}')
            else:
                logger.info(f'✓ Directory already exists: {folder}')
        except Exception as e:
            logger.error(f'Failed to create directory {folder}: {str(e)}')
            raise
    
    # Initialize production health monitoring
    if config_name == 'production':
        logger.info('Initializing production health monitoring...')
        try:
            from app.services.health_monitor import health_monitor
            health_monitor.init_app(app)
            logger.info('✓ Health monitoring initialized')
        except Exception as e:
            logger.warning(f'⚠ Health monitoring failed to initialize: {e}')
    
    # Import models to ensure they are registered with SQLAlchemy (after db initialization)
    logger.info('Setting up lazy model loading...')
    try:
        # Use a push/pop context pattern to avoid context issues with eventlet
        with app.app_context():
            from app.models.lazy_loader import model_loader
            
            # Use lazy loading to avoid circular imports
            models = model_loader.load_models(app)
            logger.info(f'✓ Loaded {len(models)} models successfully via lazy loader')
            
            # Store model loader in app for later use
            app.model_loader = model_loader
        
    except Exception as e:
        logger.error(f'Failed to setup model loading: {str(e)}')
        import traceback
        logger.error(f'Traceback: {traceback.format_exc()}')
        logger.warning('Continuing startup without models - they will be loaded on first use')
    
    # Initialize HR Pipeline Scheduler (only once)
    logger.info('Initializing HR Pipeline Scheduler...')
    try:
        from app.services.hr_pipeline_scheduler import hr_pipeline_scheduler
        hr_pipeline_scheduler.init_app(app)
        logger.info('✓ HR Pipeline Scheduler initialized')
    except Exception as e:
        logger.error(f'Failed to initialize HR Pipeline Scheduler: {str(e)}')
        logger.warning('Continuing without HR Pipeline Scheduler - automation features disabled')
    
    # Initialize Monitoring Scheduler with better error handling
    logger.info('Initializing Monitoring Scheduler...')
    try:
        # Delay import to avoid eventlet conflicts
        import importlib
        monitoring_module = importlib.import_module('app.services.monitoring_scheduler')
        init_monitoring_scheduler = getattr(monitoring_module, 'init_monitoring_scheduler')
        monitoring_scheduler = init_monitoring_scheduler(app)
        logger.info('✓ Monitoring Scheduler initialized')
    except Exception as e:
        logger.error(f'Failed to initialize Monitoring Scheduler: {str(e)}')
        logger.warning('Continuing without Monitoring Scheduler - monitoring features disabled')
        # Set a dummy attribute to prevent further errors
        app.monitoring_scheduler = None
    
    # Auto-fix HR Templates issues on startup
    logger.info('Checking HR Templates system...')
    try:
        with app.app_context():
            from app.services.hr_templates_autofix import HRTemplatesAutoFixService
            
            # Quick check for issues
            issues = HRTemplatesAutoFixService.detect_issues()
            if any(issues.values()):
                logger.info('HR Templates issues detected, attempting auto-fix...')
                results = HRTemplatesAutoFixService.auto_fix_all_issues()
                
                if results.get('overall_success'):
                    logger.info('✓ HR Templates auto-fix completed successfully')
                else:
                    logger.warning(f'⚠️ HR Templates auto-fix partially failed: {results.get("message")}')
                    logger.info('💡 Admin can manually fix via: POST /api/v1/admin/hr-templates/auto-fix')
            else:
                logger.info('✓ HR Templates system is healthy')
                
    except Exception as e:
        logger.error(f'HR Templates auto-fix failed: {str(e)}')
        logger.info('💡 Admin can manually diagnose via: GET /api/v1/admin/hr-templates/diagnose')
        logger.warning('Continuing startup without HR Templates auto-fix')
    
    logger.info('='*50)
    logger.info('FLASK APPLICATION INITIALIZATION COMPLETED')
    logger.info('='*50)
    
    return app
