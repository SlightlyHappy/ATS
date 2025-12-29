#!/usr/bin/env python3
"""
Backward compatibility layer for the refactored HR ATS System
This file maintains the same interface as the original app.py while using the new modular architecture
"""

import logging
from app_factory import create_app

logger = logging.getLogger(__name__)

# Create the application using the new factory pattern
app = create_app()

# For backward compatibility, expose the same interface as the original app.py
def get_app():
    """Get the Flask application instance"""
    return app

# For direct execution compatibility
if __name__ == '__main__':
    import os
    
    # Get port from environment (Railway/Heroku compatible)
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    
    # Production vs Development configuration
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"🌍 Starting server on {host}:{port} (Compatibility Mode)")
    logger.info(f"🔧 Debug mode: {debug}")
    
    # Check if SocketIO is available for enhanced features
    try:
        socketio = getattr(app, 'socketio', None)
        if socketio:
            logger.info("🔌 Starting with SocketIO support")
            socketio.run(app, host=host, port=port, debug=debug)
        else:
            logger.info("🔌 Starting without SocketIO (basic mode)")
            app.run(host=host, port=port, debug=debug)
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        # Fallback to basic Flask app
        app.run(host=host, port=port, debug=debug)
