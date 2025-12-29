#!/usr/bin/env python3
"""
Unified Deployment Script for HR Consultancy ATS v1.2
Handles all deployment scenarios with Smart Resource Scaling integration.
"""

import os
import sys
import logging
import traceback
import subprocess
import asyncio
from datetime import datetime
from pathlib import Path

class DeploymentManager:
    """Unified deployment manager with Smart Resource Scaling"""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.project_root = Path(__file__).parent
        self.scaling_enabled = os.getenv('ENABLE_SMART_SCALING', 'true').lower() == 'true'
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [DEPLOY] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def detect_environment(self):
        """Detect the deployment environment"""
        if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_PROJECT_ID'):
            return 'railway'
        elif os.getenv('DOCKER_CONTAINER'):
            return 'docker'
        elif os.path.exists('/.dockerenv'):
            return 'docker'
        else:
            return 'local'
    
    def railway_initialization(self):
        """Special initialization for Railway deployment with Smart Resource Scaling"""
        self.logger.info("=== RAILWAY DEPLOYMENT INITIALIZATION v1.2 ===")
        
        # Set default admin credentials if not provided
        if not os.getenv('DEFAULT_ADMIN_EMAIL'):
            os.environ['DEFAULT_ADMIN_EMAIL'] = 'admin@bearsystems.co.in'
        if not os.getenv('DEFAULT_ADMIN_PASSWORD'):
            os.environ['DEFAULT_ADMIN_PASSWORD'] = 'Benzie1!Benzie1!Benzie1!Benzie1!'
        
        self.logger.info(f"Admin user will be: {os.getenv('DEFAULT_ADMIN_EMAIL')}")
        
        try:
            # Import and create app to test basic functionality
            from app import create_app
            app = create_app('production')
            
            with app.app_context():
                from app import db
                
                # Create all tables
                self.logger.info("Creating database tables...")
                db.create_all()
                
                # Run migrations
                self.logger.info("Running database migrations...")
                try:
                    from flask_migrate import upgrade
                    upgrade()
                    self.logger.info("✓ Migrations completed")
                except Exception as e:
                    self.logger.warning(f"Migration issue (continuing): {e}")
                
                # Create default admin user
                self.logger.info("Checking/creating admin user...")
                self.create_default_admin()
                
                # Create necessary directories
                directories = [
                    'uploads',
                    'uploads/resumes', 
                    'uploads/batches',
                    'logs',
                    'metrics'  # For scaling system metrics
                ]
                
                for directory in directories:
                    os.makedirs(directory, exist_ok=True)
                    self.logger.info(f"✓ Directory created: {directory}")
                
                # Test model loading
                if hasattr(app, 'model_loader'):
                    models = app.model_loader.get_all_models(app)
                    self.logger.info(f"✓ Loaded {len(models)} models")
                
                # Initialize Smart Resource Scaling (if enabled)
                if self.scaling_enabled:
                    self.logger.info("Initializing Smart Resource Scaling system...")
                    try:
                        self._initialize_smart_scaling_sync()
                        self.logger.info("✓ Smart Resource Scaling initialized")
                    except Exception as scaling_error:
                        self.logger.warning(f"Smart scaling initialization failed: {scaling_error}")
                        self.logger.info("Continuing without smart scaling...")
                
                self.logger.info("✓ Railway initialization completed successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Railway initialization failed: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _initialize_smart_scaling_sync(self):
        """Initialize Smart Resource Scaling system synchronously"""
        try:
            # Set environment variables for production scaling
            os.environ.setdefault('ENVIRONMENT', 'production')
            os.environ.setdefault('MIN_WORKERS', '2')
            os.environ.setdefault('MAX_WORKERS', '8')
            os.environ.setdefault('ENABLE_INTELLIGENT_QUEUE', 'true')
            
            # Import scaling configuration
            from app.config.scaling_config import apply_environment_config
            apply_environment_config()
            
            self.logger.info("Smart Resource Scaling configuration applied")
            
        except ImportError as e:
            self.logger.warning(f"Smart scaling modules not found: {e}")
        except Exception as e:
            self.logger.error(f"Error initializing smart scaling: {e}")
            raise
    
    def install_dependencies(self):
        """Install Python dependencies"""
        self.logger.info("Installing Python dependencies...")
        
        # First install basic requirements
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
            ], check=True)
            
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
            ], check=True)
            
            self.logger.info("✓ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def setup_database(self):
        """Initialize database with migrations"""
        self.logger.info("Setting up database...")
        
        try:
            # Import here to avoid early import issues
            from app import create_app, db
            from flask_migrate import upgrade
            
            app = create_app('production')
            with app.app_context():
                # Create tables
                db.create_all()
                
                # Run migrations if they exist
                try:
                    upgrade()
                    self.logger.info("✓ Database migrations applied")
                except Exception as e:
                    self.logger.warning(f"Migration warning (continuing): {e}")
                
                # Create default admin user
                self.create_default_admin()
                
            self.logger.info("✓ Database setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Database setup failed: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    def create_default_admin(self):
        """Create default admin user if it doesn't exist"""
        try:
            from app.models.user import User
            from app.models import AdminUser
            from app.services.auth_manager import auth_manager
            from app import db
            
            admin_email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@bearsystems.co.in')
            admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'Benzie1!Benzie1!Benzie1!Benzie1!')
            desired_username = admin_email.split('@')[0]  # 'admin'
            
            self.logger.info(f"Checking for admin user: {admin_email}")
            
            # Check if admin user exists by email or username
            existing_admin_by_email = User.query.filter_by(email=admin_email).first()
            existing_admin_by_username = User.query.filter_by(username=desired_username).first()
            existing_admin = existing_admin_by_email or existing_admin_by_username
            
            if not existing_admin:
                self.logger.info(f"Creating admin user: {admin_email}")
                
                # Create new admin user
                admin_user = User(
                    email=admin_email,
                    username=desired_username,
                    password_hash=auth_manager.hash_password(admin_password),
                    first_name='System',
                    last_name='Administrator',
                    is_admin=True,
                    is_active=True,
                    credits_balance=10000  # High credit limit for admin
                )
                db.session.add(admin_user)
                db.session.flush()  # Get the user ID
                
                # Create admin profile
                admin_profile = AdminUser(
                    user_id=admin_user.id,
                    role='super_admin',
                    access_level=100,
                    can_access_all_users=True,
                    can_modify_credits=True,
                    can_manage_queue=True,
                    can_view_analytics=True,
                    can_manage_system=True,
                    can_access_sales_intelligence=True
                )
                db.session.add(admin_profile)
                db.session.commit()
                
                self.logger.info(f"✓ Default admin user created: {admin_email}")
                self.logger.info(f"✓ Admin profile created with super_admin role")
                
            elif existing_admin_by_username and not existing_admin_by_email:
                # Found user by username but not email - update the existing user
                self.logger.info(f"Found existing user with username '{desired_username}', updating to admin...")
                existing_admin_by_username.email = admin_email
                existing_admin_by_username.is_admin = True
                existing_admin_by_username.is_active = True
                existing_admin_by_username.credits_balance = max(existing_admin_by_username.credits_balance, 10000)
                
                # Verify admin profile exists
                admin_profile = AdminUser.query.filter_by(user_id=existing_admin_by_username.id).first()
                if not admin_profile:
                    self.logger.info("Creating admin profile for existing user...")
                    admin_profile = AdminUser(
                        user_id=existing_admin_by_username.id,
                        role='super_admin',
                        access_level=100,
                        can_access_all_users=True,
                        can_modify_credits=True,
                        can_manage_queue=True,
                        can_view_analytics=True,
                        can_manage_system=True,
                        can_access_sales_intelligence=True
                    )
                    db.session.add(admin_profile)
                
                db.session.commit()
                self.logger.info(f"✓ Updated existing user to admin: {admin_email}")
                existing_admin = existing_admin_by_username
                
            else:
                # Admin user already exists with correct email
                self.logger.info("✓ Admin user already exists")
                
                # Ensure user is marked as admin and active
                if not existing_admin.is_admin:
                    existing_admin.is_admin = True
                    self.logger.info("Updated user to admin status")
                
                if not existing_admin.is_active:
                    existing_admin.is_active = True
                    self.logger.info("Activated admin user")
                
                # Verify admin profile exists
                admin_profile = AdminUser.query.filter_by(user_id=existing_admin.id).first()
                if not admin_profile:
                    self.logger.info("Creating missing admin profile...")
                    admin_profile = AdminUser(
                        user_id=existing_admin.id,
                        role='super_admin',
                        access_level=100,
                        can_access_all_users=True,
                        can_modify_credits=True,
                        can_manage_queue=True,
                        can_view_analytics=True,
                        can_manage_system=True,
                        can_access_sales_intelligence=True
                    )
                    db.session.add(admin_profile)
                    db.session.commit()
                    self.logger.info("✓ Admin profile created")
                
            # Log summary of admin users
            admin_count = User.query.filter_by(is_admin=True).count()
            self.logger.info(f"✓ Total admin users in system: {admin_count}")
                
        except Exception as e:
            self.logger.error(f"Could not create admin user: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't fail the deployment for admin creation issues
            self.logger.warning("Continuing deployment without admin user creation")
    
    def verify_services(self):
        """Verify that all required services are accessible"""
        self.logger.info("Verifying external services...")
        
        # Check database connection
        try:
            from app import create_app, db
            app = create_app('production')
            with app.app_context():
                db.engine.execute('SELECT 1').fetchone()
            self.logger.info("✓ Database connection verified")
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return False
        
        # Check Ollama service (optional)
        ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        try:
            import requests
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.logger.info("✓ Ollama service accessible")
            else:
                self.logger.warning("⚠ Ollama service not accessible (continuing anyway)")
        except Exception as e:
            self.logger.warning(f"⚠ Ollama service check failed: {e} (continuing anyway)")
        
        return True
    
    def start_application(self):
        """Start the Flask application"""
        environment = self.detect_environment()
        self.logger.info(f"Starting application in {environment} environment...")
        
        if environment == 'railway':
            # Railway uses gunicorn with proper WSGI entry point
            port = int(os.getenv('PORT', 8000))
            cmd = [
                'gunicorn',
                '--bind', f'0.0.0.0:{port}',
                '--workers', '1',
                '--worker-class', 'eventlet',
                '--worker-connections', '1000',
                '--timeout', '120',
                '--keep-alive', '2',
                '--log-level', 'info',
                '--access-logfile', '-',
                '--error-logfile', '-',
                '--preload-app',  # Add preload for better eventlet compatibility
                'wsgi_production:application'  # Use the production-optimized WSGI entry point
            ]
        else:
            # Local development
            cmd = [sys.executable, 'run.py']
        
        self.logger.info(f"Executing: {' '.join(cmd)}")
        subprocess.run(cmd)
    
    def deploy(self):
        """Execute full deployment process"""
        environment = self.detect_environment()
        self.logger.info(f"🚀 Starting deployment for {environment} environment")
        
        steps = [
            ("Installing dependencies", self.install_dependencies),
            ("Setting up database", self.setup_database),
            ("Verifying services", self.verify_services),
            ("Starting application", self.start_application)
        ]
        
        for step_name, step_func in steps:
            self.logger.info(f"📋 {step_name}...")
            if step_func == self.start_application:
                # Don't check return value for start_application as it runs indefinitely
                step_func()
                break
            elif not step_func():
                self.logger.error(f"❌ {step_name} failed!")
                return False
        
        self.logger.info("✅ Deployment completed successfully!")
        return True

def main():
    """Main deployment entry point with command line argument support"""
    import argparse
    
    # Command line argument parsing
    parser = argparse.ArgumentParser(description='HR Consultancy ATS Deployment Manager')
    parser.add_argument('--railway-init', action='store_true', 
                       help='Run Railway-specific initialization only')
    parser.add_argument('--environment', choices=['local', 'railway', 'docker'], 
                       help='Force specific environment')
    parser.add_argument('--skip-deps', action='store_true', 
                       help='Skip dependency installation')
    
    args = parser.parse_args()
    
    try:
        manager = DeploymentManager()
        
        # Handle Railway initialization only
        if args.railway_init:
            manager.logger.info("Running Railway initialization only...")
            success = manager.railway_initialization()
            sys.exit(0 if success else 1)
        
        # Full deployment
        environment = args.environment or manager.detect_environment()
        manager.logger.info(f"Deploying to environment: {environment}")
        
        success = manager.deploy()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠ Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Deployment failed with unexpected error: {e}")
        logging.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
