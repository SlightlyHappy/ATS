#!/usr/bin/env python3
"""
Production startup script for Railway deployment.
Handles database initialization, migrations, and application startup.
"""

import os
import sys
import logging
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def wait_for_database(max_attempts=30, delay=2):
    """Wait for database to be available"""
    logger.info("Waiting for database to be ready...")
    
    for attempt in range(max_attempts):
        try:
            from app import create_app
            app = create_app('production')
            
            with app.app_context():
                from app import db
                db.engine.execute('SELECT 1')
                logger.info("✓ Database is ready")
                return True
                
        except Exception as e:
            logger.info(f"Database not ready (attempt {attempt + 1}/{max_attempts}): {e}")
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                logger.error("❌ Database failed to become ready")
                return False
    
    return False

def run_migrations():
    """Run database migrations"""
    logger.info("Running database migrations...")
    
    try:
        from app import create_app
        from flask_migrate import upgrade
        
        app = create_app('production')
        
        with app.app_context():
            upgrade()
            logger.info("✓ Migrations completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def initialize_application():
    """Initialize the application"""
    logger.info("Initializing application...")
    
    try:
        from app import create_app
        app = create_app('production')
        
        with app.app_context():
            # Test basic functionality
            from app import db
            
            # Ensure tables exist
            db.create_all()
            
            # Test model loading
            if hasattr(app, 'model_loader'):
                models = app.model_loader.get_all_models(app)
                logger.info(f"✓ Loaded {len(models)} models")
            
            # Create necessary directories
            directories = [
                app.config.get('UPLOAD_FOLDER', 'uploads'),
                'uploads/resumes',
                'uploads/batches',
                'logs'
            ]
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"✓ Directory ready: {directory}")
            
            logger.info("✓ Application initialized successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ Application initialization failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main startup function"""
    logger.info("🚀 Starting Railway production deployment...")
    
    # Check environment
    railway_env = os.environ.get('RAILWAY_ENVIRONMENT')
    if railway_env:
        logger.info(f"Railway environment: {railway_env}")
    
    # Step 1: Wait for database
    if not wait_for_database():
        logger.error("❌ Startup failed: Database not ready")
        sys.exit(1)
    
    # Step 2: Run migrations
    if not run_migrations():
        logger.error("❌ Startup failed: Migration errors")
        sys.exit(1)
    
    # Step 3: Initialize application
    if not initialize_application():
        logger.error("❌ Startup failed: Application initialization errors")
        sys.exit(1)
    
    logger.info("🎉 Railway deployment startup completed successfully!")
    
    # If running as main script, start the application
    if len(sys.argv) > 1 and sys.argv[1] == '--start-server':
        logger.info("Starting production server...")
        os.system('gunicorn wsgi_production:application --bind 0.0.0.0:$PORT --workers 2 --worker-class sync --timeout 60')

if __name__ == "__main__":
    main()
