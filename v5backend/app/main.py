from __future__ import annotations
import os
import sys
from flask import Flask
from app.core.config import settings
from app.core.logging import configure_logging, instrument_flask
from app.db.session import init_db
from app.api.routes import bp as api_bp
from app.services.storage import ensure_buckets_existence


def create_app() -> Flask:
    """Create Flask application with enhanced Railway deployment support."""
    startup_start_time = __import__('time').time()
    
    # Log Railway deployment info immediately
    print("🚂 RAILWAY DEPLOYMENT DEBUG INFO:")
    print(f"   📋 Service: {os.environ.get('RAILWAY_SERVICE_NAME', 'UNKNOWN')}")
    print(f"   🆔 Deployment: {os.environ.get('RAILWAY_DEPLOYMENT_ID', 'UNKNOWN')}")
    print(f"   🌍 Environment: {os.environ.get('RAILWAY_ENVIRONMENT_NAME', 'UNKNOWN')}")
    print(f"   🐍 Python: {sys.version}")
    print(f"   📂 CWD: {os.getcwd()}")
    print(f"   💾 Memory: {os.environ.get('RAILWAY_MEMORY_GB', 'UNKNOWN')}GB")
    print(f"   🚀 Replica: {os.environ.get('RAILWAY_REPLICA_ID', 'UNKNOWN')}")
    
    try:
        # Configure structured logging early
        print("🔄 Configuring logging...")
        configure_logging(settings.LOG_LEVEL, service="api", env=settings.ENV)
        print(f"✅ Logging configured: level={settings.LOG_LEVEL}, env={settings.ENV}")
        
        print("🔄 Creating Flask application...")
        app = Flask(__name__)
        app.config['APP_NAME'] = settings.APP_NAME
        app.config['ENV'] = settings.ENV
        print(f"✅ Flask app created: {settings.APP_NAME}")

        # Instrument HTTP logging
        print("🔄 Setting up HTTP instrumentation...")
        instrument_flask(app)
        print("✅ HTTP instrumentation configured")

        # Init DB (ensure pgvector) - non-blocking for startup
        print("🔄 Initializing database connection...")
        print(f"   🏪 Database URL: {settings.DATABASE_URL[:30]}...***MASKED***")
        print(f"   🔌 Connection pool size: {getattr(settings, 'DB_POOL_SIZE', 'default')}")
        try:
            init_db()
            print("✅ Database initialization completed successfully")
        except Exception as e:
            print(f"❌ CRITICAL: Database initialization failed: {e}")
            print(f"   🏪 Full Database URL pattern: {settings.DATABASE_URL[:50]}...***MASKED***")
            print(f"   🔍 Error type: {type(e).__name__}")
            import traceback
            print("   📋 Full traceback:")
            traceback.print_exc()
            print("   ⚠️  The app will still start, but database operations WILL FAIL")

        # Ensure S3 buckets - non-blocking for startup
        print("🔄 Checking S3/MinIO bucket availability...")
        print(f"   🪣 S3 Endpoint: {settings.S3_ENDPOINT}")
        print(f"   🔑 S3 Access Key: {settings.S3_ACCESS_KEY[:10]}...***MASKED***")
        print(f"   📦 Resume Bucket: {settings.S3_BUCKET_RESUMES}")
        try:
            bucket_result = ensure_buckets_existence()
            if bucket_result:
                print("✅ S3/MinIO buckets verified successfully")
            else:
                print("❌ S3/MinIO buckets check failed but continuing...")
        except Exception as e:
            print(f"❌ CRITICAL: S3 bucket initialization failed: {e}")
            print(f"   🔍 Error type: {type(e).__name__}")
            import traceback
            print("   📋 Full traceback:")
            traceback.print_exc()
            print("   ⚠️  The app will still start, but file operations WILL FAIL")

        # Register blueprints
        print("🔄 Registering API blueprints...")
        try:
            app.register_blueprint(api_bp, url_prefix="/api")
            print("✅ API blueprints registered successfully")
        except Exception as e:
            print(f"❌ CRITICAL: Failed to register API blueprints: {e}")
            print(f"   🔍 Error type: {type(e).__name__}")
            import traceback
            print("   📋 Full traceback:")
            traceback.print_exc()
            raise

        @app.get("/")
        def index():
            return {
                "name": settings.APP_NAME, 
                "status": "healthy", 
                "env": settings.ENV,
                "railway_deployment": os.environ.get('RAILWAY_DEPLOYMENT_ID', 'unknown'),
                "railway_service": os.environ.get('RAILWAY_SERVICE_NAME', 'unknown'),
                "timestamp": __import__('datetime').datetime.utcnow().isoformat()
            }

        @app.get("/health")
        def health():
            health_status = {
                "status": "ok", 
                "service": "api",
                "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
                "railway": {
                    "deployment_id": os.environ.get('RAILWAY_DEPLOYMENT_ID', 'unknown'),
                    "service_name": os.environ.get('RAILWAY_SERVICE_NAME', 'unknown'),
                    "environment": os.environ.get('RAILWAY_ENVIRONMENT_NAME', 'unknown'),
                    "replica_id": os.environ.get('RAILWAY_REPLICA_ID', 'unknown')
                }
            }
            
            # Test basic connectivity
            try:
                from app.db.session import get_db_session
                with get_db_session() as session:
                    session.execute(__import__('sqlalchemy.text').text("SELECT 1"))
                health_status["database"] = "connected"
            except Exception as e:
                health_status["database"] = f"error: {str(e)}"
                
            try:
                from app.services.storage import test_s3_connection
                if test_s3_connection():
                    health_status["s3"] = "connected"
                else:
                    health_status["s3"] = "failed"
            except Exception as e:
                health_status["s3"] = f"error: {str(e)}"
                
            return health_status

        @app.get("/debug/startup")
        def debug_startup():
            """Detailed startup information for Railway debugging."""
            startup_info = {
                "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
                "python_version": sys.version,
                "working_directory": os.getcwd(),
                "environment_variables": {
                    "RAILWAY_DEPLOYMENT_ID": os.environ.get('RAILWAY_DEPLOYMENT_ID', 'not_set'),
                    "RAILWAY_SERVICE_NAME": os.environ.get('RAILWAY_SERVICE_NAME', 'not_set'),
                    "RAILWAY_ENVIRONMENT_NAME": os.environ.get('RAILWAY_ENVIRONMENT_NAME', 'not_set'),
                    "PORT": os.environ.get('PORT', 'not_set'),
                    "ENV": os.environ.get('ENV', 'not_set'),
                    "LOG_LEVEL": os.environ.get('LOG_LEVEL', 'not_set'),
                    "DATABASE_URL": "***MASKED***" if os.environ.get('DATABASE_URL') else 'not_set',
                    "S3_ENDPOINT": os.environ.get('S3_ENDPOINT', 'not_set'),
                },
                "flask_config": {
                    "APP_NAME": app.config.get('APP_NAME'),
                    "ENV": app.config.get('ENV'),
                },
                "registered_routes": [rule.rule for rule in app.url_map.iter_rules()],
                "startup_duration": f"{startup_duration:.2f}s" if 'startup_duration' in locals() else "unknown"
            }
            
            # Test services
            startup_info["service_tests"] = {}
            
            try:
                from app.db.session import get_db_session
                with get_db_session() as session:
                    result = session.execute(__import__('sqlalchemy.text').text("SELECT version()"))
                    version = result.fetchone()[0]
                startup_info["service_tests"]["database"] = {"status": "ok", "version": version[:100]}
            except Exception as e:
                startup_info["service_tests"]["database"] = {"status": "error", "error": str(e)}
                
            try:
                from app.services.storage import get_s3_client
                s3 = get_s3_client()
                buckets = s3.list_buckets()
                startup_info["service_tests"]["s3"] = {"status": "ok", "bucket_count": len(buckets.get('Buckets', []))}
            except Exception as e:
                startup_info["service_tests"]["s3"] = {"status": "error", "error": str(e)}
                
            return startup_info

        startup_duration = __import__('time').time() - startup_start_time
        print(f"✅ Flask application created successfully in {startup_duration:.2f}s")
        print(f"🎯 Ready to serve requests on Railway deployment {os.environ.get('RAILWAY_DEPLOYMENT_ID', 'unknown')}")
        return app
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR during Flask app creation: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        print(f"🚂 Railway Deployment: {os.environ.get('RAILWAY_DEPLOYMENT_ID', 'unknown')}")
        import traceback
        print("📋 FULL ERROR TRACEBACK:")
        traceback.print_exc()
        print("🆘 Attempting to create minimal Flask app as fallback...")
        
        # Create minimal fallback app
        fallback_app = Flask(__name__)
        
        @fallback_app.get("/")
        def fallback_index():
            return {
                "error": "Application startup failed", 
                "details": str(e),
                "railway_deployment": os.environ.get('RAILWAY_DEPLOYMENT_ID', 'unknown'),
                "timestamp": __import__('datetime').datetime.utcnow().isoformat()
            }, 500
            
        @fallback_app.get("/health")
        def fallback_health():
            return {
                "status": "degraded", 
                "error": str(e),
                "railway_deployment": os.environ.get('RAILWAY_DEPLOYMENT_ID', 'unknown'),
                "timestamp": __import__('datetime').datetime.utcnow().isoformat()
            }, 503
            
        print("⚠️  Minimal fallback app created - will return 500 errors but at least respond")
        return fallback_app


# Create the app instance with enhanced error handling
print("🚂 RAILWAY STARTUP SEQUENCE INITIATED")
print("="*60)
try:
    print("🚀 Starting Flask application creation...")
    print(f"🐍 Python version: {sys.version}")
    print(f"📂 Working directory: {os.getcwd()}")
    print(f"🔧 PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    print(f"🌐 PORT: {os.environ.get('PORT', 'Not set')}")
    print(f"🔧 ROLE: {os.environ.get('ROLE', 'Not set')}")
    print(f"🚂 Railway Environment: {os.environ.get('RAILWAY_ENVIRONMENT_NAME', 'Not set')}")
    print(f"🆔 Railway Deployment: {os.environ.get('RAILWAY_DEPLOYMENT_ID', 'Not set')}")
    print(f"📋 Railway Service: {os.environ.get('RAILWAY_SERVICE_NAME', 'Not set')}")
    print("="*60)
    
    app = create_app()
    print("✅ Flask application instance created successfully")
    print("🎯 Ready for Railway to start serving traffic")
    
except Exception as e:
    print("="*60)
    print(f"❌ CRITICAL: Failed to create Flask application: {e}")
    print(f"🔍 Error type: {type(e).__name__}")
    print(f"🚂 Railway Deployment: {os.environ.get('RAILWAY_DEPLOYMENT_ID', 'unknown')}")
    import traceback
    print("📋 COMPLETE ERROR TRACEBACK:")
    traceback.print_exc()
    print("="*60)
    
    # Create emergency fallback app
    print("🆘 Creating emergency fallback application...")
    app = Flask(__name__)
    
    @app.get("/")
    def emergency_index():
        return {
            "error": "Application failed to start", 
            "details": str(e),
            "error_type": type(e).__name__,
            "railway_deployment": os.environ.get('RAILWAY_DEPLOYMENT_ID', 'unknown'),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }, 500
    
    @app.get("/health") 
    def emergency_health():
        return {
            "status": "critical", 
            "error": str(e),
            "error_type": type(e).__name__,
            "railway_deployment": os.environ.get('RAILWAY_DEPLOYMENT_ID', 'unknown'),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }, 503
        
    print("⚠️  Emergency fallback application created - will serve error responses")
    print("🔍 Check Railway logs for full error details")

if __name__ == "__main__":
    print("🧪 Running Flask app in development mode...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)
