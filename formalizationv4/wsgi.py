#!/usr/bin/env python3
"""
WSGI entry point for production deployment.
Handles proper eventlet monkey patching before any other imports.
"""

# CRITICAL: Apply eventlet monkey patching BEFORE any other imports
import os
import sys

# Force eventlet monkey patching for production environments
if (os.environ.get('RAILWAY_ENVIRONMENT') or 
    os.environ.get('GUNICORN_CMD_ARGS') or 
    'gunicorn' in str(sys.argv) or
    'eventlet' in str(sys.argv)):
    
    try:
        import eventlet
        # Apply more selective monkey patching to avoid Flask context issues
        eventlet.monkey_patch(
            os=True,
            select=True,
            socket=True,
            time=True,
            thread=False,  # Don't patch threading - let Flask handle its own threading
            all=False      # Be selective to avoid conflicts
        )
        # Set a flag to indicate patching was done
        setattr(eventlet, '_wsgi_patched', True)
        print("✓ Eventlet monkey patching applied successfully (selective mode)")
    except ImportError:
        print("⚠ eventlet not available, continuing without it")
    except Exception as e:
        print(f"⚠ eventlet monkey patching failed: {e}, continuing without it")

# Apply Python 3.13 compatibility patches early
import warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='transformers')
warnings.filterwarnings('ignore', message='.*ALL_PRETRAINED_CONFIG_ARCHIVE_MAP.*')
warnings.filterwarnings('ignore', message='.*TypingOnly.*', category=UserWarning)
warnings.filterwarnings('ignore', message='.*directly inherits TypingOnly.*', category=UserWarning)

# Protect against eventlet monkey patching conflicts with Werkzeug
try:
    import werkzeug.local
    # Temporarily protect Werkzeug locals from being monkey patched
    if hasattr(werkzeug.local, 'LocalProxy'):
        _original_getattribute = werkzeug.local.LocalProxy.__getattribute__
except ImportError:
    pass

# Fix SQLAlchemy Python 3.13 compatibility issues early
try:
    import sqlalchemy.sql.elements
    if hasattr(sqlalchemy.sql.elements, 'SQLCoreOperations'):
        try:
            if hasattr(sqlalchemy.sql.elements.SQLCoreOperations, '__firstlineno__'):
                delattr(sqlalchemy.sql.elements.SQLCoreOperations, '__firstlineno__')
            if hasattr(sqlalchemy.sql.elements.SQLCoreOperations, '__static_attributes__'):
                delattr(sqlalchemy.sql.elements.SQLCoreOperations, '__static_attributes__')
        except (AttributeError, TypeError):
            pass
except Exception:
    pass

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s]: %(message)s'
)
logger = logging.getLogger(__name__)

# Set up the application path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create application directly without fallbacks
application = None

try:
    logger.info('🌐 Starting WSGI application import...')
    
    # Check if eventlet monkey patching is active
    eventlet_active = False
    try:
        import eventlet
        eventlet_active = hasattr(eventlet, '_wsgi_patched')
        if eventlet_active:
            logger.info('✓ Eventlet monkey patching is active')
        else:
            logger.info('ℹ Eventlet available but not monkey patched')
    except ImportError:
        logger.info('ℹ Eventlet not available')
    
    # Import app factory directly
    from app import create_app
    logger.info('✓ App factory imported successfully')
    
    # Create application instance for production
    application = create_app('production')
    logger.info('✓ Application created successfully')
    
    # Test basic functionality
    with application.app_context():
        logger.info('✓ Application context established')
        application.logger.info('WSGI application ready for production deployment')
    
except Exception as e:
    logger.error(f'❌ Failed to create application: {str(e)}')
    import traceback
    logger.error(f'Full traceback: {traceback.format_exc()}')
    raise RuntimeError(f"Failed to create Flask application: {str(e)}")

# Validate application was created
if application is None:
    raise RuntimeError("Failed to create Flask application")

logger.info('🚀 WSGI application ready for deployment')

# For direct execution (development/testing only)
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    application.run(host='0.0.0.0', port=port, debug=False)
