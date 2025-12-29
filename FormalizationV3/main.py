#!/usr/bin/env python3
"""
Main entry point for HR ATS System
Refactored from monolithic app.py to clean modular architecture
"""

import os
import logging
from utils.logger_config import setup_logging
from app_factory import create_app

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    logger.info("🚀 Starting HR ATS System (Refactored Architecture)")
    
    # Create the application using factory pattern
    app = create_app()
    
    # Get port from environment (Railway/Heroku compatible)
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    
    # Production vs Development configuration
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"🌍 Starting server on {host}:{port}")
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

if __name__ == '__main__':
    main()
