import os
import logging
import sys
import traceback
import argparse
import warnings

# Skip eventlet monkey patching in Railway environment to prevent conflicts
# Eventlet causes issues with gthread worker class and SQLAlchemy threading
# EVENTLET COMPLETELY DISABLED FOR RAILWAY DEPLOYMENT
# Railway uses gthread workers, eventlet conflicts with Flask/Werkzeug
# Never import eventlet in production to prevent Gunicorn auto-detection

# Apply Python 3.13 compatibility patches early
try:
    # Suppress SQLAlchemy Python 3.13 compatibility warnings
    warnings.filterwarnings('ignore', message='.*TypingOnly.*', category=UserWarning)
    warnings.filterwarnings('ignore', message='.*directly inherits TypingOnly.*', category=UserWarning)
    
    # Fix SQLAlchemy SQLCoreOperations compatibility issue with Python 3.13
    import sqlalchemy.sql.elements
    if hasattr(sqlalchemy.sql.elements, 'SQLCoreOperations'):
        try:
            # Remove problematic attributes that cause the inheritance issue
            if hasattr(sqlalchemy.sql.elements.SQLCoreOperations, '__firstlineno__'):
                delattr(sqlalchemy.sql.elements.SQLCoreOperations, '__firstlineno__')
            if hasattr(sqlalchemy.sql.elements.SQLCoreOperations, '__static_attributes__'):
                delattr(sqlalchemy.sql.elements.SQLCoreOperations, '__static_attributes__')
        except (AttributeError, TypeError):
            pass
except Exception:
    pass

def setup_logging(level='INFO', include_file=False):
    """Setup comprehensive logging with optional file output"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if include_file and not os.environ.get('RAILWAY_ENVIRONMENT'):
        # Only add file logging in non-Railway environments
        try:
            os.makedirs('logs', exist_ok=True)
            file_handler = logging.FileHandler('logs/startup.log')
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s [%(name)s]: %(message)s'
            ))
            handlers.append(file_handler)
        except Exception:
            pass  # Skip file logging if it fails
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s %(levelname)s [%(name)s]: %(message)s',
        handlers=handlers,
        force=True
    )

def parse_args():
    """Parse command line arguments for different startup modes"""
    parser = argparse.ArgumentParser(description='ResumeAI Pro Application Server')
    parser.add_argument('--mode', choices=['production', 'development', 'test', 'diagnostics'], 
                       default=os.environ.get('FLASK_ENV', 'production'),
                       help='Application mode')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default=os.environ.get('LOG_LEVEL', 'INFO'),
                       help='Logging level')
    parser.add_argument('--diagnostics', action='store_true',
                       help='Run diagnostics before starting')
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 8000)),
                       help='Port to run on (development mode only)')
    return parser.parse_args()

def run_diagnostics():
    """Run basic diagnostics to check system health"""
    logger = logging.getLogger(__name__)
    logger.info('Running system diagnostics...')
    
    # Check required environment variables
    required_vars = ['DATABASE_URL'] if os.environ.get('FLASK_ENV') == 'production' else []
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.warning(f'Missing environment variables: {missing_vars}')
    
    # Check file system
    required_dirs = ['app', 'app/models', 'app/api', 'app/services']
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            logger.error(f'Missing required directory: {dir_path}')
            return False
    
    logger.info('✓ System diagnostics passed')
    return True

def create_application(env='production'):
    """Create Flask application with enhanced error handling"""
    logger = logging.getLogger(__name__)
    
    logger.info('='*60)
    logger.info('STARTING RESUMEAI PRO APPLICATION')
    logger.info('='*60)
    
    # Log environment information
    logger.info(f'Python version: {sys.version}')
    logger.info(f'Working directory: {os.getcwd()}')
    logger.info(f'Environment: {env}')
    logger.info(f'Port: {os.environ.get("PORT", "Not set")}')
    
    # Import Flask application with additional error handling
    logger.info('Importing Flask application...')
    try:
        # Apply additional SQLAlchemy fixes before importing
        import sqlalchemy
        logger.info(f'SQLAlchemy version: {sqlalchemy.__version__}')
        
        # Import with proper exception handling for eventlet issues
        try:
            from app import create_app, db, socketio
        except RuntimeError as re:
            if 'Working outside of' in str(re):
                logger.warning(f'Flask context issue during import: {str(re)}')
                logger.info('Retrying import with application context setup...')
                # This might happen due to eventlet monkey patching issues
                from app import create_app, db, socketio
            else:
                raise
        
        logger.info('✓ Flask imports successful')
    except Exception as e:
        logger.error(f'Failed to import Flask application: {str(e)}')
        logger.error(f'Traceback: {traceback.format_exc()}')
        raise
    
    # Create Flask application
    logger.info(f'Creating Flask application instance for {env}...')
    try:
        app = create_app(env)
        
        # Test database connection and setup tables
        logger.info('Testing database connection...')
        with app.app_context():
            try:
                # Test connection - use newer SQLAlchemy API
                if hasattr(db.engine, 'connect'):
                    with db.engine.connect() as conn:
                        conn.execute(sqlalchemy.text('SELECT 1'))
                else:
                    # Fallback for older versions
                    db.engine.execute(sqlalchemy.text('SELECT 1'))
                logger.info('✓ Database connection successful')
                
                # Create tables
                logger.info('Creating database tables...')
                try:
                    db.create_all()
                    logger.info('✓ Database tables created/verified')
                except Exception as table_error:
                    if 'already defined' in str(table_error) or 'already exists' in str(table_error):
                        logger.info('✓ Database tables already exist')
                    else:
                        logger.warning(f'Database table creation issue: {str(table_error)}')
                        # Try to continue anyway
                        pass
                
                # Initialize admin user during startup with proper handling
                logger.info('Initializing database tables at startup...')
                try:
                    from app.models import User, CreditTransaction, Resume, Analysis
                    from app.models.admin import AdminUser, AdminAction
                    from app.services.auth_manager import auth_manager
                    
                    # Define admin credentials
                    admin_email = 'admin@bearsystems.co.in'
                    admin_password = 'Benzie1!Benzie1!Benzie1!Benzie1!'
                    admin_username = 'admin'
                    
                    # Check for existing admin users (by email or username)
                    existing_admin_by_email = User.query.filter_by(email=admin_email).first()
                    existing_admin_by_username = User.query.filter_by(username=admin_username).first()
                    
                    # Handle existing admin users properly with cascade deletion
                    users_to_remove = []
                    if existing_admin_by_email:
                        users_to_remove.append(existing_admin_by_email)
                        logger.info(f'Found existing admin user by email: {admin_email}')
                        
                    if existing_admin_by_username and existing_admin_by_username != existing_admin_by_email:
                        users_to_remove.append(existing_admin_by_username)
                        logger.info(f'Found existing admin user by username: {admin_username}')
                    
                    # Also find any other admin users
                    other_admins = User.query.filter(
                        User.is_admin == True,
                        User.email != admin_email,
                        User.username != admin_username
                    ).all()
                    users_to_remove.extend(other_admins)
                    
                    # Remove all related records first to avoid foreign key constraint issues
                    for user in users_to_remove:
                        logger.info(f'Removing admin user: {user.email} (username: {user.username})')
                        
                        # First, remove any AdminUser records that reference this user
                        try:
                            if hasattr(user, 'admin_profile') and user.admin_profile:
                                admin_profile = user.admin_profile
                                # Proactively delete related admin actions to avoid NOT NULL FK issues
                                try:
                                    with db.session.no_autoflush:
                                        deleted = db.session.query(AdminAction).filter_by(admin_user_id=admin_profile.id).delete(synchronize_session=False)
                                        if deleted:
                                            logger.info(f'Deleted {deleted} admin action(s) for admin_user_id={admin_profile.id}')
                                except Exception as e:
                                    logger.warning(f'Error deleting admin actions for {user.email}: {e}')
                                logger.info(f'Removing AdminUser record for user via relationship: {user.email}')
                                db.session.delete(admin_profile)
                        except Exception:
                            # Fallback to direct query
                            admin_user_record = AdminUser.query.filter_by(user_id=user.id).first()
                            if admin_user_record:
                                try:
                                    with db.session.no_autoflush:
                                        deleted = db.session.query(AdminAction).filter_by(admin_user_id=admin_user_record.id).delete(synchronize_session=False)
                                        if deleted:
                                            logger.info(f'Deleted {deleted} admin action(s) for admin_user_id={admin_user_record.id}')
                                except Exception as e:
                                    logger.warning(f'Error deleting admin actions for {user.email}: {e}')
                                logger.info(f'Removing AdminUser record for user via query: {user.email}')
                                db.session.delete(admin_user_record)
                        
                        # Remove usage insights (analytics data)
                        try:
                            from app.models.analytics import UsageInsight, ErrorTracking
                            
                            # Remove usage insights
                            usage_insights = db.session.query(UsageInsight).filter_by(user_id=user.id).all()
                            for insight in usage_insights:
                                logger.info(f'Removing usage insight: {insight.id} for user {user.email}')
                                db.session.delete(insight)
                            
                            # Remove error tracking records
                            error_records = db.session.query(ErrorTracking).filter_by(user_id=user.id).all()
                            for error_record in error_records:
                                logger.info(f'Removing error tracking: {error_record.id} for user {user.email}')
                                db.session.delete(error_record)
                                
                        except ImportError:
                            logger.warning('Analytics models not available, skipping analytics cleanup')
                        except Exception as e:
                            logger.warning(f'Error cleaning up analytics data for {user.email}: {str(e)}')
                        
                        # Remove any other potential foreign key references
                        try:
                            # Remove analysis queue items
                            from app.models.queue import AnalysisQueue
                            queue_items = db.session.query(AnalysisQueue).filter_by(user_id=user.id).all()
                            for queue_item in queue_items:
                                logger.info(f'Removing queue item: {queue_item.id} for user {user.email}')
                                db.session.delete(queue_item)
                        except Exception as e:
                            logger.warning(f'Error cleaning up queue items for {user.email}: {str(e)}')
                        
                        # Remove sales intelligence data
                        try:
                            from app.models.sales import Lead, LeadActivity, LeadScoreHistory
                            
                            # Remove lead activities and score history first
                            leads = db.session.query(Lead).filter_by(user_id=user.id).all()
                            for lead in leads:
                                # Remove lead activities
                                activities = db.session.query(LeadActivity).filter_by(lead_id=lead.id).all()
                                for activity in activities:
                                    logger.info(f'Removing lead activity: {activity.id} for user {user.email}')
                                    db.session.delete(activity)
                                
                                # Remove lead score history
                                score_history = db.session.query(LeadScoreHistory).filter_by(lead_id=lead.id).all()
                                for score in score_history:
                                    logger.info(f'Removing lead score history: {score.id} for user {user.email}')
                                    db.session.delete(score)
                                
                                # Remove the lead itself
                                logger.info(f'Removing lead: {lead.id} for user {user.email}')
                                db.session.delete(lead)
                                
                        except Exception as e:
                            logger.warning(f'Error cleaning up sales data for {user.email}: {str(e)}')
                        
                        # Remove credit transactions (they have non-nullable foreign key)
                        credit_transactions = db.session.query(CreditTransaction).filter_by(user_id=user.id).all()
                        for transaction in credit_transactions:
                            logger.info(f'Removing credit transaction: {transaction.id} for user {user.email}')
                            db.session.delete(transaction)
                        
                        # Remove resumes and related analyses
                        for resume in user.resumes:
                            logger.info(f'Removing resume: {resume.id} for user {user.email}')
                            # Remove analyses related to this resume
                            analyses = db.session.query(Analysis).filter_by(resume_id=resume.id).all()
                            for analysis in analyses:
                                db.session.delete(analysis)
                            db.session.delete(resume)
                        
                        # Finally remove the user
                        db.session.delete(user)
                    
                    # Commit deletions
                    db.session.commit()
                    logger.info('✓ Existing admin users and AdminUser records removed')
                    
                    # Create the new admin user
                    admin = User(
                        email=admin_email,
                        username=admin_username,
                        password_hash=auth_manager.hash_password(admin_password),
                        first_name='System',
                        last_name='Administrator',
                        is_admin=True,
                        is_active=True,
                        credits_balance=10000
                    )
                    
                    db.session.add(admin)
                    db.session.flush()  # Flush to get the ID before creating AdminUser
                    
                    # Create corresponding AdminUser record
                    admin_user = AdminUser(
                        user_id=admin.id,
                        role='super_admin',
                        access_level=100,
                        can_access_all_users=True,
                        can_modify_credits=True,
                        can_manage_queue=True,
                        can_view_analytics=True,
                        can_manage_system=True,
                        can_access_sales_intelligence=True,
                        is_active=True
                    )
                    
                    db.session.add(admin_user)
                    db.session.commit()
                    
                    logger.info(f'✅ Admin user created/updated: {admin_email} with username: {admin_username}')
                    logger.info(f'✅ AdminUser record created with super_admin role')
                    logger.info('✓ Database tables initialized successfully')
                    
                except Exception as admin_error:
                    logger.error(f'Failed to initialize admin user: {str(admin_error)}')
                    # Rollback the transaction to prevent partial state
                    try:
                        db.session.rollback()
                        logger.info('Database session rolled back')
                    except:
                        pass
                    # Don't fail the whole application for this
                    pass
                
            except Exception as db_error:
                logger.warning(f'Database setup issue (continuing): {str(db_error)}')
                # Continue anyway for graceful degradation
        
        logger.info('✓ Flask application created successfully')
        return app, db, socketio
    except Exception as e:
        logger.error(f'Failed to create Flask application: {str(e)}')
        logger.error(f'Traceback: {traceback.format_exc()}')
        raise

# Initialize based on arguments or environment
if __name__ == '__main__':
    args = parse_args()
else:
    # When imported by gunicorn, use environment variables
    class Args:
        mode = os.environ.get('FLASK_ENV', 'production')
        log_level = os.environ.get('LOG_LEVEL', 'INFO')
        diagnostics = os.environ.get('RUN_DIAGNOSTICS', 'false').lower() == 'true'
        port = int(os.environ.get('PORT', 8000))
    args = Args()

# Setup logging
setup_logging(args.log_level, include_file=(args.mode == 'development'))

logger = logging.getLogger(__name__)

# Run diagnostics if requested
if args.diagnostics:
    if not run_diagnostics():
        logger.error('Diagnostics failed - exiting')
        sys.exit(1)

# Create application
try:
    app, db, socketio = create_application(args.mode)
    logger.info('✓ Application initialization complete')
except Exception as e:
    logger.error(f'Application initialization failed: {str(e)}')
    sys.exit(1)

# Add CLI commands and context processors after app creation
def setup_app_commands():
    """Setup CLI commands and context processors"""
    @app.shell_context_processor
    def make_shell_context():
        """Make database models available in shell context."""
        logger.info('Setting up shell context...')
        try:
            from app.models import User, CreditTransaction, Resume, Analysis, AnalysisQueue, BatchUpload
            return {
                'db': db,
                'User': User,
                'CreditTransaction': CreditTransaction,
                'Resume': Resume,
                'Analysis': Analysis,
                'AnalysisQueue': AnalysisQueue,
                'BatchUpload': BatchUpload
            }
        except Exception as e:
            logger.error(f'Failed to setup shell context: {str(e)}')
            return {'db': db}

    @app.cli.command()
    def init_db():
        """Initialize the database."""
        logger.info('Initializing database...')
        try:
            db.create_all()
            logger.info("✓ Database initialized successfully!")
            print("Database initialized!")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            print(f"Database initialization failed: {str(e)}")

    @app.cli.command()
    def reset_db():
        """Reset the database."""
        logger.info('Resetting database...')
        try:
            db.drop_all()
            db.create_all()
            logger.info("✓ Database reset successfully!")
            print("Database reset!")
        except Exception as e:
            logger.error(f"Failed to reset database: {str(e)}")
            print(f"Database reset failed: {str(e)}")

    @app.cli.command()
    def run_diagnostics_cmd():
        """Run system diagnostics via CLI"""
        success = run_diagnostics()
        if success:
            print("✓ All diagnostics passed")
        else:
            print("✗ Some diagnostics failed - check logs")
            sys.exit(1)

# Setup app commands
setup_app_commands()

def initialize_database():
    """Initialize database tables at startup (not during request)."""
    if not hasattr(initialize_database, 'done'):
        logger.info('Initializing database tables at startup...')
        try:
            with app.app_context():
                # Use a separate engine for initialization to avoid threading issues
                from sqlalchemy import create_engine
                from app.config import Config
                
                # Create a dedicated engine for initialization
                init_engine = create_engine(
                    app.config['SQLALCHEMY_DATABASE_URI'],
                    pool_size=1,  # Use single connection for initialization
                    max_overflow=0,
                    pool_pre_ping=False,
                    echo=False
                )
                
                # Create tables using the dedicated engine
                db.metadata.create_all(bind=init_engine)
                init_engine.dispose()  # Clean up
                
                logger.info("✓ Database tables initialized successfully")
            initialize_database.done = True
        except Exception as e:
            logger.error(f"Error initializing database tables: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            initialize_database.done = True

# Initialize database at startup for production environments
if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLASK_ENV') == 'production':
    try:
        initialize_database()
    except Exception as e:
        logger.warning(f"Database initialization failed at startup: {e}")
        # Continue - database might be initialized by migration

# Make app available for WSGI servers (gunicorn, etc.)
application = app
app = app  # Also export as 'app' for start.py compatibility

if __name__ == '__main__':
    # Direct execution - development mode
    if args.mode == 'diagnostics':
        logger.info('Running diagnostics mode only')
        success = run_diagnostics()
        sys.exit(0 if success else 1)
    
    logger.info(f'Starting development server in {args.mode} mode...')
    
    if args.mode == 'test':
        # Test mode - just verify app creation
        logger.info('Test mode - application created successfully')
        print("✓ Application test passed")
        sys.exit(0)
    
    # Development server
    debug_mode = args.mode == 'development'
    
    logger.info(f'Starting server on port {args.port}, debug={debug_mode}')
    
    try:
        socketio.run(
            app,
            host='0.0.0.0',
            port=args.port,
            debug=debug_mode,
            allow_unsafe_werkzeug=True  # For Railway compatibility
        )
    except Exception as e:
        logger.error(f'Failed to start development server: {str(e)}')
        logger.error(f'Traceback: {traceback.format_exc()}')
        sys.exit(1)
else:
    # Imported by WSGI server
    logger.info('Application imported for production deployment (WSGI)')
    logger.info('='*60)
    logger.info('RESUMEAI PRO APPLICATION READY FOR WSGI')
    logger.info('='*60)
