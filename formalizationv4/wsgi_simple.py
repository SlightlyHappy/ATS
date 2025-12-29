#!/usr/bin/env python3
"""
Simplified WSGI entry point that avoids eventlet conflicts.
Use this when eventlet causes issues with Flask context.
"""

import os
import sys
import logging

# Set up early logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s]: %(message)s'
)
logger = logging.getLogger(__name__)

# Set up the application path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger.info('🌐 Starting simplified WSGI application...')

try:
    # Import app factory directly without eventlet
    from app import create_app
    logger.info('✓ App factory imported successfully')
    
    # Create application instance for production
    application = create_app('production')
    logger.info('✓ Application created successfully')
    
    # Test basic functionality
    with application.app_context():
        logger.info('✓ Application context established')
        application.logger.info('Simplified WSGI application ready for production deployment')
    
except Exception as e:
    logger.error(f'❌ Failed to create application: {str(e)}')
    import traceback
    logger.error(f'Full traceback: {traceback.format_exc()}')
    raise RuntimeError(f"Failed to create Flask application: {str(e)}")

# Validate application was created
if application is None:
    raise RuntimeError("Failed to create Flask application")

logger.info('🚀 Simplified WSGI application ready for deployment')

# For direct execution (development/testing only)
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    application.run(host='0.0.0.0', port=port, debug=False)
