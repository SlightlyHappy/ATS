#!/usr/bin/env python3
"""
Application Factory for HR ATS System
Clean separation of concerns with modular initialization
"""

import os
import logging
from flask import Flask
from flask_cors import CORS

from config import Config
try:
    from core.initializers import (
        ComponentInitializer,
        MiddlewareInitializer,
        RoutesInitializer
    )
    from core.health_manager import HealthManager
    from utils.logger_config import setup_logging
    from services.cache_manager import initialize_cache_manager
except ImportError as e:
    # Fallback imports if modules are missing
    print(f"Warning: Some modules not available: {e}")
    ComponentInitializer = None
    MiddlewareInitializer = None
    RoutesInitializer = None
    HealthManager = None
    setup_logging = None
    initialize_cache_manager = None

logger = logging.getLogger(__name__)

def create_app(config_name='default'):
    """
    Application factory function
    Creates and configures the Flask application with all components
    """
    # Setup logging first
    if setup_logging:
        setup_logging()
    
    logger.info("🏭 Starting HR ATS Application Factory...")
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    config = Config()
    app.config.from_object(config)
    logger.info("✅ Configuration loaded")
    
    # Setup CORS
    _setup_cors(app)
    logger.info("✅ CORS configured")
    
    # Initialize cache manager
    if initialize_cache_manager:
        cache_manager = initialize_cache_manager()
        app.cache_manager = cache_manager
        logger.info("✅ Cache manager initialized")
    
    # Check if we have all required modules
    if not all([ComponentInitializer, MiddlewareInitializer, RoutesInitializer, HealthManager]):
        logger.warning("⚠️ Some modules missing, creating minimal app")
        return _create_minimal_app(app)
    
    # Initialize core components
    component_init = ComponentInitializer(app)
    components = component_init.initialize_all()
    logger.info("✅ Core components initialized")
    
    # Setup middleware
    middleware_init = MiddlewareInitializer(app, components)
    middleware_init.setup_all()
    logger.info("✅ Middleware configured")
    
    # Setup health management
    health_manager = HealthManager(app, components)
    health_manager.register_endpoints()
    logger.info("✅ Health management configured")
    
    # Register all routes
    routes_init = RoutesInitializer(app, components)
    routes_init.register_all()
    logger.info("✅ Routes registered")
    
    # Store components in app context for access
    app.hr_components = components
    
    logger.info("🎉 HR ATS Application created successfully!")
    return app

def _create_minimal_app(app):
    """Create minimal app if some modules are missing"""
    from datetime import datetime
    from flask import jsonify
    
    @app.route('/health', methods=['GET'])
    @app.route('/', methods=['GET'])
    def health():
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "3.0.0-refactored-minimal",
            "message": "HR ATS System Operational (Minimal Mode)"
        })
    
    logger.info("🎉 Minimal HR ATS Application created!")
    return app

def _setup_cors(app):
    """Configure CORS for production deployment"""
    allowed_origins = [
        "https://hrtool-sable.vercel.app",
        "https://hrtbearsystems.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    
    # Add environment-specific origins
    if os.getenv('FRONTEND_URL'):
        allowed_origins.append(os.getenv('FRONTEND_URL'))
    if os.getenv('ADMIN_FRONTEND_URL'):
        allowed_origins.append(os.getenv('ADMIN_FRONTEND_URL'))
        
    logger.info(f"CORS configured for origins: {allowed_origins}")
        
    CORS(
        app,
        origins=allowed_origins,
        supports_credentials=True,
        allow_headers=['Content-Type', 'Authorization', 'Accept', 'X-Requested-With'],
        methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        expose_headers=['Content-Range', 'X-Content-Range']
    )
