#!/usr/bin/env python3
"""
Simple startup script to run either web app or worker based on environment variable.
This allows Railway to deploy both services from the same codebase.
"""
import os
import sys
import subprocess

def main():
    """Main entry point."""
    service_type = os.environ.get('SERVICE_TYPE', 'web').lower()
    
    if service_type == 'worker':
        print("Starting queue worker...")
        sys.exit(subprocess.call([sys.executable, 'worker.py']))
    else:
        print("Starting web application...")
        # Initialize database first
        init_db()
        
        # Start gunicorn
        port = os.environ.get('PORT', '8000')
        workers = os.environ.get('GUNICORN_WORKERS', '4')
        threads = os.environ.get('GUNICORN_THREADS', '6')
        
        cmd = [
            'gunicorn',
            '--bind', f'0.0.0.0:{port}',
            '--worker-class', 'gthread',  # Use gthread instead of eventlet for Railway
            '--workers', '1',  # Single worker for WebSocket compatibility
            '--threads', '4',  # Multiple threads for concurrency
            '--timeout', '120',
            '--keep-alive', '2',
            '--max-requests', '1000',
            '--max-requests-jitter', '100',
            '--preload',
            '--log-level', 'info',
            '--access-logfile', '-',
            '--error-logfile', '-',
            'wsgi_clean:application'  # Use wsgi_clean for eventlet-free deployment
        ]
        
        sys.exit(subprocess.call(cmd))

def run_migrations():
    """Run database migrations using the migration manager."""
    try:
        print("📋 Running database migrations...")
        
        # Use the comprehensive migration manager
        from scripts.migration_manager import MigrationManager
        
        manager = MigrationManager()
        success = manager.run_migrations()
        
        if success:
            print("✅ Database migrations completed successfully!")
        else:
            print("⚠️  Migration issues detected - continuing with fallback...")
            
    except Exception as e:
        print(f"⚠️  Migration error: {str(e)}")
        print("🔄 Continuing with fallback database initialization...")
        # Don't fail completely - the comprehensive initializer can handle missing tables

def init_db():
    """Initialize database with comprehensive setup including migrations."""
    try:
        print("🚀 Starting database initialization with migrations...")
        
        # Step 1: Run database migrations first
        run_migrations()
        
        # Step 2: Import the comprehensive database initializer for additional setup
        from scripts.railway_db_init import DatabaseInitializer
        
        print("🚀 Starting comprehensive database initialization...")
        initializer = DatabaseInitializer()
        success = initializer.initialize_database()
        
        if success:
            print("✅ Database initialization completed successfully!")
            
            # Process legal documents if RAG is enabled
            process_legal_documents()
            
            # Initialize production monitoring
            setup_production_monitoring()
        else:
            print("❌ Database initialization failed!")
            
    except Exception as e:
        print(f'Database initialization error: {e}')
        # Don't exit on DB errors in case it's a connection issue
        # Fallback to basic initialization
        try:
            print("🔄 Attempting fallback database initialization...")
            from app import create_app, db
            from app.models import User, CreditTransaction, Resume, Analysis, AnalysisQueue, BatchUpload
            from app.services.auth_manager import auth_manager
            
            app = create_app()
            with app.app_context():
                db.create_all()
                print('Basic database tables created')
                
                # Create default admin with proper credentials
                admin_email = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@bearsystems.co.in')
                admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'Benzie1!Benzie1!Benzie1!Benzie1!')
                admin = User.query.filter_by(email=admin_email).first()
                
                if not admin:
                    admin = User(
                        email=admin_email,
                        username=admin_email.split('@')[0],
                        password_hash=auth_manager.hash_password(admin_password),
                        first_name='System',
                        last_name='Administrator',
                        is_admin=True,
                        is_active=True,
                        credits_balance=10000
                    )
                    db.session.add(admin)
                    db.session.commit()
                    print(f'✅ Admin user created: {admin_email} with password')
                else:
                    print(f'✅ Admin user exists: {admin_email}')
                    
        except Exception as fallback_error:
            print(f'Fallback initialization also failed: {fallback_error}')

def setup_production_monitoring():
    """Setup production monitoring and health checks."""
    try:
        # Ensure logs directory exists
        if not os.path.exists('logs'):
            os.makedirs('logs')
            print("📁 Created logs directory")
        
        # Test critical services
        print("🔍 Testing critical services...")
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            # Test database
            db.session.execute(db.text('SELECT 1'))
            print("✅ Database connectivity verified")
            
            # Test Ollama (if available)
            if not app.config.get('SIMPLE_HEALTH_ONLY', False):
                try:
                    import asyncio
                    from app.services.ollama_service import OllamaService
                    
                    async def test_ollama():
                        async with OllamaService() as ollama:
                            return await ollama.check_health()
                    
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    is_healthy = loop.run_until_complete(test_ollama())
                    loop.close()
                    
                    if is_healthy:
                        print("✅ Ollama service verified")
                    else:
                        print("⚠️  Ollama service not available - degraded mode")
                        
                except Exception as e:
                    print(f"⚠️  Ollama service test failed: {str(e)[:50]}...")
            
            print("🎯 Production monitoring setup complete!")
            
    except Exception as e:
        print(f"⚠️  Production monitoring setup failed: {str(e)[:100]}...")
        # Don't fail startup for monitoring issues

def process_legal_documents():
    """Process legal documents during startup if enabled."""
    try:
        print("📚 Checking legal document processing requirements...")
        from app.config import Config
        
        # Check if legal RAG is enabled and auto-update is enabled
        if not Config.LEGAL_RAG_ENABLED:
            print("📚 Legal RAG disabled - skipping document processing")
            return
        
        if not Config.AUTO_UPDATE_ON_DEPLOY:
            print("📚 Auto-update on deploy disabled - skipping document processing")
            return
        
        print("📚 Legal RAG is enabled - starting document processing...")
        print("🔄 Setting up async event loop...")
        
        # Run the legal document processing script
        import asyncio
        from scripts.process_legal_documents import process_legal_documents as process_docs
        
        # Run the async function with detailed logging and timeout
        print("🔧 Creating new event loop...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        print("🚀 Starting legal document processing...")
        print("⏰ Setting 15-minute timeout for model downloads...")
        
        try:
            # Add timeout for the entire operation (15 minutes)
            success = loop.run_until_complete(
                asyncio.wait_for(process_docs(), timeout=900)  # 15 minutes
            )
            print(f"📊 Legal document processing completed with result: {success}")
        except asyncio.TimeoutError:
            print("⏰ Legal document processing timed out after 15 minutes")
            print("🌐 This usually indicates network issues with model downloads")
            print("📚 Application will continue without legal RAG - can be enabled later")
            success = False
        except Exception as async_error:
            print(f"❌ Error during async processing: {str(async_error)}")
            import traceback
            print(f"📋 Traceback: {traceback.format_exc()}")
            success = False
        finally:
            print("🔄 Closing event loop...")
            loop.close()
            print("✅ Event loop closed")
        
        if success:
            print("✅ Legal documents processed successfully!")
        else:
            print("⚠️  Legal document processing had issues - check logs")
            print("💡 You can manually trigger processing later via admin panel")
            
    except Exception as e:
        print(f"❌ Legal document processing failed: {str(e)}")
        import traceback
        print(f"📋 Full traceback: {traceback.format_exc()}")
        print("📚 Application will continue without legal RAG - can be enabled later")
        print("💡 You can manually trigger processing later via admin panel")

if __name__ == '__main__':
    main()
