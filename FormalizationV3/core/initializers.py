"""
Core initialization modules for HR ATS System
Handles component initialization, middleware setup, and route registration
"""

import logging
import os
from typing import Dict, Any
from dataclasses import dataclass

from models.database import DatabaseManager
from supabase_client import SupabaseClient
from storage_manager import StorageManager
from auth_middleware import AuthMiddleware
from security_manager import SecurityManager
from railway_optimizer import railway_optimizer
from utils.unified_ai_processor import initialize_unified_processor

logger = logging.getLogger(__name__)

@dataclass
class ApplicationComponents:
    """Container for all application components"""
    db_manager: DatabaseManager = None
    supabase: SupabaseClient = None
    storage: StorageManager = None
    auth: AuthMiddleware = None
    security: SecurityManager = None
    ai_processor: Any = None
    credit_manager: Any = None
    email_automation: Any = None
    analytics_engine: Any = None
    sales_intelligence: Any = None
    backup_sync: Any = None
    realtime_manager: Any = None
    search_engine: Any = None
    performance_monitor: Any = None
    memory_cache: Any = None

class ComponentInitializer:
    """Handles initialization of all core components"""
    
    def __init__(self, app):
        self.app = app
        self.components = ApplicationComponents()
    
    def initialize_all(self) -> ApplicationComponents:
        """Initialize all components with lazy loading"""
        logger.info("🛠️ Initializing core components...")
        
        # Apply Railway optimizations first
        self._apply_optimizations()
        
        # Initialize core components
        self._init_database()
        self._init_storage()
        self._init_ai_processing()
        self._init_optional_components()
        
        logger.info("✅ All components initialized")
        return self.components
    
    def _apply_optimizations(self):
        """Apply Railway and performance optimizations"""
        logger.info("🚀 Applying Railway optimizations...")
        optimization_result = railway_optimizer.optimize_for_railway()
        logger.info(f"✅ Railway optimization result: {optimization_result}")
    
    def _init_database(self):
        """Initialize database components"""
        logger.info("📊 Initializing database components...")
        
        try:
            self.components.db_manager = DatabaseManager()
            logger.info("✅ Database manager initialized")
        except Exception as e:
            logger.error(f"❌ Database manager failed: {e}")
            # Fallback to Supabase only
            
        try:
            self.components.supabase = SupabaseClient()
            logger.info("✅ Supabase client initialized")
        except Exception as e:
            logger.error(f"❌ Supabase client failed: {e}")
    
    def _init_storage(self):
        """Initialize storage components"""
        logger.info("📁 Initializing storage components...")
        
        try:
            self.components.storage = StorageManager()
            logger.info("✅ Storage manager initialized")
        except Exception as e:
            logger.error(f"❌ Storage manager failed: {e}")
        
        # Create necessary directories
        self._create_directories()
    
    def _init_ai_processing(self):
        """Initialize AI processing components"""
        logger.info("🤖 Initializing AI processing...")
        
        try:
            railway_db = getattr(self.components.db_manager, 'railway_pg', None)
            self.components.ai_processor = initialize_unified_processor(
                railway_db=railway_db,
                cache_manager=None  # Initialize cache separately if needed
            )
            logger.info("✅ AI processor initialized")
        except Exception as e:
            logger.error(f"❌ AI processor failed: {e}")
    
    def _init_optional_components(self):
        """Initialize optional components (credit system, analytics, etc.)"""
        logger.info("🔧 Initializing optional components...")
        
        # Credit Manager
        try:
            from credit_manager import CreditManager
            self.components.credit_manager = CreditManager(self.components.db_manager)
            logger.info("✅ Credit manager initialized")
        except Exception as e:
            logger.warning(f"Credit manager not available: {e}")
        
        # Email Automation
        try:
            from email_automation import EmailAutomationManager
            if self.components.credit_manager:
                self.components.email_automation = EmailAutomationManager(
                    self.components.db_manager, 
                    self.components.credit_manager
                )
                logger.info("✅ Email automation initialized")
        except Exception as e:
            logger.warning(f"Email automation not available: {e}")
        
        # Analytics Engine
        try:
            from advanced_analytics import AdvancedAnalyticsEngine
            if self.components.credit_manager:
                self.components.analytics_engine = AdvancedAnalyticsEngine(
                    self.components.db_manager, 
                    self.components.credit_manager
                )
                logger.info("✅ Analytics engine initialized")
        except Exception as e:
            logger.warning(f"Analytics engine not available: {e}")
        
        # Sales Intelligence
        try:
            from sales_intelligence import SalesIntelligenceDashboard
            if (self.components.credit_manager and 
                self.components.analytics_engine and 
                self.components.email_automation):
                self.components.sales_intelligence = SalesIntelligenceDashboard(
                    self.components.db_manager,
                    self.components.credit_manager,
                    self.components.analytics_engine,
                    self.components.email_automation
                )
                logger.info("✅ Sales intelligence initialized")
        except Exception as e:
            logger.warning(f"Sales intelligence not available: {e}")
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = ['uploads', 'processed', 'temp', 'logs', 'data/backups']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"✅ Directory ensured: {directory}")

class MiddlewareInitializer:
    """Handles middleware setup"""
    
    def __init__(self, app, components: ApplicationComponents):
        self.app = app
        self.components = components
    
    def setup_all(self):
        """Setup all middleware"""
        logger.info("🔧 Setting up middleware...")
        
        self._init_auth_middleware()
        self._init_security_middleware()
        self._setup_request_handlers()
        
        logger.info("✅ Middleware setup complete")
    
    def _init_auth_middleware(self):
        """Initialize authentication middleware"""
        try:
            self.components.auth = AuthMiddleware(self.components.db_manager)
            logger.info("✅ Auth middleware initialized")
        except Exception as e:
            logger.error(f"❌ Auth middleware failed: {e}")
    
    def _init_security_middleware(self):
        """Initialize security middleware"""
        try:
            self.components.security = SecurityManager()
            logger.info("✅ Security middleware initialized")
        except Exception as e:
            logger.error(f"❌ Security middleware failed: {e}")
    
    def _setup_request_handlers(self):
        """Setup before/after request handlers"""
        
        @self.app.before_request
        def before_request():
            if self.components.security:
                # Apply security headers
                self.components.security.apply_security_headers()
                
                # Apply rate limiting
                from flask import request, jsonify
                if not self.components.security.check_rate_limit(request.remote_addr):
                    return jsonify({"error": "Rate limit exceeded"}), 429
        
        @self.app.after_request
        def after_request(response):
            # Add security headers to response
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            return response

class RoutesInitializer:
    """Handles route registration"""
    
    def __init__(self, app, components: ApplicationComponents):
        self.app = app
        self.components = components
    
    def register_all(self):
        """Register all application routes"""
        logger.info("🛣️ Registering routes...")
        
        self._register_auth_routes()
        self._register_admin_routes()
        self._register_user_routes()
        self._register_hr_legal_routes()
        self._register_monitoring_routes()
        self._register_credit_routes()
        self._register_payment_routes()
        self._register_analytics_routes()
        self._register_backup_routes()
        self._register_advanced_features()
        
        logger.info("✅ All routes registered")
    
    def _register_auth_routes(self):
        """Register authentication routes"""
        try:
            from routes.auth import auth_bp, init_auth_routes
            init_auth_routes(self.components.db_manager)
            self.app.register_blueprint(auth_bp)
            logger.info("✅ Auth routes registered")
        except Exception as e:
            logger.error(f"❌ Auth routes failed: {e}")
    
    def _register_admin_routes(self):
        """Register admin routes"""
        try:
            from routes.admin import admin_bp, init_admin_routes
            init_admin_routes(self.components.db_manager)
            self.app.register_blueprint(admin_bp)
            logger.info("✅ Admin routes registered")
        except Exception as e:
            logger.error(f"❌ Admin routes failed: {e}")
    
    def _register_user_routes(self):
        """Register user routes"""
        try:
            from routes.user import user_bp, init_user_routes
            railway_db = getattr(self.components.db_manager, 'railway_pg', None)
            init_user_routes(
                database_manager=self.components.db_manager,
                railway_database=railway_db,
                auth_mid=self.components.auth,
                storage_mgr=self.components.storage,
                credit_mgr=self.components.credit_manager
            )
            self.app.register_blueprint(user_bp)
            logger.info("✅ User routes registered")
        except Exception as e:
            logger.error(f"❌ User routes failed: {e}")
    
    def _register_payment_routes(self):
        """Register payment and subscription management routes"""
        try:
            from routes.payments import payments_bp, init_payments_routes
            init_payments_routes(
                getattr(self.components, 'payment_manager', None),
                self.components.credit_manager,
                self.components.auth_middleware,
                self.components.db_manager
            )
            self.app.register_blueprint(payments_bp)
            logger.info("✅ Payment routes registered")
        except Exception as e:
            logger.error(f"❌ Payment routes failed: {e}")
    
    def _register_hr_legal_routes(self):
        """Register HR legal and RAG routes"""
        try:
            from routes.hr_legal import hr_legal_bp, init_hr_legal_routes
            init_hr_legal_routes(
                ai_processor=self.components.ai_processor,
                auth_middleware=self.components.auth,
                cache_manager=getattr(self.components, 'cache_manager', None)
            )
            self.app.register_blueprint(hr_legal_bp)
            logger.info("✅ HR Legal routes registered")
        except Exception as e:
            logger.error(f"❌ HR Legal routes failed: {e}")
    
    def _register_monitoring_routes(self):
        """Register system monitoring routes"""
        try:
            from routes.monitoring import monitoring_bp, init_monitoring_routes
            railway_db = getattr(self.components.db_manager, 'railway_pg', None)
            backup_manager = getattr(self.components, 'backup_sync', None)
            
            init_monitoring_routes(
                db_manager=self.components.db_manager,
                auth_middleware=self.components.auth,
                cache_manager=getattr(self.components, 'cache_manager', None),
                railway_db=railway_db,
                backup_manager=backup_manager
            )
            self.app.register_blueprint(monitoring_bp)
            logger.info("✅ Monitoring routes registered")
        except Exception as e:
            logger.error(f"❌ Monitoring routes failed: {e}")
    
    def _register_analytics_routes(self):
        """Register analytics and reporting routes"""
        try:
            from routes.analytics_routes import analytics_bp, init_analytics_routes
            init_analytics_routes(
                db_manager=self.components.db_manager,
                auth_middleware=self.components.auth,
                analytics_engine=self.components.analytics_engine,
                sales_intelligence=self.components.sales_intelligence,
                email_automation=self.components.email_automation
            )
            self.app.register_blueprint(analytics_bp)
            logger.info("✅ Analytics routes registered")
        except Exception as e:
            logger.error(f"❌ Analytics routes failed: {e}")
    
    def _register_credit_routes(self):
        """Register credit system and queue management routes"""
        try:
            from routes.credits import credits_bp, init_credits_routes
            init_credits_routes(
                self.components.credit_manager,
                getattr(self.components, 'queue_manager', None),
                self.components.auth_middleware,
                self.components.db_manager
            )
            self.app.register_blueprint(credits_bp)
            logger.info("✅ Credit routes registered")
        except Exception as e:
            logger.error(f"❌ Credit routes failed: {e}")
    
    def _register_backup_routes(self):
        """Register backup management routes"""
        try:
            from routes.backup_management import backup_bp, init_backup_routes
            init_backup_routes(self.app)
            logger.info("✅ Backup routes registered")
        except Exception as e:
            logger.error(f"❌ Backup routes failed: {e}")
    
    def _register_advanced_features(self):
        """Register advanced feature routes"""
        logger.info("🚀 Registering advanced features...")
        
        # WebSocket real-time features
        self._register_websocket_routes()
        
        # Bulk operations
        self._register_bulk_routes()
        
        # Advanced search
        self._register_search_routes()
        
        # Performance helpers
        self._register_performance_routes()
        
        # Ollama test routes
        self._register_ollama_test_routes()
        
        # Health monitoring dashboard
        self._register_health_routes()
        
        logger.info("✅ Advanced features registered")
    
    def _register_websocket_routes(self):
        """Register WebSocket routes"""
        try:
            from routes.websocket import websocket_bp, init_websocket_routes
            from utils.realtime_manager import RealtimeManager
            
            self.components.realtime_manager = RealtimeManager()
            init_websocket_routes(
                realtime_manager=self.components.realtime_manager,
                db_manager=self.components.db_manager
            )
            self.app.register_blueprint(websocket_bp)
            logger.info("✅ WebSocket routes registered")
        except Exception as e:
            logger.warning(f"WebSocket routes not available: {e}")
    
    def _register_bulk_routes(self):
        """Register bulk operation routes"""
        try:
            from routes.bulk import bulk_bp, init_bulk_routes
            from utils.bulk_operations import BulkOperationsManager
            
            bulk_manager = BulkOperationsManager(
                db_manager=self.components.db_manager,
                realtime_manager=self.components.realtime_manager
            )
            init_bulk_routes(
                bulk_manager_instance=bulk_manager,
                db_manager=self.components.db_manager,
                auth_middleware=self.components.auth
            )
            self.app.register_blueprint(bulk_bp)
            logger.info("✅ Bulk operation routes registered")
        except Exception as e:
            logger.warning(f"Bulk operation routes not available: {e}")
    
    def _register_search_routes(self):
        """Register advanced search routes"""
        try:
            from routes.search import search_bp, init_search_routes
            from utils.advanced_search import AdvancedSearchEngine
            
            self.components.search_engine = AdvancedSearchEngine(
                db_manager=self.components.db_manager
            )
            init_search_routes(
                search_engine_param=self.components.search_engine,
                db_manager=self.components.db_manager,
                auth_middleware=self.components.auth
            )
            self.app.register_blueprint(search_bp)
            logger.info("✅ Search routes registered")
        except Exception as e:
            logger.warning(f"Search routes not available: {e}")
    
    def _register_performance_routes(self):
        """Register performance helper routes"""
        try:
            from routes.performance import performance_bp
            from utils.performance_helpers import PerformanceMonitor, MemoryCache
            
            self.components.performance_monitor = PerformanceMonitor()
            self.components.memory_cache = MemoryCache(max_size=1000)
            
            self.app.register_blueprint(performance_bp)
            logger.info("✅ Performance routes registered")
        except Exception as e:
            logger.warning(f"Performance routes not available: {e}")
    
    def _register_ollama_test_routes(self):
        """Register Ollama test routes"""
        try:
            from routes.ollama_test import ollama_test_bp
            self.app.register_blueprint(ollama_test_bp)
            logger.info("✅ Ollama test routes registered")
        except Exception as e:
            logger.warning(f"Ollama test routes not available: {e}")
    
    def _register_health_routes(self):
        """Register health monitoring dashboard routes"""
        try:
            from routes.health_routes import health_bp, init_health_routes
            init_health_routes(
                db_manager=self.components.db_manager,
                auth_middleware=self.components.auth
            )
            self.app.register_blueprint(health_bp)
            logger.info("✅ Health dashboard routes registered")
        except Exception as e:
            logger.warning(f"Health dashboard routes not available: {e}")
