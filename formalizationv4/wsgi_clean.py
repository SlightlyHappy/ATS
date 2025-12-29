#!/usr/bin/env python3
"""
Clean WSGI entry point for Railway deployment - NO EVENTLET.
This file completely avoids eventlet to ensure gthread workers work properly.
"""

import os
import sys
import logging

# CRITICAL: Force Flask-SocketIO to use threading instead of eventlet
# This must be set BEFORE any imports that might import eventlet
os.environ['FLASK_SOCKETIO_ASYNC_MODE'] = 'threading'

# Prevent accidental eventlet imports by removing it from the path
# This ensures that even if something tries to import eventlet, it will fail gracefully
import importlib.util
if importlib.util.find_spec("eventlet") is not None:
    print("⚠️ WARNING: eventlet found in environment but will be ignored")
    print("🔧 Flask-SocketIO configured for threading mode")

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure Railway environment is detected
if os.environ.get('RAILWAY_ENVIRONMENT'):
    logger.info("🚂 Railway environment detected - using gthread workers")
else:
    logger.info("🔧 Development environment - using threading")

logger.info("🔧 Flask-SocketIO configured for threading mode")

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the Flask application
try:
    logger.info("📦 Importing Flask application...")
    from run import app
    logger.info("✅ Flask application imported successfully")
    
    # The WSGI application that Gunicorn will serve
    application = app
    
    # Log the configuration
    logger.info(f"🌐 Application ready for WSGI deployment")
    logger.info(f"🔧 Flask environment: {app.config.get('ENV', 'unknown')}")
    logger.info(f"🔐 Debug mode: {app.debug}")
    
except Exception as e:
    logger.error(f"❌ Failed to import Flask application: {str(e)}")
    raise

# Health check function for the application
def health_check():
    """Simple health check for the application"""
    try:
        with application.app_context():
            return True
    except Exception:
        return False

if __name__ == '__main__':
    # This won't be called by Gunicorn, but useful for testing
    logger.info("⚠️ Running Flask app directly (not recommended for production)")
    application.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
