"""
Production-ready database migration system for Railway deployment.
Replaces basic db.create_all() with proper Alembic migrations.
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from alembic import command
from alembic.config import Config
import logging
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database initialization, migrations, and versioning for production."""
    
    def __init__(self, app: Flask, db: SQLAlchemy):
        self.app = app
        self.db = db
        self.migrate = Migrate(app, db)
        
    def initialize_production_database(self):
        """Initialize database for production with proper migrations."""
        try:
            with self.app.app_context():
                # Check if database exists and has tables
                inspector = self.db.inspect(self.db.engine)
                existing_tables = inspector.get_table_names()
                
                if not existing_tables:
                    logger.info("Fresh database detected. Creating initial schema...")
                    self.create_initial_migration()
                else:
                    logger.info("Existing database detected. Checking migration status...")
                    self.check_migration_status()
                    
                # Run any pending migrations
                self.run_migrations()
                
                # Create default admin user if needed
                self.create_default_admin()
                
                logger.info("Database initialization completed successfully")
                return True
                
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            return False
    
    def create_initial_migration(self):
        """Create initial migration for fresh database."""
        try:
            # Generate initial migration
            command.revision(
                self.get_alembic_config(),
                message="Initial database schema",
                autogenerate=True
            )
            logger.info("Initial migration created")
        except Exception as e:
            logger.error(f"Failed to create initial migration: {str(e)}")
            raise
    
    def check_migration_status(self):
        """Check current migration status."""
        try:
            config = self.get_alembic_config()
            # This will show current migration status
            command.current(config)
        except Exception as e:
            logger.warning(f"Could not check migration status: {str(e)}")
    
    def run_migrations(self):
        """Run pending migrations."""
        try:
            config = self.get_alembic_config()
            command.upgrade(config, "head")
            logger.info("Database migrations completed")
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            raise
    
    def get_alembic_config(self):
        """Get Alembic configuration."""
        config = Config()
        config.set_main_option("script_location", "migrations")
        config.set_main_option("sqlalchemy.url", self.app.config['DATABASE_URL'])
        return config
    
    def create_default_admin(self):
        """Create default admin user if it doesn't exist."""
        try:
            from app.models import User, AdminUser
            from app.services.auth_manager import auth_manager
            
            admin_email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@bearsystems.co.in')
            admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'Benzie1!Benzie1!Benzie1!Benzie1!')
            existing_admin = User.query.filter_by(email=admin_email).first()
            
            if not existing_admin:
                # Create admin user with password
                admin_user = User(
                    email=admin_email,
                    username=admin_email.split('@')[0],
                    password_hash=auth_manager.hash_password(admin_password),
                    first_name='System',
                    last_name='Administrator',
                    is_admin=True,
                    is_active=True,
                    credits_balance=10000  # High credit limit for admin
                )
                self.db.session.add(admin_user)
                self.db.session.flush()  # Get the user ID
                
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
                self.db.session.add(admin_profile)
                self.db.session.commit()
                
                logger.info(f"Default admin user created: {admin_email} with password")
            else:
                # Update existing admin if no password is set
                if not existing_admin.password_hash:
                    existing_admin.password_hash = auth_manager.hash_password(admin_password)
                    existing_admin.username = admin_email.split('@')[0] if not existing_admin.username else existing_admin.username
                    existing_admin.is_active = True
                    self.db.session.commit()
                    logger.info(f"Password set for existing admin user: {admin_email}")
                else:
                    logger.info("Default admin user already exists with password")
                
        except Exception as e:
            logger.error(f"Failed to create default admin: {str(e)}")
            self.db.session.rollback()
    
    def validate_database_schema(self):
        """Validate that all required tables and indexes exist."""
        required_tables = [
            'users', 'credit_transactions', 'resumes', 'analyses',
            'analysis_queue', 'batch_uploads', 'admin_users',
            'admin_actions', 'system_configurations', 'admin_notifications'
        ]
        
        try:
            inspector = self.db.inspect(self.db.engine)
            existing_tables = inspector.get_table_names()
            
            missing_tables = set(required_tables) - set(existing_tables)
            if missing_tables:
                logger.error(f"Missing required tables: {missing_tables}")
                return False
            
            # Check critical indexes
            self.validate_indexes()
            
            logger.info("Database schema validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Database schema validation failed: {str(e)}")
            return False
    
    def validate_indexes(self):
        """Validate that critical indexes exist."""
        critical_indexes = [
            ('users', 'idx_users_email'),
            ('analysis_queue', 'idx_queue_status'),
            ('resumes', 'idx_resumes_user_id'),
            ('analyses', 'idx_analyses_resume_id')
        ]
        
        inspector = self.db.inspect(self.db.engine)
        
        for table_name, index_name in critical_indexes:
            indexes = inspector.get_indexes(table_name)
            index_names = [idx['name'] for idx in indexes]
            
            if index_name not in index_names:
                logger.warning(f"Missing critical index: {index_name} on {table_name}")
    
    def backup_database(self):
        """Create database backup (Railway-specific)."""
        # Implementation would depend on Railway's backup capabilities
        # For now, log the backup request
        logger.info("Database backup requested - implement Railway-specific backup")
    
    def get_database_health(self):
        """Get database health metrics."""
        try:
            with self.app.app_context():
                # Test basic connectivity
                self.db.session.execute(self.db.text('SELECT 1'))
                
                # Get table counts
                from app.models import User, Resume, Analysis, AnalysisQueue
                
                health_metrics = {
                    'status': 'healthy',
                    'tables': {
                        'users': User.query.count(),
                        'resumes': Resume.query.count(),
                        'analyses': Analysis.query.count(),
                        'queue_items': AnalysisQueue.query.count()
                    },
                    'database_size': self.get_database_size()
                }
                
                return health_metrics
                
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {'status': 'unhealthy', 'error': str(e)}
    
    def get_database_size(self):
        """Get estimated database size."""
        try:
            # PostgreSQL specific query to get database size
            result = self.db.session.execute(
                self.db.text("SELECT pg_size_pretty(pg_database_size(current_database()))")
            ).scalar()
            return result
        except:
            return "Unknown"
