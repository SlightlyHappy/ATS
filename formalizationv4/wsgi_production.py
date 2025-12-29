#!/usr/bin/env python3
"""
Production-ready WSGI entry point for Railway deployment.
Optimized for reliability, performance, and monitoring.
Fixed eventlet compatibility and application context issues.
"""

import os
import sys
import logging
import time
from pathlib import Path

# Skip eventlet entirely in Railway environment to prevent worker class conflicts
# Railway deployment uses gthread workers, not eventlet
EVENTLET_AVAILABLE = False
if os.environ.get('RAILWAY_ENVIRONMENT'):
    print("ℹ Railway environment detected - using gthread workers (no eventlet)")
else:
    # Conservative eventlet approach - only use if explicitly configured
    # This prevents the monkey patching context issues
    try:
        # Only use eventlet if explicitly configured as worker class
        if os.environ.get('WORKER_CLASS') == 'eventlet':
            import eventlet
            eventlet.monkey_patch()
            EVENTLET_AVAILABLE = True
            print("✓ Eventlet monkey patching applied (worker class: eventlet)")
        else:
            print("ℹ Using standard sync workers (no eventlet)")
    except ImportError:
        print("ℹ Eventlet not available, using standard threading")
    except Exception as e:
        print(f"⚠ Eventlet setup failed: {e}")

# Production Environment Detection
IS_PRODUCTION = bool(
    os.environ.get('RAILWAY_ENVIRONMENT') or 
    os.environ.get('RAILWAY_PROJECT_ID') or
    os.environ.get('GUNICORN_CMD_ARGS') or
    'gunicorn' in str(sys.argv)
)

# Configure production-grade logging
log_level = logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# Early path setup
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Suppress warnings for cleaner production logs
import warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='transformers')
warnings.filterwarnings('ignore', message='.*ALL_PRETRAINED_CONFIG_ARCHIVE_MAP.*')
warnings.filterwarnings('ignore', message='.*TypingOnly.*', category=UserWarning)

logger.info(f"🌍 Environment: {'PRODUCTION' if IS_PRODUCTION else 'DEVELOPMENT'}")
logger.info(f"🔧 Eventlet: {'ENABLED' if EVENTLET_AVAILABLE else 'DISABLED'}")

def create_production_app():
    """Create Flask application optimized for production"""
    logger.info("🚀 Starting production WSGI application...")
    
    try:
        # Apply compatibility patches early
        try:
            from app.compatibility_patch import apply_sqlalchemy_patches
            apply_sqlalchemy_patches()
            logger.info("✓ Applied compatibility patches")
        except ImportError:
            logger.warning("⚠ Compatibility patches not available")
        except Exception as e:
            logger.warning(f"⚠ Compatibility patch error: {e}")
        
        # Import app factory
        from app import create_app
        logger.info("✓ App factory imported")
        
        # Create application with production config
        app = create_app('production')
        logger.info("✓ Flask application created")
        
        # Production validation
        with app.app_context():
            # Test basic functionality
            try:
                from app import db
                # Quick database test
                db.engine.execute('SELECT 1')
                logger.info("✓ Database connection verified")
            except Exception as db_error:
                logger.warning(f"⚠ Database connection issue: {db_error}")
                # Continue - database might not be ready yet
            
            # Initialize monitoring scheduler safely
            try:
                from app.services.monitoring_scheduler import init_monitoring_scheduler, start_monitoring
                scheduler = init_monitoring_scheduler(app)
                
                # Start monitoring only in production and if not in debug mode
                if IS_PRODUCTION and not app.debug:
                    start_monitoring()
                    logger.info("✓ Monitoring scheduler started for production")
                else:
                    logger.info("✓ Monitoring scheduler initialized (not started in dev/debug)")
                    
            except Exception as monitoring_error:
                logger.warning(f"⚠ Monitoring scheduler initialization failed: {monitoring_error}")
                # Continue without monitoring - not critical for basic functionality
            
            # Verify models can be loaded
            try:
                if hasattr(app, 'model_loader'):
                    models = app.model_loader.get_all_models(app)
                    logger.info(f"✓ Loaded {len(models)} models")
                else:
                    logger.warning("⚠ Model loader not available")
            except Exception as model_error:
                logger.warning(f"⚠ Model loading issue: {model_error}")
        
        logger.info("🎉 Production WSGI application ready")
        return app
        
    except Exception as e:
        logger.error(f"❌ Critical error creating application: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # In production, create a minimal fallback app
        if IS_PRODUCTION:
            try:
                from flask import Flask, jsonify
                fallback_app = Flask(__name__)
                
                @fallback_app.route('/health')
                def health():
                    return jsonify({
                        'status': 'error',
                        'message': 'Application failed to start properly',
                        'timestamp': int(time.time())
                    }), 500
                
                @fallback_app.route('/')
                def root():
                    return jsonify({
                        'error': 'Application startup failed',
                        'timestamp': int(time.time())
                    }), 500
                
                logger.warning("⚠ Returning fallback app for Railway health checks")
                return fallback_app
            except Exception as fallback_error:
                logger.error(f"Even fallback app failed: {fallback_error}")
        
        raise

# Create the application instance
logger.info("Creating application instance...")
application = create_production_app()

# Add production middleware and error handlers
@application.errorhandler(500)
def handle_500(error):
    """Production error handler"""
    logger.error(f"Internal server error: {error}")
    return {'error': 'Internal server error', 'timestamp': int(time.time())}, 500

@application.errorhandler(404)
def handle_404(error):
    """Production 404 handler"""
    return {'error': 'Not found', 'timestamp': int(time.time())}, 404

# Production health check
@application.route('/health')
def health_check():
    """Comprehensive health check for Railway"""
    try:
        status = {
            'status': 'healthy',
            'timestamp': int(time.time()),
            'environment': 'production' if IS_PRODUCTION else 'development',
            'checks': {}
        }
        
        # Database check
        try:
            from app import db
            with application.app_context():
                db.engine.execute('SELECT 1')
            status['checks']['database'] = 'healthy'
        except Exception:
            status['checks']['database'] = 'unhealthy'
            status['status'] = 'degraded'
        
        # Model check
        try:
            with application.app_context():
                if hasattr(application, 'model_loader'):
                    models = application.model_loader.get_all_models(application)
                    status['checks']['models'] = f'{len(models)} loaded'
                else:
                    status['checks']['models'] = 'not available'
        except Exception:
            status['checks']['models'] = 'error'
        
        return status, 200 if status['status'] == 'healthy' else 503
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': int(time.time())
        }, 500

# Development server (for local testing only)
if __name__ == "__main__":
    if not IS_PRODUCTION:
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Starting development server on port {port}")
        application.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True
        )
    else:
        logger.error("❌ Use gunicorn or another WSGI server for production!")
        sys.exit(1)
warnings.filterwarnings('ignore', category=FutureWarning, module='transformers')
warnings.filterwarnings('ignore', message='.*ALL_PRETRAINED_CONFIG_ARCHIVE_MAP.*')
warnings.filterwarnings('ignore', message='.*TypingOnly.*', category=UserWarning)

# STEP 3: Set up minimal logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s]: %(message)s'
)
logger = logging.getLogger(__name__)

# STEP 4: Fix path and environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force production environment
os.environ['FLASK_ENV'] = 'production'

# STEP 5: Create application with maximum error resilience
application = None

def create_production_app():
    """Create Flask app with production-specific optimizations"""
    try:
        logger.info("🚀 Creating production Flask application...")
        
        # Import app factory
        from app import create_app
        
        # Create application in production mode
        app = create_app('production')
        
        # Verify app was created successfully
        if app is None:
            raise RuntimeError("App factory returned None")
            
        # Test basic app functionality
        with app.app_context():
            logger.info("✓ Application context test passed")
            
        logger.info("✅ Production application created successfully")
        return app
        
    except Exception as e:
        logger.error(f"❌ Failed to create production app: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

# Main application creation logic
try:
    application = create_production_app()
    logger.info("✅ Production application created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create production application: {str(e)}")
    import traceback
    logger.error(f"Full traceback: {traceback.format_exc()}")
    raise RuntimeError(f"Production application creation failed: {str(e)}")

# Validate final application
if application is None:
    raise RuntimeError("Application is None after creation")

logger.info("🎉 WSGI production application ready for deployment")

# For direct execution (testing only)
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Running application directly on port {port}")
    application.run(host='0.0.0.0', port=port, debug=False)
