#!/usr/bin/env python3
"""
WSGI entry point for production deployment
This file is used by WSGI servers like Gunicorn for production deployment
"""

import os
import sys
import logging

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Set production environment
os.environ.setdefault('NODE_ENV', 'production')

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Import the Flask application
    from app import app
    logger.info("Flask application imported successfully")
    
    # This is what WSGI servers will look for
    application = app
    
except Exception as e:
    logger.error(f"Failed to import Flask application: {e}")
    raise

if __name__ == "__main__":
    # For local development
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting Flask application on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
