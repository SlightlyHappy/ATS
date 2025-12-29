#!/usr/bin/env python3
"""
Lightweight HR ATS System for Railway Deployment
Clean, optimized implementation based on Technical Blueprint
"""

import os
import json
import tempfile
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import hashlib

# Core Flask imports
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

# File processing imports
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from docx import Document
import pandas as pd
import requests

# System imports
import sys
import psutil
import gc

# Import our lightweight modules
from config import Config
from supabase_client import SupabaseClient
from ai_processor import AgenticResumeProcessor, analyze_resume, process_legal_query
from storage_manager import StorageManager
from auth_middleware import AuthMiddleware
from security_manager import SecurityManager
from models.database import DatabaseManager

# Railway Performance Optimization
from railway_optimizer import railway_optimizer

# CPU Optimization for Railway Pro
from cpu_optimizer import cpu_optimizer, optimize_for_ai, cache_response, get_cached_response

# Unified AI Processing System
from utils.unified_ai_processor import initialize_unified_processor, get_unified_processor

# AI Response Processing Layer
from utils.ai_response_processor import process_ai_response

# Supabase Initialization
from utils.supabase_initializer import initialize_supabase



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Railway Database Integration (after logging setup)
try:
    from railway_database import RailwayPostgreSQL
    from backup_sync import BackupSyncManager
    RAILWAY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Railway components not available: {e}")
    RAILWAY_AVAILABLE = False

class HRATSApplication:
    def __init__(self):
        """Initialize the lightweight HR ATS application with memory optimization"""
        logger.info("🚀 Starting HRATSApplication initialization with memory optimization...")
        
        logger.info("Step A1: Creating Flask app instance...")
        self.app = Flask(__name__)
        logger.info("Step A1: ✅ Flask app created successfully")
        
        logger.info("Step A1b: Initializing SocketIO for real-time features...")
        try:
            from flask_socketio import SocketIO
            
            # Production-ready SocketIO configuration
            self.socketio = SocketIO(
                self.app,
                cors_allowed_origins="*",
                logger=True,
                engineio_logger=False,
                async_mode='eventlet',
                ping_timeout=60,
                ping_interval=25,
                manage_session=False  # Use Flask sessions instead
            )
            
            # Register SocketIO event handlers
            self._setup_socketio_handlers()
            logger.info("Step A1b: ✅ SocketIO initialized with real-time features enabled")
            
        except Exception as e:
            logger.warning(f"SocketIO initialization failed: {e}")
            logger.warning("Continuing without real-time features")
            self.socketio = None
        
        logger.info("Step A2: Loading configuration...")
        self.config = Config()
        logger.info("Step A2: ✅ Configuration loaded successfully")
        
        # Initialize Railway-optimized caching system
        logger.info("Step A3: Initializing caching system...")
        self._admin_cache = {}
        self._response_cache = {}  # New comprehensive response cache
        
        # Initialize CPU optimization for Railway Pro
        logger.info("Step A3b: Initializing CPU optimization...")
        optimize_for_ai()  # Configure system for AI processing
        logger.info("Step A3b: ✅ CPU optimization configured")
        
        logger.info("Step A3: ✅ Caching system initialized")
        
        logger.info("Step A4: Setting up CORS...")
        self.setup_cors()
        logger.info("Step A4: ✅ CORS setup completed")
        
        logger.info("Step A5: Setting up middleware...")
        self.setup_middleware()
        logger.info("Step A5: ✅ Middleware setup completed")
        
        logger.info("Step A6: Initializing components with lazy loading...")
        self.initialize_components_lazy()
        logger.info("Step A6: ✅ Lazy components initialization completed")
        
        # Check AI processing availability
        try:
            from routes.admin import admin_ai_processing_available
            admin_ai_available = admin_ai_processing_available()
        except ImportError:
            admin_ai_available = False
        except Exception as e:
            logger.warning(f"Error checking admin AI processing: {e}")
            admin_ai_available = False
            
        if admin_ai_available:
            logger.info("✅ Admin AI processing function available for user uploads")
        else:
            logger.warning("⚠️ Admin AI processing function not available, will use fallback AI processing for user uploads")
        
        logger.info("Step A7: Registering critical health endpoints...")
        self._register_critical_health_endpoints()
        logger.info("Step A7a: ✅ Critical health endpoints registered")
        
        logger.info("Step A7b: Registering application routes...")
        try:
            self.register_routes()
            logger.info("Step A7b: ✅ Routes registration completed")
        except Exception as e:
            logger.error(f"❌ Route registration failed: {e}")
            logger.warning("Continuing with just health endpoints for Railway deployment...")
            import traceback
            logger.error(f"Route registration error details: {traceback.format_exc()}")
        
        logger.info("🎉 HRATSApplication initialization completed successfully with memory optimization!")
    
    def _get_cached_result(self, cache_key: str, ttl_seconds: int = 300):
        """Railway-optimized caching helper"""
        if (cache_key in self._admin_cache and 
            (datetime.now() - self._admin_cache[cache_key]['cached_at']).seconds < ttl_seconds):
            return self._admin_cache[cache_key]['data']
        return None
    
    def _set_cached_result(self, cache_key: str, data: Any):
        """Railway-optimized cache setter"""
        if not hasattr(self, '_admin_cache'):
            self._admin_cache = {}
        self._admin_cache[cache_key] = {
            'data': data,
            'cached_at': datetime.now()
        }
    
    def _get_response_cache(self, cache_key: str, ttl_seconds: int = 300):
        """Get cached response with TTL check"""
        if not hasattr(self, '_response_cache'):
            self._response_cache = {}
            
        if (cache_key in self._response_cache and 
            (datetime.now() - self._response_cache[cache_key]['cached_at']).seconds < ttl_seconds):
            return self._response_cache[cache_key]['data']
        return None
    
    def _set_response_cache(self, cache_key: str, data: Any):
        """Set response cache with timestamp"""
        if not hasattr(self, '_response_cache'):
            self._response_cache = {}
            
        self._response_cache[cache_key] = {
            'data': data,
            'cached_at': datetime.now()
        }
        
        # Cleanup old cache entries (keep last 100 entries)
        if len(self._response_cache) > 100:
            # Remove oldest entries
            sorted_keys = sorted(self._response_cache.keys(), 
                               key=lambda k: self._response_cache[k]['cached_at'])
            for old_key in sorted_keys[:20]:  # Remove 20 oldest
                del self._response_cache[old_key]
    
    def _safe_service_check(self, service_name: str) -> Dict[str, Any]:
        """Safely check service health with timeout"""
        try:
            if service_name == 'supabase':
                return self.supabase.health_check()
            elif service_name == 'storage':
                return self.storage.health_check()
            elif service_name == 'ai':
                return self.ai_analyzer.health_check()
            elif service_name == 'database':
                return self.db_manager.health_check()
            elif service_name == 'auth':
                return self.auth.health_check()
            else:
                return {"status": "unknown", "service": service_name}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def _invalidate_cache(self, pattern: str = None):
        """Cache invalidation strategy for Railway"""
        if not hasattr(self, '_admin_cache'):
            return
        
        if pattern:
            # Invalidate specific cache patterns
            keys_to_remove = [key for key in self._admin_cache.keys() if pattern in key]
            for key in keys_to_remove:
                self._admin_cache.pop(key, None)
                logger.debug(f"Invalidated cache key: {key}")
        else:
            # Clear all cache
            self._admin_cache.clear()
            logger.info("All cache invalidated")
    
    def _cleanup_expired_cache(self):
        """Cleanup expired cache entries to prevent memory bloat"""
        if not hasattr(self, '_admin_cache'):
            return
        
        current_time = datetime.now()
        expired_keys = []
        
        for key, cache_data in self._admin_cache.items():
            # Remove entries older than 1 hour regardless of TTL
            if (current_time - cache_data['cached_at']).seconds > 3600:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._admin_cache.pop(key, None)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
    def setup_cors(self):
        """Configure CORS for production deployment"""
        allowed_origins = [
            "https://hrtool-sable.vercel.app",     # Main frontend + Admin frontend
            "https://hrtbearsystems.vercel.app",   # Additional frontend
            "https://hrtool-sable.vercel.app",     # Additional reference (for good measure)
            "http://localhost:3000",               # Development
            "http://localhost:3001",               # Admin development
            "http://127.0.0.1:3000",              # Alternative localhost
            "http://127.0.0.1:3001",              # Alternative localhost admin
        ]
        
        # Add environment-specific origins
        if os.getenv('FRONTEND_URL'):
            allowed_origins.append(os.getenv('FRONTEND_URL'))
        if os.getenv('ADMIN_FRONTEND_URL'):
            allowed_origins.append(os.getenv('ADMIN_FRONTEND_URL'))
            
        logger.info(f"CORS configured for origins: {allowed_origins}")
            
        CORS(
            self.app,
            origins=allowed_origins,
            supports_credentials=True,
            allow_headers=['Content-Type', 'Authorization', 'Accept', 'X-Requested-With'],
            methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            expose_headers=['Content-Range', 'X-Content-Range']
        )
        
    def setup_middleware(self):
        """Setup enhanced security and authentication middleware"""
        logger.info("🔧 Setting up middleware...")
        
        # Initialize database manager first
        logger.info("Middleware Step 1: Importing DatabaseManager...")
        from models.database import DatabaseManager
        logger.info("Middleware Step 1: ✅ DatabaseManager imported")
        
        logger.info("Middleware Step 2: Creating DatabaseManager instance...")
        self.db_manager = DatabaseManager()
        logger.info("Middleware Step 2: ✅ DatabaseManager created")
        
        # CRITICAL: Set railway_db attribute for route dependencies
        self.railway_db = getattr(self.db_manager, 'railway_pg', None)
        if self.railway_db:
            logger.info(f"✅ Railway PostgreSQL connection established")
        else:
            logger.warning("⚠️ Railway PostgreSQL not available - using fallback database")
        
        # Initialize enhanced authentication with database support
        logger.info("Middleware Step 3: Creating AuthMiddleware...")
        self.auth = AuthMiddleware(self.db_manager)
        logger.info("Middleware Step 3: ✅ AuthMiddleware created")
        
        logger.info("Middleware Step 4: Creating SecurityManager...")
        self.security = SecurityManager()
        logger.info("Middleware Step 4: ✅ SecurityManager created")
        
        # Initialize credit system (Phase 1 - B2B SaaS)
        logger.info("Middleware Step 5: Initializing credit system...")
        try:
            logger.info("Importing credit system modules...")
            from credit_manager import CreditManager
            from queue_manager import BasicRequestQueue
            from credit_middleware import CreditRouteMiddleware
            logger.info("✅ Credit system modules imported")
            
            logger.info("Creating CreditManager...")
            self.credit_manager = CreditManager(self.db_manager)
            logger.info("✅ CreditManager created")
            
            logger.info("Creating BasicRequestQueue...")
            self.queue_manager = BasicRequestQueue(self.credit_manager, max_concurrent=10)  # Increased from 3 for Railway
            logger.info("✅ BasicRequestQueue created")
            
            logger.info("Creating CreditRouteMiddleware...")
            self.credit_middleware = CreditRouteMiddleware(self.credit_manager, self.queue_manager)
            logger.info("✅ CreditRouteMiddleware created")
            
            logger.info("Credit system initialized successfully for B2B SaaS")
        except Exception as e:
            logger.error(f"Credit system initialization failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            # Continue without credit system - non-breaking
            self.credit_manager = None
            self.queue_manager = None
            self.credit_middleware = None
            logger.info("Continuing without credit system (non-breaking)")
        
        # Initialize Phase 3 - Sales Intelligence & Advanced Analytics
        logger.info("Middleware Step 6: Initializing Phase 3 components...")
        try:
            logger.info("Importing Phase 3 modules...")
            from email_automation import EmailAutomationManager
            from advanced_analytics import AdvancedAnalyticsEngine
            from sales_intelligence import SalesIntelligenceDashboard
            logger.info("✅ Phase 3 modules imported")
            
            if self.credit_manager:
                logger.info("Credit manager available, initializing Phase 3 with credit support...")
                
                logger.info("Creating EmailAutomationManager...")
                self.email_automation = EmailAutomationManager(self.db_manager, self.credit_manager)
                logger.info("✅ EmailAutomationManager created")
                
                logger.info("Creating AdvancedAnalyticsEngine...")
                self.analytics_engine = AdvancedAnalyticsEngine(self.db_manager, self.credit_manager)
                logger.info("✅ AdvancedAnalyticsEngine created")
                
                logger.info("Creating SalesIntelligenceDashboard...")
                self.sales_intelligence = SalesIntelligenceDashboard(
                    self.db_manager, self.credit_manager, self.analytics_engine, self.email_automation
                )
                logger.info("✅ SalesIntelligenceDashboard created")
                
                # Connect email automation to credit manager to avoid circular imports
                logger.info("Connecting email automation to credit manager...")
                self.credit_manager.set_email_automation(self.email_automation)
                logger.info("✅ Email automation connected to credit manager")
                
                logger.info("Phase 3 Sales Intelligence & Analytics initialized successfully")
            else:
                logger.warning("Phase 3 initialization skipped - credit system not available")
                self.email_automation = None
                self.analytics_engine = None
                self.sales_intelligence = None
                
        except Exception as e:
            logger.error(f"Phase 3 initialization failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            self.email_automation = None
            self.analytics_engine = None
            self.sales_intelligence = None
            logger.info("Continuing without Phase 3 components (non-breaking)")
        
        logger.info("Middleware Step 7: Setting up request handlers...")
        # Clean up expired cache periodically
        @self.app.before_request
        def before_request():
            # Apply security headers
            self.security.apply_security_headers()
            
            # Apply rate limiting
            if not self.security.check_rate_limit(request.remote_addr):
                return jsonify({"error": "Rate limit exceeded"}), 429
            
            # Railway cache cleanup (every 100 requests)
            if hasattr(self, '_request_count'):
                self._request_count += 1
                if self._request_count % 100 == 0:
                    self._cleanup_expired_cache()
            else:
                self._request_count = 1
        
        @self.app.after_request
        def after_request(response):
            # Add security headers to response
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            return response
        
        logger.info("Middleware Step 7: ✅ Request handlers setup completed")
        logger.info("🔧 Middleware setup completed successfully")
            
    def initialize_components_lazy(self):
        """Initialize core system components with lazy loading for memory optimization"""
        logger.info("🛠️ Initializing core system components with lazy loading...")
        try:
            # Apply Railway optimizations first (lightweight)
            logger.info("Components Step 1: Applying Railway optimizations...")
            optimization_result = railway_optimizer.optimize_for_railway()
            logger.info(f"Components Step 1: ✅ Railway optimization result: {optimization_result}")
            
            # Initialize Supabase schema (critical for database compatibility)
            logger.info("Components Step 1.5: Initializing Supabase schema...")
            try:
                supabase_results = initialize_supabase()
                if supabase_results['success']:
                    logger.info("✅ Supabase initialization completed successfully")
                    if supabase_results['sql_generated']:
                        logger.info("📝 Supabase schema SQL generated - check supabase_schema_setup.sql")
                else:
                    logger.warning("⚠️ Supabase initialization had issues - check logs")
            except Exception as supabase_error:
                logger.warning(f"Supabase initialization failed: {supabase_error}")
                logger.info("Application will continue with Railway-only mode")
            
            # Initialize basic components immediately (lightweight)
            logger.info("Components Step 2: Initializing basic components...")
            
            # Create SupabaseClient (lightweight)
            self.supabase = SupabaseClient()
            logger.info("Components Step 2.1: ✅ SupabaseClient created")
            
            # Create StorageManager (lightweight)
            self.storage = StorageManager()
            logger.info("Components Step 2.2: ✅ StorageManager created")
            
            # Create necessary directories (lightweight)
            self._create_directories()
            logger.info("Components Step 2.3: ✅ Directories created")
            
            # Initialize lazy loading flags
            self._db_manager_loaded = False
            self._ai_analyzer_loaded = False
            self._credit_manager_loaded = False
            self._backup_sync_loaded = False
            self._backup_health_manager_loaded = False
            
            logger.info("🎯 Core components initialized with lazy loading - heavy components will load on-demand")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize basic components: {e}")
            # Ensure we have basic functionality even if initialization fails
            if not hasattr(self, 'supabase'):
                self.supabase = SupabaseClient()
            if not hasattr(self, 'storage'):
                self.storage = StorageManager()
    
    async def _ensure_db_manager_loaded(self):
        """Ensure database manager is loaded on-demand"""
        if self._db_manager_loaded and hasattr(self, 'db_manager'):
            return self.db_manager
            
        try:
            logger.info("🔄 Loading database manager on-demand...")
            from models.database import DatabaseManager
            self.db_manager = DatabaseManager()
            
            # Initialize monitoring systems
            try:
                from intelligent_db_router import get_database_router
                self.db_router = get_database_router()
                
                from connection_pool_monitor import get_pool_monitor
                railway_db = getattr(self.db_manager, 'railway_pg', None)
                self.pool_monitor = get_pool_monitor(railway_db)
                self.pool_monitor.start_monitoring()
                
            except Exception as monitor_error:
                logger.warning(f"Failed to initialize monitoring systems: {monitor_error}")
                self.db_router = None
                self.pool_monitor = None
            
            self._db_manager_loaded = True
            logger.info("✅ Database manager loaded successfully")
            return self.db_manager
            
        except Exception as e:
            logger.error(f"Failed to load database manager: {e}")
            self.db_manager = None
            return None
    
    async def _ensure_ai_analyzer_loaded(self):
        """Ensure AI analyzer is loaded on-demand"""
        if self._ai_analyzer_loaded and hasattr(self, 'ai_analyzer'):
            return self.ai_analyzer
            
        try:
            logger.info("🔄 Initializing Unified AI Processor...")
            
            # Initialize the unified AI processor with database and cache
            if not hasattr(self, 'unified_ai_processor') or not self.unified_ai_processor:
                self.unified_ai_processor = initialize_unified_processor(
                    railway_db=self.railway_db,
                    cache_manager=getattr(self, 'cache_manager', None)
                )
            
            self._ai_analyzer_loaded = True
            logger.info("✅ Unified AI Processor initialized successfully")
            return self.unified_ai_processor
            
        except Exception as e:
            logger.error(f"Failed to initialize Unified AI Processor: {e}")
            self.unified_ai_processor = None
            return None
    
    async def _ensure_credit_manager_loaded(self):
        """Ensure credit manager is loaded on-demand"""
        if self._credit_manager_loaded and hasattr(self, 'credit_manager'):
            return self.credit_manager
            
        try:
            logger.info("🔄 Loading credit manager on-demand...")
            from credit_manager import CreditManager
            self.credit_manager = CreditManager()
            self._credit_manager_loaded = True
            logger.info("✅ Credit manager loaded successfully")
            return self.credit_manager
            
        except Exception as e:
            logger.warning(f"Failed to load credit manager: {e}")
            self.credit_manager = None
            return None
    
    async def _ensure_backup_health_manager_loaded(self):
        """Ensure backup health manager is loaded on-demand"""
        if self._backup_health_manager_loaded and hasattr(self, 'backup_health_manager'):
            return self.backup_health_manager
            
        try:
            logger.info("🔄 Loading backup health manager on-demand...")
            from utils.backup_health_manager import initialize_backup_health_manager
            
            # Get railway database for backup operations
            railway_db = getattr(self.db_manager, 'railway_pg', None) if self.db_manager else None
            
            # Get supabase client for backup sync
            supabase_client = getattr(self, 'supabase', None)
            
            # Initialize backup configuration
            backup_config = {
                'max_backup_age_hours': 24,
                'backup_retention_days': 30,
                'backup_directory': 'data/backups',
                'enable_compression': True,
                'backup_verification': True,
                'supabase_sync_enabled': True if supabase_client else False,
                'health_check_interval': 15,
                'max_response_time_ms': 5000,
                'max_connection_pool_usage': 80,
                'min_free_space_gb': 2
            }
            
            self.backup_health_manager = initialize_backup_health_manager(
                railway_db_manager=railway_db,
                supabase_client=supabase_client,
                config=backup_config
            )
            
            self._backup_health_manager_loaded = True
            logger.info("✅ Backup health manager loaded successfully")
            return self.backup_health_manager
            
        except Exception as e:
            logger.warning(f"Failed to load backup health manager: {e}")
            self.backup_health_manager = None
            return None
    
    def _create_directories(self):
        """Create necessary directories (lightweight operation)"""
        directories = ['uploads', 'processed', 'temp', 'logs']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
    def initialize_components(self):
        """DEPRECATED: Use initialize_components_lazy for memory optimization"""
        logger.warning("initialize_components called - redirecting to lazy initialization")
        self.initialize_components_lazy()
        """Initialize core system components with Railway optimization"""
        logger.info("🛠️ Initializing core system components...")
        try:
            # Apply Railway optimizations first
            logger.info("Components Step 1: Applying Railway optimizations...")
            optimization_result = railway_optimizer.optimize_for_railway()
            logger.info(f"Components Step 1: ✅ Railway optimization result: {optimization_result}")
            
            # Initialize hybrid database manager (Railway + Supabase)
            logger.info("Components Step 2: Initializing hybrid database manager...")
            try:
                from models.database import DatabaseManager
                self.db_manager = DatabaseManager()
                logger.info("Components Step 2: ✅ Hybrid database manager initialized")
                
                # Initialize our new monitoring systems (Solutions 1, 2, 4, 5)
                logger.info("Components Step 2.1: Initializing advanced monitoring systems...")
                try:
                    # Initialize intelligent database router (Solution 2)
                    from intelligent_db_router import get_database_router
                    self.db_router = get_database_router()
                    logger.info("✅ Intelligent Database Router initialized")
                    
                    # Initialize connection pool monitor (Solution 4)
                    from connection_pool_monitor import get_pool_monitor
                    railway_db = getattr(self.db_manager, 'railway_pg', None)
                    self.pool_monitor = get_pool_monitor(railway_db)
                    self.pool_monitor.start_monitoring()
                    logger.info("✅ Connection Pool Monitor started")
                    
                    # Enhanced Railway Optimizer (Solution 5) - already initialized above
                    logger.info("✅ Enhanced Railway Optimizer active")
                    
                except Exception as monitor_error:
                    logger.warning(f"Failed to initialize monitoring systems: {monitor_error}")
                    self.db_router = None
                    self.pool_monitor = None
                
                # Log database configuration
                logger.info(f"Primary database: {getattr(self.db_manager, 'primary_db', 'unknown')}")
                logger.info(f"Railway available: {hasattr(self.db_manager, 'railway_pg') and self.db_manager.railway_pg is not None}")
                logger.info(f"Supabase available: {hasattr(self.db_manager, 'supabase') and self.db_manager.supabase is not None}")
                logger.info(f"Backup sync enabled: {hasattr(self.db_manager, 'backup_sync') and self.db_manager.backup_sync is not None}")
                
                # Initialize Railway backup sync if available (DISABLED FOR INITIAL DEPLOYMENT)
                if (RAILWAY_AVAILABLE and hasattr(self.db_manager, 'railway_pg') and 
                    self.db_manager.railway_pg is not None and 
                    os.getenv('BACKUP_SYNC_ENABLED', 'false').lower() == 'true'):  # Changed default to 'false'
                    
                    logger.info("Initializing Railway backup sync manager...")
                    try:
                        from backup_sync import BackupSyncManager
                        self.backup_sync = BackupSyncManager(
                            self.db_manager.railway_pg, 
                            self.db_manager.supabase
                        )
                        self.backup_sync.start_background_sync()
                        logger.info("✅ Railway backup sync manager started")
                    except Exception as sync_error:
                        logger.warning(f"Failed to start backup sync: {sync_error}")
                        self.backup_sync = None
                else:
                    logger.info("Railway backup sync disabled for initial deployment (set BACKUP_SYNC_ENABLED=true to enable)")
                    self.backup_sync = None
                
            except Exception as e:
                logger.error(f"Failed to initialize database manager: {e}")
                # Fallback to basic Supabase client
                logger.info("Falling back to basic Supabase client...")
                self.supabase = SupabaseClient()
                self.db_manager = None
                self.backup_sync = None
                
            logger.info("Components Step 3: Creating SupabaseClient (if not already initialized)...")
            if not hasattr(self, 'supabase'):
                self.supabase = SupabaseClient()
            logger.info("Components Step 3: ✅ SupabaseClient ensured")
            
            logger.info("Components Step 4: Creating StorageManager...")
            self.storage = StorageManager()
            logger.info("Components Step 4: ✅ StorageManager created")
            
            # Initialize AI analyzer with credit manager for premium routing
            logger.info("Components Step 5: Initializing Unified AI Processor...")
            
            # Initialize unified AI processor instead of multiple instances
            self.unified_ai_processor = initialize_unified_processor(
                railway_db=self.railway_db,
                cache_manager=getattr(self, 'cache_manager', None)
            )
            
            # Keep backward compatibility
            self.ai_analyzer = self.unified_ai_processor
            
            logger.info("✅ Unified AI Processor initialized with admin-configurable models")
            logger.info("Components Step 5: ✅ AI processing system ready")
            
            # Create necessary directories
            logger.info("Components Step 6: Creating necessary directories...")
            os.makedirs('uploads', exist_ok=True)
            logger.info("✅ uploads directory ensured")
            os.makedirs('processed', exist_ok=True)
            logger.info("✅ processed directory ensured")
            os.makedirs('logs', exist_ok=True)
            logger.info("✅ logs directory ensured")
            logger.info("Components Step 6: ✅ Directories created")
            
            # Initialize service health management
            logger.info("Components Step 7: Initializing service health management...")
            try:
                from utils.service_health_manager import init_service_health_monitoring
                
                init_service_health_monitoring(
                    railway_db=self.railway_db,
                    cache_manager=getattr(self, 'cache_manager', None),
                    ai_processor=self.unified_ai_processor
                )
                
                logger.info("Components Step 7: ✅ Service health management initialized")
            except Exception as health_error:
                logger.warning(f"Service health management initialization failed: {health_error}")
                # Continue without health management - not critical
            
            # Register health endpoints (critical and service-specific)
            logger.info("Components Step 8: Registering health endpoints (critical and service-specific)...")
            try:
                # Ensure critical health endpoints (/health, /api/health) are registered first
                self._register_critical_health_endpoints()
                # Then register service-specific health endpoints (/health/<service_name>)
                self._register_health_endpoints()
                logger.info("Components Step 8: ✅ All health endpoints registered")
            except Exception as health_endpoint_error:
                logger.warning(f"Health endpoints registration failed: {health_endpoint_error}")
            
            logger.info("🛠️ All components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
            
    def _register_critical_health_endpoints(self):
        """Register critical health endpoints first to ensure Railway deployment works"""
        logger.info("🏥 Registering critical health endpoints...")
        
        @self.app.route('/health', methods=['GET'])
        @self.app.route('/', methods=['GET'])
        def railway_health_check():
            """Primary health check endpoint for Railway"""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "2.0.0-railway-critical-fix",
                "message": "HR ATS System Operational",
                "service": "hr-tools-backend"
            })
        
        @self.app.route('/api/health', methods=['GET'])
        def api_health_simple():
            """API health check endpoint"""
            return jsonify({
                "status": "ok",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "hr-tools-api"
            })
        
        logger.info("🏥 ✅ Critical health endpoints registered successfully")
    
    def register_routes(self):
        """Register all application routes including enhanced authentication"""
        logger.info("🛣️ Registering application routes...")
        
        # Import and register authentication routes
        logger.info("Routes Step 1: Importing auth routes...")
        try:
            from routes.auth import auth_bp, init_auth_routes
            logger.info("Routes Step 1: ✅ Auth routes imported successfully")
        except Exception as e:
            logger.error(f"❌ Failed to import auth routes: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise
        
        logger.info("Routes Step 1a: Initializing auth routes...")
        try:
            init_auth_routes(self.db_manager)
            logger.info("Routes Step 1a: ✅ Auth routes initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize auth routes: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise
        
        logger.info("Routes Step 1b: Registering auth blueprint...")
        try:
            self.app.register_blueprint(auth_bp)
            logger.info("Routes Step 1b: ✅ Auth blueprint registered")
        except Exception as e:
            logger.error(f"❌ Failed to register auth blueprint: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise
        
        # Import and register admin routes
        logger.info("Routes Step 2: Importing admin routes...")
        try:
            from routes.admin import admin_bp, init_admin_routes
            logger.info("Routes Step 2: ✅ Admin routes imported successfully")
        except Exception as e:
            logger.error(f"❌ Failed to import admin routes: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise
        
        logger.info("Routes Step 2a: Initializing admin routes...")
        try:
            init_admin_routes(self.db_manager)
            logger.info("Routes Step 2a: ✅ Admin routes initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize admin routes: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise
        
        logger.info("Routes Step 2b: Registering admin blueprint...")
        try:
            self.app.register_blueprint(admin_bp)
            logger.info("Routes Step 2b: ✅ Admin blueprint registered")
        except Exception as e:
            logger.error(f"❌ Failed to register admin blueprint: {e}")
        
        # Register Admin AI Configuration Routes
        logger.info("Routes Step 2c: Setting up admin AI configuration routes...")
        try:
            from routes.admin_ai import admin_ai_bp, init_admin_ai_routes
            
            # Initialize admin AI routes with dependencies
            init_admin_ai_routes(
                railway_database=self.railway_db,
                auth_mid=self.auth  # Fixed: was self.auth_middleware, should be self.auth
            )
            
            # Register the blueprint
            self.app.register_blueprint(admin_ai_bp)
            logger.info("Routes Step 2c: ✅ Admin AI configuration routes registered")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize admin AI routes: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            # Continue without admin AI routes - not critical for basic functionality
            logger.error(f"Error type: {type(e).__name__}")
            raise
        
        # Register Backup Management Routes (Phase 6)
        logger.info("Routes Step 2d: Setting up backup management routes...")
        try:
            from routes.backup_management import backup_bp, init_backup_routes
            
            # Initialize backup routes
            init_backup_routes(self.app)
            logger.info("Routes Step 2d: ✅ Backup management routes registered")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize backup management routes: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            # Continue without backup routes - not critical for basic functionality
            logger.warning("Continuing without backup management routes (non-critical)")
        
        # Import and register payment routes (Phase 2)
        logger.info("Routes Step 3: Checking credit manager for payment routes...")
        if self.credit_manager:
            logger.info("Credit manager available, importing payment routes...")
            try:
                from routes.payment import payment_bp, init_payment_routes
                logger.info("✅ Payment routes imported successfully")
                
                logger.info("Initializing payment routes...")
                init_payment_routes(self.db_manager, self.credit_manager, self.auth)
                logger.info("✅ Payment routes initialized")
                
                logger.info("Registering payment blueprint...")
                self.app.register_blueprint(payment_bp)
                logger.info("Payment routes registered successfully")
            except Exception as e:
                logger.error(f"Failed to register payment routes: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                logger.info("Continuing without payment routes (non-breaking)")
        else:
            logger.warning("Credit manager not available - payment routes skipped")
        
        # Import and register user routes (Phase 1 - CRITICAL)
        logger.info("Routes Step 3.5: Importing and registering user routes...")
        try:
            from routes.user import user_bp, init_user_routes
            logger.info("✅ User routes imported successfully")
            
            logger.info("Initializing user routes...")
            railway_db = getattr(self.db_manager, 'railway_pg', None) if self.db_manager else None
            init_user_routes(
                database_manager=self.db_manager,
                railway_database=railway_db,
                auth_mid=self.auth,
                storage_mgr=getattr(self, 'storage', None),
                credit_mgr=self.credit_manager
            )
            logger.info("✅ User routes initialized")
            
            logger.info("Registering user blueprint...")
            self.app.register_blueprint(user_bp)
            logger.info("✅ User routes registered successfully - CRITICAL ENDPOINTS NOW AVAILABLE")
        except Exception as e:
            logger.error(f"❌ Failed to register user routes: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            # This is critical - don't continue silently
            logger.error("CRITICAL: User routes registration failed - this blocks frontend functionality")
            # For development, continue without failing the entire app
            logger.warning("Continuing without user routes for development purposes")
        
        logger.info("Routes Step 4: Registering core health check endpoints...")
        
        # Register enhanced health monitoring dashboard (Enhanced Production Version)
        logger.info("Routes Step 4a: Registering enhanced health monitoring dashboard...")
        try:
            from enhanced_health_monitor import create_health_endpoints
            
            # Create enhanced health endpoints
            create_health_endpoints(self.app)
            logger.info("Routes Step 4a: ✅ Enhanced production health monitoring registered")
            
            # Also try to register existing health dashboard if available
            try:
                from health_dashboard import health_bp, initialize_monitoring
                self.app.register_blueprint(health_bp)
                initialize_monitoring()
                logger.info("Routes Step 4a: ✅ Additional health dashboard registered")
            except ImportError:
                logger.info("Routes Step 4a: ⚠️ Legacy health dashboard not available - using enhanced monitoring only")
                
        except Exception as e:
            logger.warning(f"Failed to register enhanced health monitoring: {e}")
            # Fallback to simple health check
            logger.info("Routes Step 4a: 🔄 Falling back to basic health monitoring")
        
        
        
        # Railway health check endpoint (what Railway expects) - DISABLED TO AVOID CONFLICTS
        # @self.app.route('/health', methods=['GET'])
        # def railway_health_check():
        #     """Railway platform health check endpoint"""
        #     return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})
        
        # Simple health check endpoint for Railway
        @self.app.route('/api/health', methods=['GET'])
        def simple_health_check():
            """Simple health check endpoint for Railway load balancer"""
            return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})
        
        # Memory monitoring endpoint
        @self.app.route('/api/memory', methods=['GET'])
        def memory_status():
            """Memory monitoring endpoint for production debugging"""
            try:
                from memory_monitor import get_memory_report, check_memory_health
                
                action = request.args.get('action', 'report')
                
                if action == 'health':
                    health_data = check_memory_health()
                    return jsonify(health_data)
                else:
                    report_data = get_memory_report()
                    return jsonify(report_data)
                    
            except ImportError:
                return jsonify({
                    "error": "Memory monitor not available",
                    "status": "unavailable"
                }), 404
            except Exception as e:
                logger.error(f"Memory status error: {e}")
                return jsonify({
                    "error": str(e),
                    "status": "error"
                }), 500
        
        logger.info("✅ Simple health check endpoint registered")
        
        # ======================================================================
        # ADVANCED FEATURES INTEGRATION (5 Feature Sets) - NOW ENABLED FOR RAILWAY
        # ======================================================================
        logger.info("🚀 Advanced Features now enabled for Railway deployment")
        logger.info("Railway database optimizations allow for advanced features")
        
        # Enable advanced features on Railway now that database optimizations are in place
        railway_deployment = os.getenv('RAILWAY_ENVIRONMENT') == 'production'
        
        # Always register advanced features (Railway optimizations now support this)
        logger.info("🚀 Registering Advanced Features (Phase 2 Enhancement)...")
        try:
            self._register_advanced_features()
            logger.info("✅ Advanced Features successfully enabled for Railway deployment")
        except Exception as e:
            logger.warning(f"⚠️ Advanced Features registration failed, using fallback: {e}")
            # Set default attributes to prevent errors
            self.realtime_manager = None
            self.bulk_operations_manager = None
            self.search_engine = None
            self.performance_monitor = None
            self.memory_cache = None
            self.response_formatter = None
        
        # ======================================================================
        # ADVANCED FEATURES STATUS SUMMARY
        # ======================================================================
        logger.info("🎉 Route registration completed!")
        logger.info("📊 Features Status Summary:")
        
        # Show actual feature availability based on successful registration
        websocket_available = hasattr(self, 'realtime_manager') and self.realtime_manager is not None
        bulk_ops_available = hasattr(self, 'bulk_operations_manager') and self.bulk_operations_manager is not None
        search_available = hasattr(self, 'search_engine') and self.search_engine is not None
        performance_available = hasattr(self, 'performance_monitor') and self.performance_monitor is not None
        data_structure_available = hasattr(self, 'response_formatter') and self.response_formatter is not None
        
        logger.info(f"   • WebSocket Real-time: {'✅ Available' if websocket_available else '❌ Unavailable'}")
        logger.info(f"   • Bulk Operations: {'✅ Available' if bulk_ops_available else '❌ Unavailable'}")
        logger.info(f"   • Advanced Search: {'✅ Available' if search_available else '❌ Unavailable'}")
        logger.info(f"   • Performance Helpers: {'✅ Available' if performance_available else '❌ Unavailable'}")
        logger.info(f"   • Enhanced Data Structure: {'✅ Available' if data_structure_available else '❌ Unavailable'}")
        
        # Environment information (separate from feature capability)
        environment = os.getenv('RAILWAY_ENVIRONMENT', 'development')
        logger.info(f"🌍 Environment: {environment}")
        
        # Summary
        available_features = sum([websocket_available, bulk_ops_available, search_available, performance_available, data_structure_available])
        logger.info(f"🚀 Application ready with {available_features}/5 advanced features enabled")
    
    def _register_advanced_features(self):
        """Register advanced features (only for non-Railway environments)"""
        logger.info("�🚀 Registering Advanced Features (Phase 2 Enhancement)...")
        
        # Advanced Feature 1: WebSocket Real-time Data Features
        logger.info("Routes Step 6: Importing WebSocket real-time features...")
        try:
            from routes.websocket import websocket_bp, init_websocket_routes
            from utils.realtime_manager import RealtimeManager
            
            # Initialize realtime manager
            self.realtime_manager = RealtimeManager()
            
            # Initialize WebSocket routes with dependencies
            init_websocket_routes(
                realtime_manager=self.realtime_manager,
                db_manager=self.db_manager
            )
            
            # Register WebSocket blueprint
            self.app.register_blueprint(websocket_bp)
            logger.info("Routes Step 6: ✅ WebSocket real-time features registered")
            
        except Exception as e:
            logger.warning(f"WebSocket real-time features registration failed: {e}")
            logger.warning("Continuing without real-time features (non-breaking)")
            self.realtime_manager = None
        
        # Advanced Feature 2: Bulk Operations Enhancement
        logger.info("Routes Step 7: Importing bulk operations enhancement...")
        try:
            from routes.bulk import bulk_bp, init_bulk_routes
            from utils.bulk_operations import BulkOperationsManager
            
            # Initialize bulk operations manager
            self.bulk_operations_manager = BulkOperationsManager(
                db_manager=self.db_manager,
                realtime_manager=getattr(self, 'realtime_manager', None)
            )
            
            # Initialize bulk routes with dependencies
            init_bulk_routes(
                bulk_manager_instance=self.bulk_operations_manager,
                db_manager=self.db_manager,
                auth_middleware=self.auth
            )
            
            # Register bulk operations blueprint
            self.app.register_blueprint(bulk_bp)
            logger.info("Routes Step 7: ✅ Bulk operations enhancement registered")
            
        except Exception as e:
            logger.warning(f"Bulk operations enhancement registration failed: {e}")
            logger.warning("Continuing without bulk operations (non-breaking)")
        
        # Advanced Feature 3: Advanced Search & Filtering
        logger.info("Routes Step 8: Importing advanced search & filtering...")
        try:
            from routes.search import search_bp, init_search_routes
            from utils.advanced_search import AdvancedSearchEngine
            
            # Initialize advanced search engine
            self.search_engine = AdvancedSearchEngine(
                db_manager=self.db_manager
            )
            
            # Initialize search routes with dependencies
            init_search_routes(
                search_engine_param=self.search_engine,
                db_manager=self.db_manager,
                auth_middleware=self.auth
            )
            
            # Register advanced search blueprint
            self.app.register_blueprint(search_bp)
            logger.info("Routes Step 8: ✅ Advanced search & filtering registered")
            
        except Exception as e:
            logger.warning(f"Advanced search & filtering registration failed: {e}")
            logger.warning("Continuing without advanced search (non-breaking)")
        
        # Advanced Feature 4: Frontend Performance Helpers
        logger.info("Routes Step 9: Importing frontend performance helpers...")
        try:
            from routes.performance import performance_bp
            from utils.performance_helpers import PerformanceMonitor, MemoryCache
            
            # Initialize performance components
            self.performance_monitor = PerformanceMonitor()
            self.memory_cache = MemoryCache(max_size=1000)
            
            # Register performance helpers blueprint (no auth injection for now)
            self.app.register_blueprint(performance_bp)
            logger.info("Routes Step 9: ✅ Frontend performance helpers registered")
            
        except Exception as e:
            logger.warning(f"Frontend performance helpers registration failed: {e}")
            logger.warning("Continuing without performance helpers (non-breaking)")
        
        # Ollama Test Routes (for Railway testing)
        logger.info("Routes Step 9.5: Registering Ollama test routes...")
        try:
            from routes.ollama_test import ollama_test_bp
            self.app.register_blueprint(ollama_test_bp)
            logger.info("Routes Step 9.5: ✅ Ollama test routes registered")
        except Exception as e:
            logger.warning(f"Ollama test routes registration failed: {e}")
            logger.warning("Continuing without Ollama test routes (non-breaking)")
        
        # Advanced Feature 5: Enhanced Frontend Data Structure
        logger.info("Routes Step 10: Initializing enhanced frontend data structure...")
        try:
            from utils.response_formatter import EnhancedResponseFormatter
            
            # Initialize enhanced response formatter
            self.response_formatter = EnhancedResponseFormatter()
            
            logger.info("Routes Step 10: ✅ Enhanced frontend data structure initialized")
            
        except Exception as e:
            logger.warning(f"Enhanced frontend data structure initialization failed: {e}")
            logger.warning("Continuing without enhanced response formatting (non-breaking)")
        
        @self.app.route('/api/rag/health', methods=['GET'])
        @self.app.route('/rag/health', methods=['GET'])
        def rag_health_check():
            """HR Legal RAG System health check endpoint"""
            try:
                from modules.hr_legal_rag.hr_legal_rag import get_rag_health
                rag_status = get_rag_health()
                
                return jsonify({
                    "status": "healthy" if rag_status.get("system_status") in ["operational", "fallback"] else "unhealthy",
                    "rag_system": rag_status,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"RAG health check error: {e}")
                return jsonify({
                    "status": "unhealthy",
                    "error": str(e),
                    "fallback_available": True,
                    "timestamp": datetime.utcnow().isoformat()
                }), 500
        
        # Credit System Health Check (B2B SaaS)
        @self.app.route('/api/credits/health', methods=['GET'])
        def credit_system_health():
            """Credit system health check endpoint with thread-safe timeout"""
            import concurrent.futures
            
            try:
                if not self.credit_middleware:
                    return jsonify({
                        "status": "unavailable",
                        "message": "Credit system not initialized",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # Use ThreadPoolExecutor for thread-safe timeout
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self.credit_middleware.health_check)
                    try:
                        health_status = future.result(timeout=15)  # 15-second timeout
                        return jsonify(health_status)
                    except concurrent.futures.TimeoutError:
                        logger.warning("Credit health check timed out, returning cached status")
                        return jsonify({
                            "status": "timeout",
                            "message": "Health check timed out, system may be under load",
                            "timestamp": datetime.utcnow().isoformat()
                        }), 503
                
            except Exception as e:
                logger.error(f"Credit system health check error: {e}")
                return jsonify({
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }), 500
        
        # Railway Performance Monitoring Endpoints
        @self.app.route('/api/railway/performance', methods=['GET'])
        @self.auth.require_admin
        def railway_performance():
            """Railway performance monitoring endpoint"""
            try:
                performance_report = railway_optimizer.get_performance_report()
                return jsonify({
                    "success": True,
                    "railway_performance": performance_report
                })
            except Exception as e:
                logger.error(f"Railway performance error: {e}")
                return jsonify({"error": "Failed to get Railway performance"}), 500
        
        # Railway Database Monitoring Endpoints (if available)
        if self.db_manager and hasattr(self.db_manager, 'railway_pg') and self.db_manager.railway_pg:
            logger.info("Routes Step 5: Registering Railway database monitoring routes...")
            
            @self.app.route('/api/database/health', methods=['GET'])
            @self.auth.require_admin
            def database_health():
                """Database health monitoring endpoint"""
                try:
                    health_status = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "primary_db": getattr(self.db_manager, 'primary_db', 'unknown'),
                        "services": {}
                    }
                    
                    # Railway PostgreSQL health
                    if hasattr(self.db_manager, 'railway_pg') and self.db_manager.railway_pg:
                        try:
                            health_status["services"]["railway"] = self.db_manager.railway_pg.health_check()
                        except Exception as e:
                            health_status["services"]["railway"] = {"status": "unhealthy", "error": str(e)}
                    
                    # Supabase health
                    if hasattr(self.db_manager, 'supabase') and self.db_manager.supabase:
                        try:
                            health_status["services"]["supabase"] = self.db_manager.supabase.health_check()
                        except Exception as e:
                            health_status["services"]["supabase"] = {"status": "unhealthy", "error": str(e)}
                    
                    # Overall status
                    all_healthy = all(
                        service.get("status") == "healthy" 
                        for service in health_status["services"].values()
                    )
                    health_status["overall_status"] = "healthy" if all_healthy else "degraded"
                    
                    return jsonify(health_status)
                    
                except Exception as e:
                    logger.error(f"Database health check error: {e}")
                    return jsonify({
                        "overall_status": "error",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }), 500
            
            @self.app.route('/api/database/backup-sync/status', methods=['GET'])
            @self.auth.require_admin
            def backup_sync_status():
                """Backup sync status monitoring endpoint"""
                try:
                    if not self.backup_sync:
                        return jsonify({
                            "status": "disabled",
                            "message": "Backup sync not configured",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    
                    sync_status = self.backup_sync.get_status()
                    return jsonify({
                        "status": "active",
                        "sync_status": sync_status,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"Backup sync status error: {e}")
                    return jsonify({
                        "status": "error",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }), 500
            
            @self.app.route('/api/database/performance', methods=['GET'])
            @self.auth.require_admin
            def database_performance():
                """Database performance metrics endpoint"""
                try:
                    performance_data = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "metrics": {}
                    }
                    
                    # Railway performance metrics
                    if hasattr(self.db_manager, 'railway_pg') and self.db_manager.railway_pg:
                        try:
                            railway_health = self.db_manager.railway_pg.health_check()
                            performance_data["metrics"]["railway"] = {
                                "status": railway_health.get("status", "unknown"),
                                "pool_size": railway_health.get("pool_size", 0),
                                "pool_max": railway_health.get("pool_max", 0),
                                "database": railway_health.get("database", "unknown")
                            }
                        except Exception as e:
                            performance_data["metrics"]["railway"] = {"error": str(e)}
                    
                    # System metrics
                    try:
                        performance_data["system"] = {
                            "memory_usage": psutil.virtual_memory().percent,
                            "cpu_usage": psutil.cpu_percent(interval=0.1)
                        }
                    except Exception as e:
                        performance_data["system"] = {"error": str(e)}
                    
                    return jsonify(performance_data)
                    
                except Exception as e:
                    logger.error(f"Database performance error: {e}")
                    return jsonify({
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }), 500
            
            logger.info("✅ Railway database monitoring routes registered")
        else:
            logger.info("Railway database monitoring routes skipped (Railway not available)")
        
        @self.app.route('/api/railway/optimize', methods=['POST'])
        @self.auth.require_admin
        def railway_optimize():
            """Trigger Railway optimization"""
            try:
                optimization_result = railway_optimizer.optimize_for_railway()
                return jsonify({
                    "success": True,
                    "optimization_result": optimization_result
                })
            except Exception as e:
                logger.error(f"Railway optimization error: {e}")
                return jsonify({"error": "Failed to optimize Railway"}), 500
        
        @self.app.route('/api/railway/memory', methods=['GET'])
        @self.auth.require_admin
        def railway_memory():
            """Railway memory usage endpoint"""
            try:
                memory_usage = railway_optimizer.get_memory_usage()
                return jsonify({
                    "success": True,
                    "memory_usage": memory_usage
                })
            except Exception as e:
                logger.error(f"Railway memory error: {e}")
                return jsonify({"error": "Failed to get memory usage"}), 500
        
        # Queue Management Endpoints (B2B SaaS)
        @self.app.route('/api/queue/add', methods=['POST'])
        @self.auth.require_auth
        def add_to_queue():
            """Add request to processing queue"""
            try:
                if not self.credit_middleware:
                    return jsonify({"error": "Credit system not available"}), 503
                
                from credit_middleware import handle_queue_request
                return handle_queue_request(self.credit_middleware)
                
            except Exception as e:
                logger.error(f"Queue add error: {e}")
                return jsonify({"error": "Failed to add to queue"}), 500
        
        @self.app.route('/api/queue/status/<request_id>', methods=['GET'])
        @self.auth.require_auth
        def get_queue_status(request_id):
            """Get status of queued request"""
            try:
                if not self.credit_middleware:
                    return jsonify({"error": "Credit system not available"}), 503
                
                from credit_middleware import handle_request_status
                return handle_request_status(self.credit_middleware, request_id)
                
            except Exception as e:
                logger.error(f"Queue status error: {e}")
                return jsonify({"error": "Failed to get status"}), 500
        
        # Legacy compatibility endpoints (redirects to new auth system)
        @self.app.route('/api/auth/login', methods=['POST'])
        def legacy_login():
            """Legacy login endpoint - redirects to new auth system"""
            return jsonify({
                "message": "Please use /api/auth/user-login for user login or /api/auth/admin-login for admin login",
                "new_endpoints": {
                    "user_login": "/api/auth/user-login",
                    "admin_login": "/api/auth/admin-login"
                }
            }), 301
                
        @self.app.route('/api/auth/register', methods=['POST'])
        def legacy_register():
            """Legacy register endpoint - now admin-only user creation"""
            return jsonify({
                "message": "User registration is now admin-only. Please contact administrator.",
                "admin_endpoint": "/api/auth/create-user"
            }), 301        # Resume processing routes
        @self.app.route('/api/upload', methods=['POST'])
        @self.auth.require_auth
        def upload_resume():
            """Upload and process resume files with automatic AI analysis"""
            try:
                user = self.auth.get_current_user()
                
                # Check trial limits
                if not self.auth.check_trial_limits(user['user_id']):
                    return jsonify({"error": "Trial limit exceeded"}), 403
                
                # Handle both 'files' and 'file' field names for compatibility
                files = []
                if 'files' in request.files:
                    files = request.files.getlist('files')
                elif 'file' in request.files:
                    files = [request.files['file']]
                
                if not files:
                    return jsonify({"error": "No files provided"}), 400
                
                results = []
                successful_uploads = 0
                
                for file in files:
                    if file and file.filename and self.is_allowed_file(file.filename):
                        try:
                            result = self.process_resume_file(file, user)
                            results.append(result)
                            
                            # Increment trial usage if successful
                            if result.get('status') == 'uploaded':
                                successful_uploads += 1
                                self.auth.increment_trial_usage(user['user_id'], 'resume')
                                
                        except Exception as file_error:
                            logger.error(f"Error processing file {file.filename}: {file_error}")
                            results.append({
                                "filename": file.filename,
                                "status": "error",
                                "error": str(file_error)
                            })
                    else:
                        results.append({
                            "filename": file.filename if file else "unknown",
                            "status": "error",
                            "error": "File type not allowed or invalid file"
                        })
                
                # Enhanced response format (matches admin upload)
                response_data = {
                    "success": successful_uploads > 0,
                    "results": results,
                    "processed_count": len(results),
                    "successful_uploads": successful_uploads,
                    "ai_processing_enabled": True,
                    "message": f"Processed {len(results)} files, {successful_uploads} successful uploads with AI analysis"
                }
                
                # Add individual result details for single file uploads
                if len(results) == 1:
                    single_result = results[0]
                    if single_result.get('status') == 'uploaded':
                        response_data.update({
                            "resume_id": single_result.get('resume_id'),
                            "filename": single_result.get('filename'),
                            "processing_status": single_result.get('processing_status'),
                            "ai_processing": single_result.get('ai_processing', True),
                            "note": single_result.get('note', 'AI analysis is running in background')
                        })
                
                return jsonify(response_data)
                
            except Exception as e:
                logger.error(f"Upload error: {e}")
                return jsonify({
                    "success": False,
                    "error": "Upload failed",
                    "message": str(e)
                }), 500
                
        @self.app.route('/api/analyze/<resume_id>', methods=['POST'])
        @self.auth.require_auth
        def analyze_resume(resume_id):
            """Analyze resume with 4-agent system - Enhanced with B2B credit system"""
            try:
                user = self.auth.get_current_user()
                user_id = user['user_id']
                
                # Get job requirements if provided
                data = request.get_json() or {}
                job_requirements = data.get('job_requirements', {})
                
                # B2B SaaS Enhancement: Credit-aware processing
                if self.credit_middleware:
                    try:
                        # Check credit status
                        credit_status = self.credit_manager.check_user_credits(user_id)
                        
                        # If no credits available, return monetization options
                        if not credit_status.can_process:
                            return jsonify({
                                "success": False,
                                "error": "insufficient_credits",
                                "message": "Your trial credits have been exhausted",
                                "credit_status": {
                                    "trial_credits": credit_status.trial_credits,
                                    "premium_credits": credit_status.premium_credits,
                                    "total_used": credit_status.total_used,
                                    "credits_remaining": credit_status.credits_remaining
                                },
                                "monetization_options": self.credit_middleware.offer_premium_options(credit_status),
                                "trial_completed": True
                            }), 402  # Payment Required
                        
                        # Check if queue is busy
                        queue_status = self.queue_manager.get_queue_status()
                        from queue_manager import QueueStatus
                        from credit_manager import ProcessingTier
                        
                        if (queue_status in [QueueStatus.BUSY, QueueStatus.OVERLOADED] and 
                            credit_status.processing_tier == ProcessingTier.FREE_TRIAL):
                            # Queue the request
                            request_data = {
                                'resume_id': resume_id,
                                'resume_text': self._get_resume_text(resume_id, user_id),
                                'job_requirements': job_requirements
                            }
                            
                            request_id, queue_info = self.queue_manager.add_request(
                                str(user_id), "resume_analysis", request_data, credit_status.processing_tier
                            )
                            
                            return jsonify({
                                "success": False,
                                "status": "queued",
                                "message": "System is busy. Request queued for processing.",
                                "request_id": request_id,
                                "queue_info": queue_info,
                                "options": {
                                    "wait_in_queue": {
                                        "description": "Free - wait in queue for processing",
                                        "estimated_wait": f"{queue_info.get('estimated_wait_minutes', 2)} minutes"
                                    },
                                    "skip_queue": {
                                        "description": "Skip the queue for instant processing",
                                        "price_inr": 40,
                                        "action": "POST /api/payment/queue-skip"
                                    }
                                }
                            }), 202  # Accepted - will be processed later
                        
                        # Deduct credits for immediate processing
                        if not self.credit_manager.deduct_credits(user_id, 1, "resume_analysis", credit_status.processing_tier):
                            return jsonify({
                                "success": False,
                                "error": "credit_deduction_failed",
                                "message": "Failed to deduct credits"
                            }), 402
                        
                    except Exception as credit_error:
                        logger.error(f"Credit system error (non-breaking): {credit_error}")
                        # Continue with legacy processing if credit system fails
                
                # Original processing logic (unchanged for backward compatibility)
                analysis_result = self.ai_analyzer.analyze_resume(
                    resume_id, job_requirements, user_id
                )
                
                # Store analysis results
                self.supabase.store_analysis_result(
                    resume_id, analysis_result, user_id
                )
                
                # Enhanced response with credit info
                response_data = {
                    "success": True,
                    "analysis": analysis_result
                }
                
                # Add credit status if available
                if self.credit_middleware:
                    try:
                        updated_status = self.credit_manager.check_user_credits(user_id)
                        response_data["credit_status"] = {
                            "credits_remaining": updated_status.credits_remaining,
                            "total_used": updated_status.total_used
                        }
                    except Exception:
                        pass  # Non-breaking
                
                return jsonify(response_data)
                
            except Exception as e:
                logger.error(f"Analysis error: {e}")
                return jsonify({"error": "Analysis failed"}), 500
        
        @self.app.route('/api/analyze/batch', methods=['POST'])
        @self.auth.require_auth
        def analyze_resume_batch():
            """Analyze multiple resumes with comparative ranking - Enhanced with B2B credit system"""
            try:
                user = self.auth.get_current_user()
                user_id = user['user_id']
                
                # Get request data
                data = request.get_json() or {}
                resume_batch = data.get('resumes', [])
                job_requirements = data.get('job_requirements', {})
                
                if not resume_batch:
                    return jsonify({"error": "No resumes provided for batch analysis"}), 400
                
                # Validate batch size (limit to prevent overload)
                max_batch_size = 20
                if len(resume_batch) > max_batch_size:
                    return jsonify({
                        "error": f"Batch size too large. Maximum {max_batch_size} resumes allowed"
                    }), 400
                
                # B2B SaaS Enhancement: Credit-aware processing (5 credits for batch)
                credits_needed = 5
                if self.credit_middleware:
                    try:
                        # Check credit status
                        credit_status = self.credit_manager.check_user_credits(user_id)
                        
                        # If insufficient credits, return monetization options
                        if credit_status.credits_remaining < credits_needed:
                            return jsonify({
                                "success": False,
                                "error": "insufficient_credits",
                                "message": f"Batch analysis requires {credits_needed} credits. You have {credit_status.credits_remaining}.",
                                "feature": "batch_analysis",
                                "credits_needed": credits_needed,
                                "credit_status": {
                                    "trial_credits": credit_status.trial_credits,
                                    "premium_credits": credit_status.premium_credits,
                                    "credits_remaining": credit_status.credits_remaining
                                },
                                "monetization_options": self.credit_middleware.offer_premium_options(credit_status)
                            }), 402  # Payment Required
                        
                        # Check if queue is busy - batch analysis also uses queue
                        queue_status = self.queue_manager.get_queue_status()
                        from queue_manager import QueueStatus
                        from credit_manager import ProcessingTier
                        
                        if (queue_status in [QueueStatus.BUSY, QueueStatus.OVERLOADED] and 
                            credit_status.processing_tier == ProcessingTier.FREE_TRIAL):
                            # Queue the batch analysis
                            request_data = {
                                'resumes': resume_batch,
                                'job_requirements': job_requirements
                            }
                            
                            request_id, queue_info = self.queue_manager.add_request(
                                str(user_id), "batch_analysis", request_data, credit_status.processing_tier
                            )
                            
                            return jsonify({
                                "success": False,
                                "status": "queued", 
                                "message": f"System is busy. Batch analysis queued for processing (will use {credits_needed} credits).",
                                "request_id": request_id,
                                "queue_info": queue_info,
                                "feature": "batch_analysis",
                                "credits_required": credits_needed
                            }), 202  # Accepted - will be processed later
                        
                        # Deduct credits for immediate processing
                        if not self.credit_manager.deduct_credits(user_id, credits_needed, "batch_analysis", credit_status.processing_tier):
                            return jsonify({
                                "success": False,
                                "error": "credit_deduction_failed",
                                "message": f"Failed to deduct {credits_needed} credits for batch analysis"
                            }), 402
                        
                    except Exception as credit_error:
                        logger.error(f"Credit system error (non-breaking): {credit_error}")
                        # Continue with legacy processing if credit system fails
                
                # Railway-optimized concurrent batch processing
                import concurrent.futures
                
                async def concurrent_batch_processing():
                    """Async wrapper for concurrent batch processing"""
                    # Process resumes concurrently with limited workers
                    max_workers = min(4, len(resume_batch))  # Max 4 concurrent for Railway
                    
                    async def process_single_resume(resume_item, job_requirements, user_id):
                        """Process single resume in the batch"""
                        try:
                            return await self.ai_analyzer.analyze_resume(
                                resume_item.get('text', ''), 
                                job_requirements, 
                                user_id
                            )
                        except Exception as e:
                            logger.error(f"Error processing resume in batch: {e}")
                            return {
                                "error": str(e),
                                "overall_score": 0,
                                "processing_status": "failed"
                            }
                    
                    # Run concurrent processing
                    logger.info(f"Starting concurrent batch processing for {len(resume_batch)} resumes with {max_workers} workers")
                    
                    try:
                        # Create tasks for concurrent execution
                        tasks = [
                            process_single_resume(resume_item, job_requirements, user_id)
                            for resume_item in resume_batch
                        ]
                        
                        # Execute with timeout and gather results
                        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # Filter out exceptions and process results
                        processed_results = []
                        for i, result in enumerate(batch_results):
                            if isinstance(result, Exception):
                                logger.error(f"Batch processing exception for resume {i}: {result}")
                                processed_results.append({
                                    "error": str(result),
                                    "overall_score": 0,
                                    "processing_status": "exception",
                                    "batch_position": i + 1
                                })
                            else:
                                result['batch_position'] = i + 1
                                result['total_in_batch'] = len(resume_batch)
                                processed_results.append(result)
                        
                        # Sort by overall score for ranking
                        processed_results.sort(key=lambda x: x.get('overall_score', 0), reverse=True)
                        
                        logger.info(f"Concurrent batch processing completed for {len(processed_results)} resumes")
                        return processed_results
                        
                    except asyncio.TimeoutError:
                        logger.error("Batch processing timeout - falling back to sequential processing")
                        # Fallback to original sequential processing
                        return await self.ai_analyzer.analyze_resume_batch(
                            resume_batch, job_requirements, user_id
                        )
                    
                    except Exception as concurrent_error:
                        logger.error(f"Concurrent processing failed: {concurrent_error}, falling back to sequential")
                        # Fallback to original sequential processing
                        return await self.ai_analyzer.analyze_resume_batch(
                            resume_batch, job_requirements, user_id
                        )
                
                # Run the concurrent processing
                processed_results = asyncio.run(concurrent_batch_processing())
                
                # Store batch analysis results if needed
                for result in processed_results:
                    if result.get('original_id'):
                        try:
                            self.supabase.store_analysis_result(
                                result['original_id'], result, user_id
                            )
                        except Exception as e:
                            logger.warning(f"Failed to store batch result: {e}")
                
                # Enhanced response with credit info
                response_data = {
                    "success": True,
                    "batch_analysis": {
                        "total_resumes": len(processed_results),
                        "results": processed_results,
                        "analysis_type": "enhanced_concurrent_batch_with_ranking",
                        "scoring_calibrated": True,
                        "concurrent_processing": True
                    }
                }
                
                # Add credit status if available
                if self.credit_middleware:
                    try:
                        updated_status = self.credit_manager.check_user_credits(user_id)
                        response_data["credit_status"] = {
                            "credits_remaining": updated_status.credits_remaining,
                            "total_used": updated_status.total_used,
                            "credits_used_for_batch": credits_needed
                        }
                    except Exception:
                        pass  # Non-breaking
                
                return jsonify(response_data)
                
            except Exception as e:
                logger.error(f"Batch analysis error: {e}")
                return jsonify({"error": "Batch analysis failed"}), 500
                
        @self.app.route('/api/resumes', methods=['GET'])
        @self.auth.require_auth
        def get_user_resumes():
            """Get all resumes for current user"""
            try:
                user = self.auth.get_current_user()
                resumes = self.supabase.get_user_resumes(user['user_id'])
                
                return jsonify({
                    "success": True,
                    "resumes": resumes
                })
                
            except Exception as e:
                logger.error(f"Get resumes error: {e}")
                return jsonify({"error": "Failed to get resumes"}), 500
                
        @self.app.route('/api/resumes/<resume_id>', methods=['DELETE'])
        @self.auth.require_auth
        def delete_resume(resume_id):
            """Delete a specific resume"""
            try:
                user = self.auth.get_current_user()
                success = self.supabase.delete_user_resume(resume_id, user['user_id'])
                
                if success:
                    return jsonify({"success": True, "message": "Resume deleted"})
                else:
                    return jsonify({"error": "Resume not found"}), 404
                    
            except Exception as e:
                logger.error(f"Delete resume error: {e}")
                return jsonify({"error": "Delete failed"}), 500
                
        # HR Legal endpoints
        @self.app.route('/api/hr-legal/query', methods=['POST'])
        @self.auth.require_auth
        def hr_legal_query():
            """HR Legal consultation endpoint - Enhanced with B2B credit system"""
            try:
                user = self.auth.get_current_user()
                user_id = user['user_id']
                data = request.get_json()
                
                query_text = data.get('query_text', '')
                if not query_text:
                    return jsonify({"error": "Query text required"}), 400
                
                # B2B SaaS Enhancement: Credit-aware processing
                if self.credit_middleware:
                    try:
                        # Check credit status
                        credit_status = self.credit_manager.check_user_credits(user_id)
                        
                        # If no credits available, return monetization options
                        if not credit_status.can_process:
                            return jsonify({
                                "success": False,
                                "error": "insufficient_credits", 
                                "message": "Your trial credits have been exhausted",
                                "feature": "legal_query",
                                "credit_status": {
                                    "trial_credits": credit_status.trial_credits,
                                    "premium_credits": credit_status.premium_credits,
                                    "credits_remaining": credit_status.credits_remaining
                                },
                                "monetization_options": self.credit_middleware.offer_premium_options(credit_status)
                            }), 402  # Payment Required
                        
                        # Check if queue is busy - legal queries also use queue
                        queue_status = self.queue_manager.get_queue_status()
                        from queue_manager import QueueStatus
                        from credit_manager import ProcessingTier
                        
                        if (queue_status in [QueueStatus.BUSY, QueueStatus.OVERLOADED] and 
                            credit_status.processing_tier == ProcessingTier.FREE_TRIAL):
                            # Queue the legal query
                            request_data = {
                                'query_text': query_text
                            }
                            
                            request_id, queue_info = self.queue_manager.add_request(
                                str(user_id), "legal_query", request_data, credit_status.processing_tier
                            )
                            
                            return jsonify({
                                "success": False,
                                "status": "queued",
                                "message": "System is busy. Legal query queued for processing.",
                                "request_id": request_id,
                                "queue_info": queue_info,
                                "feature": "legal_query"
                            }), 202  # Accepted - will be processed later
                        
                        # Deduct credits for immediate processing
                        if not self.credit_manager.deduct_credits(user_id, 1, "legal_query", credit_status.processing_tier):
                            return jsonify({
                                "success": False,
                                "error": "credit_deduction_failed",
                                "message": "Failed to deduct credits for legal query"
                            }), 402
                        
                    except Exception as credit_error:
                        logger.error(f"Credit system error (non-breaking): {credit_error}")
                        # Continue with legacy processing if credit system fails
                    
                # Original processing logic (unchanged for backward compatibility)
                legal_response = self.ai_analyzer.process_legal_query(
                    query_text, user_id
                )
                
                # Store legal query
                self.supabase.store_legal_query(
                    user_id, query_text, legal_response
                )
                
                # Enhanced response with credit info
                response_data = {
                    "success": True,
                    "response": legal_response
                }
                
                # Add credit status if available
                if self.credit_middleware:
                    try:
                        updated_status = self.credit_manager.check_user_credits(user_id)
                        response_data["credit_status"] = {
                            "credits_remaining": updated_status.credits_remaining,
                            "total_used": updated_status.total_used
                        }
                    except Exception:
                        pass  # Non-breaking
                
                return jsonify(response_data)
                
            except Exception as e:
                logger.error(f"Legal query error: {e}")
                return jsonify({"error": "Legal query failed"}), 500
        
        # System status endpoints
        @self.app.route('/api/system/status', methods=['GET'])
        @self.auth.require_auth
        def system_status():
            """Get comprehensive system status including enhanced AI components"""
            try:
                # Get enhanced system status
                enhanced_status = self.ai_analyzer.get_enhanced_system_status()
                
                # Get basic system health
                basic_health = {
                    "supabase": self.supabase.health_check(),
                    "storage": self.storage.health_check(),
                    "ai_basic": self.ai_analyzer.health_check()
                }
                
                return jsonify({
                    "success": True,
                    "system_status": {
                        "basic_health": basic_health,
                        "enhanced_ai_status": enhanced_status,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
                
            except Exception as e:
                logger.error(f"System status error: {e}")
                return jsonify({"error": "Failed to get system status"}), 500
                
        # Admin endpoints
        @self.app.route('/api/admin/stats', methods=['GET'])
        @self.auth.require_admin
        def admin_stats():
            """Railway-optimized admin dashboard statistics with caching"""
            try:
                # Check cache first (5-minute TTL for admin stats)
                cache_key = "admin_stats_dashboard"
                cached_result = self._get_response_cache(cache_key, ttl_seconds=300)
                
                if cached_result:
                    logger.debug("Returning cached admin stats")
                    return jsonify(cached_result)
                
                # Get fresh stats
                stats = self.supabase.get_admin_stats()
                
                response_data = {
                    "success": True,
                    "stats": stats,
                    "cached": False,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Cache the result
                self._set_response_cache(cache_key, response_data)
                
                return jsonify(response_data)
                
            except Exception as e:
                logger.error(f"Admin stats error: {e}")
                return jsonify({"error": "Failed to get stats"}), 500
                
        @self.app.route('/api/admin/users', methods=['GET'])
        @self.auth.require_admin
        def admin_users():
            """Get all users for admin"""
            try:
                users = self.supabase.get_all_users()
                return jsonify({
                    "success": True,
                    "users": users
                })
            except Exception as e:
                logger.error(f"Admin users error: {e}")
                return jsonify({"error": "Failed to get users"}), 500
        
        # Credit Management Endpoints (B2B SaaS)
        @self.app.route('/api/credits/status', methods=['GET'])
        @self.auth.require_auth
        def get_credit_status():
            """Get current user's credit status"""
            try:
                if not self.credit_manager:
                    return jsonify({"error": "Credit system not available"}), 503
                
                user = self.auth.get_current_user()
                user_id = user['user_id']
                
                credit_status = self.credit_manager.check_user_credits(user_id)
                
                return jsonify({
                    "success": True,
                    "credit_status": {
                        "trial_credits": credit_status.trial_credits,
                        "premium_credits": credit_status.premium_credits,
                        "total_used": credit_status.total_used,
                        "credits_remaining": credit_status.credits_remaining,
                        "processing_tier": credit_status.processing_tier.value,
                        "can_process": credit_status.can_process,
                        "lead_score": credit_status.lead_score
                    },
                    "usage_pattern": credit_status.usage_pattern
                })
                
            except Exception as e:
                logger.error(f"Credit status error: {e}")
                return jsonify({"error": "Failed to get credit status"}), 500
        
        @self.app.route('/api/admin/sales-intelligence', methods=['GET'])
        @self.auth.require_admin
        def get_sales_intelligence():
            """Railway-optimized sales intelligence with caching and fallback"""
            try:
                # Check if credit manager is available
                if not self.credit_manager:
                    logger.warning("Credit manager not available for sales intelligence")
                    # Return mock data for development/testing
                    return jsonify({
                        "success": True,
                        "message": "Sales intelligence service temporarily unavailable",
                        "qualified_leads": [],
                        "total_leads": 0,
                        "service_status": "unavailable",
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Generate cache key based on request parameters
                limit = request.args.get('limit', 50, type=int)
                cache_key = f"sales_intelligence_{limit}"
                
                # Check cache first (3-minute TTL for sales data)
                cached_result = self._get_response_cache(cache_key, ttl_seconds=180)
                
                if cached_result:
                    logger.debug("Returning cached sales intelligence")
                    return jsonify(cached_result)
                
                # Get fresh sales intelligence data with error handling
                try:
                    leads = self.credit_manager.get_sales_intelligence(limit)
                except Exception as sales_error:
                    logger.error(f"Sales intelligence data fetch error: {sales_error}")
                    leads = []
                
                response_data = {
                    "success": True,
                    "qualified_leads": leads,
                    "total_leads": len(leads),
                    "cached": False,
                    "service_status": "operational",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Cache the result
                self._set_response_cache(cache_key, response_data)
                
                return jsonify(response_data)
                
            except Exception as e:
                logger.error(f"Sales intelligence error: {e}")
                return jsonify({
                    "success": False,
                    "error": "Failed to get sales intelligence",
                    "message": "Sales intelligence service encountered an error",
                    "service_status": "error",
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/admin/queue-stats', methods=['GET'])
        @self.auth.require_admin
        def get_queue_stats():
            """Railway-optimized queue statistics with smart caching"""
            try:
                if not self.queue_manager:
                    return jsonify({"error": "Queue system not available"}), 503
                
                # Check for cached result (2-minute TTL for admin stats)
                cache_key = "admin_queue_stats_cache"
                cached_result = self._get_cached_result(cache_key, ttl_seconds=120)
                
                if cached_result:
                    logger.debug("Returning cached admin queue stats")
                    return jsonify(cached_result)
                
                # Get detail level from query parameter
                detail_level = request.args.get('detail', 'standard')  # minimal, standard, full
                
                # Get optimized stats based on detail level
                if detail_level == 'minimal':
                    # Ultra-fast minimal stats
                    with self.queue_manager._queue_lock:
                        stats = {
                            "queue_status": self.queue_manager.get_queue_status().value,
                            "pending_requests": len(self.queue_manager._pending_queue),
                            "processing_requests": len(self.queue_manager._processing_requests),
                            "timestamp": datetime.now().isoformat(),
                            "detail_level": "minimal"
                        }
                else:
                    # Standard or full stats with optimizations
                    stats = self.queue_manager.get_queue_stats()
                    stats["detail_level"] = detail_level
                    
                    # Add extra details for full level
                    if detail_level == 'full':
                        try:
                            # Add system resource info
                            stats["system_resources"] = {
                                "memory_percent": psutil.virtual_memory().percent,
                                "cpu_percent": psutil.cpu_percent(interval=0.1),
                                "active_threads": self.queue_manager.max_concurrent
                            }
                        except Exception as e:
                            stats["system_resources_error"] = str(e)
                
                response_data = {
                    "success": True,
                    "queue_stats": stats,
                    "cached": False
                }
                
                # Cache the result
                self._set_cached_result(cache_key, response_data)
                
                return jsonify(response_data)
                
            except Exception as e:
                logger.error(f"Queue stats error: {e}")
                return jsonify({"error": "Failed to get queue stats"}), 500
                
        @self.app.route('/api/users/<int:user_id>/usage-stats', methods=['GET'])
        @self.auth.require_admin
        def get_user_usage_stats(user_id):
            """Get detailed usage statistics for a specific user"""
            try:
                if not self.credit_manager:
                    return jsonify({"error": "Credit system not available"}), 503
                
                stats = self.credit_manager.get_user_usage_stats(user_id)
                
                return jsonify({
                    "success": True,
                    "user_id": user_id,
                    "usage_stats": stats
                })
                
            except Exception as e:
                logger.error(f"User usage stats error: {e}")
                return jsonify({"error": "Failed to get user usage stats"}), 500
        
        # ===== PHASE 3: SALES INTELLIGENCE & ADVANCED ANALYTICS ENDPOINTS =====
        
        @self.app.route('/api/admin/advanced-analytics', methods=['GET'])
        @self.auth.require_admin
        def get_advanced_analytics():
            """Enhanced business intelligence and analytics with Railway optimization and fallback"""
            try:
                # Check if analytics engine is available
                if not self.analytics_engine:
                    logger.warning("Analytics engine not available for advanced analytics")
                    # Return mock analytics data for development/testing
                    return jsonify({
                        "success": True,
                        "message": "Advanced analytics service temporarily unavailable",
                        "analytics": {
                            "funnel_analysis": {
                                "total_visitors": 0,
                                "signups": 0,
                                "active_users": 0,
                                "conversion_rate": 0
                            },
                            "revenue_analytics": {
                                "total_revenue": 0,
                                "monthly_recurring_revenue": 0,
                                "average_revenue_per_user": 0
                            },
                            "cohort_analysis": [],
                            "top_prospects": []
                        },
                        "service_status": "unavailable",
                        "cached": False,
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Check for cached results first (5-minute TTL for Railway efficiency)
                cache_key = "advanced_analytics_cache"
                cached_analytics = getattr(self, '_analytics_cache', {})
                
                if (cache_key in cached_analytics and 
                    (datetime.now() - cached_analytics[cache_key]['cached_at']).seconds < 300):
                    logger.info("Returning cached advanced analytics results")
                    return jsonify({
                        "success": True,
                        "analytics": cached_analytics[cache_key]['data'],
                        "cached": True,
                        "cache_age_seconds": (datetime.now() - cached_analytics[cache_key]['cached_at']).seconds
                    })
                
                # If no cache, try to get lightweight analytics first with comprehensive error handling
                try:
                    logger.info("Computing fresh analytics for Railway...")
                    
                    # Get lighter versions of analytics with timeout protection
                    try:
                        funnel_analysis = self.analytics_engine.get_conversion_funnel_analysis()
                    except Exception as e:
                        logger.warning(f"Funnel analysis failed: {e}")
                        funnel_analysis = {"status": "unavailable", "reason": str(e)}
                    
                    # Skip heavy operations if they're taking too long
                    try:
                        revenue_analytics = self.analytics_engine.get_revenue_analytics()
                    except Exception as e:
                        logger.warning(f"Revenue analytics skipped: {e}")
                        revenue_analytics = {"status": "unavailable", "reason": "timeout_protection"}
                    
                    try:
                        # Limit cohort analysis for Railway performance
                        cohort_analysis = self.analytics_engine.analyze_cohort("weekly")[:3]  # Only last 3 weeks
                    except Exception as e:
                        logger.warning(f"Cohort analysis skipped: {e}")
                        cohort_analysis = [{"status": "unavailable", "reason": "timeout_protection"}]
                    
                    try:
                        # Reduce top prospects for Railway performance
                        top_prospects = self.analytics_engine.get_top_prospects(10)[:5]  # Only top 5
                    except Exception as e:
                        logger.warning(f"Top prospects skipped: {e}")
                        top_prospects = [{"status": "unavailable", "reason": "timeout_protection"}]
                    
                    analytics_data = {
                        "conversion_funnel": funnel_analysis,
                        "revenue_metrics": revenue_analytics,
                        "cohort_analysis": cohort_analysis,
                        "top_prospects": top_prospects,
                        "generated_at": datetime.now().isoformat(),
                        "service_status": "operational",
                        "railway_optimized": True
                    }
                    
                    # Cache the results for Railway efficiency
                    if not hasattr(self, '_analytics_cache'):
                        self._analytics_cache = {}
                    
                    self._analytics_cache[cache_key] = {
                        'data': analytics_data,
                        'cached_at': datetime.now()
                    }
                    
                    return jsonify({
                        "success": True,
                        "analytics": analytics_data,
                        "cached": False
                    })
                    
                except Exception as computation_error:
                    logger.error(f"Analytics computation failed: {computation_error}")
                    # Return basic analytics if heavy computation fails
                    return jsonify({
                        "success": True,
                        "analytics": {
                            "status": "limited_mode",
                            "message": "Heavy analytics unavailable, using basic metrics",
                            "basic_stats": {
                                "analytics_engine_status": "degraded",
                                "generated_at": datetime.now().isoformat()
                            }
                        },
                        "service_status": "degraded",
                        "railway_optimized": True
                    })
                
            except Exception as e:
                logger.error(f"Advanced analytics error: {e}")
                return jsonify({
                    "success": False,
                    "error": "Failed to get advanced analytics",
                    "message": "Advanced analytics service encountered an error",
                    "service_status": "error",
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/admin/hot-leads', methods=['GET'])
        @self.auth.require_admin
        def get_hot_leads():
            """Real-time qualified prospects requiring immediate attention with Railway optimization"""
            try:
                if not self.sales_intelligence:
                    return jsonify({"error": "Sales intelligence not available"}), 503
                
                # Check cache first (2-minute TTL for hot leads)
                cached_data = self._get_cached_result("hot_leads", 120)
                if cached_data:
                    return jsonify({
                        "success": True,
                        "hot_leads": cached_data,
                        "cached": True
                    })
                
                try:
                    limit = min(request.args.get('limit', 10, type=int), 10)  # Cap at 10 for Railway
                    hot_leads = self.sales_intelligence.get_hot_leads(limit)
                    
                    # Convert to JSON-serializable format (Railway optimized)
                    leads_data = []
                    for lead in hot_leads[:5]:  # Only top 5 for Railway performance
                        leads_data.append({
                            "user_id": lead.user_id,
                            "email": lead.email,
                            "name": lead.name,
                            "company": getattr(lead, 'company', 'N/A'),
                            "lead_score": lead.lead_score,
                            "conversion_probability": lead.conversion_probability,
                            "priority": lead.priority.value if hasattr(lead.priority, 'value') else str(lead.priority),
                            "recommended_action": lead.recommended_action.value if hasattr(lead.recommended_action, 'value') else str(lead.recommended_action),
                            "revenue_potential": getattr(lead, 'revenue_potential', 0),
                            "last_activity": getattr(lead, 'last_activity', datetime.now().isoformat()),
                            "railway_optimized": True
                        })
                    
                    self._set_cached_result("hot_leads", leads_data)
                    
                    return jsonify({
                        "success": True,
                        "hot_leads": leads_data,
                        "total_leads": len(leads_data),
                        "generated_at": datetime.now().isoformat(),
                        "cached": False
                    })
                
                except Exception as e:
                    logger.warning(f"Hot leads computation failed: {e}")
                    return jsonify({
                        "success": True,
                        "hot_leads": [],
                        "message": "Hot leads computation unavailable",
                        "railway_optimized": True
                    })
                
            except Exception as e:
                logger.error(f"Hot leads error: {e}")
                return jsonify({"error": "Failed to get hot leads"}), 500
        
        @self.app.route('/api/admin/conversion-predictions', methods=['GET'])
        @self.auth.require_admin
        def get_conversion_predictions():
            """ML-based conversion predictions and lead scoring with Railway optimization"""
            try:
                if not self.analytics_engine:
                    return jsonify({"error": "Analytics engine not available"}), 503
                
                # Check cache first (5-minute TTL)
                cached_data = self._get_cached_result("conversion_predictions", 300)
                if cached_data:
                    return jsonify({
                        "success": True,
                        "predictions": cached_data,
                        "cached": True
                    })
                
                try:
                    # Get limited prospects for Railway performance
                    prospects = self.analytics_engine.get_top_prospects(20)  # Reduced from 50
                    
                    # Segment by conversion probability (Railway optimized)
                    high_probability = [p for p in prospects if p.get("conversion_probability", 0) >= 0.7][:3]
                    medium_probability = [p for p in prospects if 0.4 <= p.get("conversion_probability", 0) < 0.7][:3]
                    low_probability = [p for p in prospects if p.get("conversion_probability", 0) < 0.4][:2]
                    
                    predictions_data = {
                        "high_probability_conversions": high_probability,
                        "medium_probability_conversions": medium_probability,
                        "low_probability_conversions": low_probability,
                        "total_analyzed": len(prospects),
                        "railway_optimized": True
                    }
                    
                    self._set_cached_result("conversion_predictions", predictions_data)
                    
                    return jsonify({
                        "success": True,
                        "predictions": predictions_data,
                        "generated_at": datetime.now().isoformat(),
                        "cached": False
                    })
                
                except Exception as e:
                    logger.warning(f"Conversion predictions computation failed: {e}")
                    return jsonify({
                        "success": True,
                        "predictions": {
                            "status": "unavailable",
                            "reason": "computation_timeout",
                            "railway_optimized": True
                        }
                    })
                
            except Exception as e:
                logger.error(f"Conversion predictions error: {e}")
                return jsonify({"error": "Failed to get conversion predictions"}), 500
        
        @self.app.route('/api/admin/sales-pipeline', methods=['GET'])
        @self.auth.require_admin
        def get_sales_pipeline():
            """Sales pipeline overview with key metrics"""
            try:
                if not self.sales_intelligence:
                    return jsonify({"error": "Sales intelligence not available"}), 503
                
                pipeline_overview = self.sales_intelligence.get_sales_pipeline_overview()
                
                return jsonify({
                    "success": True,
                    "pipeline": pipeline_overview,
                    "generated_at": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Sales pipeline error: {e}")
                return jsonify({"error": "Failed to get sales pipeline"}), 500
        
        @self.app.route('/api/admin/trigger-email-sequence', methods=['POST'])
        @self.auth.require_admin
        def trigger_email_sequence():
            """Manually trigger email campaign for specific user"""
            try:
                if not self.email_automation:
                    return jsonify({"error": "Email automation not available"}), 503
                
                data = request.get_json()
                user_id = data.get('user_id')
                template_name = data.get('template_name')
                admin_user = self.auth.get_current_user().get('username', 'admin')
                
                if not user_id or not template_name:
                    return jsonify({"error": "user_id and template_name required"}), 400
                
                success = self.email_automation.manually_trigger_campaign(
                    user_id, template_name, admin_user
                )
                
                if success:
                    return jsonify({
                        "success": True,
                        "message": f"Email campaign {template_name} triggered for user {user_id}"
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "Failed to trigger email campaign"
                    }), 500
                
            except Exception as e:
                logger.error(f"Email trigger error: {e}")
                return jsonify({"error": "Failed to trigger email sequence"}), 500
        
        @self.app.route('/api/admin/lead-recommendations/<int:user_id>', methods=['GET'])
        @self.auth.require_admin
        def get_lead_recommendations(user_id):
            """Get specific sales recommendations for a lead"""
            try:
                if not self.sales_intelligence:
                    return jsonify({"error": "Sales intelligence not available"}), 503
                
                recommendations = self.sales_intelligence.get_lead_recommendations(user_id)
                
                return jsonify({
                    "success": True,
                    "user_id": user_id,
                    "recommendations": recommendations,
                    "generated_at": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Lead recommendations error: {e}")
                return jsonify({"error": "Failed to get lead recommendations"}), 500
        
        @self.app.route('/api/admin/email-analytics', methods=['GET'])
        @self.auth.require_admin
        def get_email_analytics():
            """Get email campaign performance analytics with Railway optimization"""
            try:
                if not self.email_automation:
                    return jsonify({"error": "Email automation not available"}), 503
                
                # Check cache first (5-minute TTL)
                cached_data = self._get_cached_result("email_analytics", 300)
                if cached_data:
                    return jsonify({
                        "success": True,
                        "email_analytics": cached_data,
                        "cached": True
                    })
                
                try:
                    analytics = self.email_automation.get_email_analytics()
                    self._set_cached_result("email_analytics", analytics)
                    
                    return jsonify({
                        "success": True,
                        "email_analytics": analytics,
                        "generated_at": datetime.now().isoformat(),
                        "cached": False
                    })
                except Exception as e:
                    # Return basic status if analytics fail
                    logger.warning(f"Email analytics computation failed: {e}")
                    return jsonify({
                        "success": True,
                        "email_analytics": {
                            "status": "unavailable",
                            "reason": "computation_timeout",
                            "railway_optimized": True
                        }
                    })
                
            except Exception as e:
                logger.error(f"Email analytics error: {e}")
                return jsonify({"error": "Failed to get email analytics"}), 500
        
        @self.app.route('/api/admin/update-lead-status', methods=['POST'])
        @self.auth.require_admin
        def update_lead_status():
            """Update lead status and add sales notes"""
            try:
                if not self.sales_intelligence:
                    return jsonify({"error": "Sales intelligence not available"}), 503
                
                data = request.get_json()
                user_id = data.get('user_id')
                status = data.get('status')
                notes = data.get('notes', '')
                sales_rep = self.auth.get_current_user().get('username', 'admin')
                
                if not user_id or not status:
                    return jsonify({"error": "user_id and status required"}), 400
                
                success = self.sales_intelligence.update_lead_status(
                    user_id, status, notes, sales_rep
                )
                
                if success:
                    return jsonify({
                        "success": True,
                        "message": f"Lead status updated for user {user_id}"
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "Failed to update lead status"
                    }), 500
                
            except Exception as e:
                logger.error(f"Update lead status error: {e}")
                return jsonify({"error": "Failed to update lead status"}), 500
        
        # Demo & Client Experience APIs
        @self.app.route('/api/demo/usage-showcase', methods=['GET'])
        @self.auth.require_auth
        def demo_usage_showcase():
            """Real-time usage statistics for presentations"""
            try:
                user = self.auth.get_current_user()
                user_id = user['user_id']
                
                if not self.analytics_engine:
                    # Fallback to basic stats
                    credit_status = self.credit_manager.check_user_credits(user_id) if self.credit_manager else None
                    return jsonify({
                        "success": True,
                        "showcase": {
                            "credits_used": credit_status.total_used if credit_status else 0,
                            "credits_remaining": credit_status.credits_remaining if credit_status else 0,
                            "features_used": 1,
                            "time_saved_hours": 2.5
                        }
                    })
                
                # Get comprehensive analytics for showcase
                analytics = self.analytics_engine.analyze_user_comprehensive(user_id)
                
                # Calculate showcase metrics
                time_saved = analytics.credits_used * 15  # 15 minutes per resume
                cost_savings = time_saved * 500  # ₹500 per hour saved
                
                showcase = {
                    "usage_summary": {
                        "credits_used": analytics.credits_used,
                        "credits_remaining": analytics.credits_remaining,
                        "features_adopted": len(analytics.feature_usage),
                        "days_active": analytics.days_since_signup
                    },
                    "efficiency_metrics": {
                        "time_saved_minutes": time_saved,
                        "time_saved_hours": round(time_saved / 60, 1),
                        "cost_savings_inr": cost_savings,
                        "productivity_increase": "300%"
                    },
                    "quality_metrics": {
                        "analysis_accuracy": "95%",
                        "decision_confidence": "High",
                        "candidate_match_rate": "87%"
                    },
                    "business_impact": {
                        "hiring_speed_improvement": "2.5x faster",
                        "bias_reduction": "40% reduction",
                        "consistency_improvement": "90% more consistent"
                    }
                }
                
                return jsonify({
                    "success": True,
                    "showcase": showcase,
                    "generated_at": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Demo showcase error: {e}")
                return jsonify({"error": "Failed to get usage showcase"}), 500
        
        @self.app.route('/api/demo/roi-calculator', methods=['POST'])
        @self.auth.require_auth
        def demo_roi_calculator():
            """ROI calculator for client value proposition"""
            try:
                data = request.get_json()
                
                # Input parameters
                monthly_hires = data.get('monthly_hires', 10)
                avg_salary = data.get('avg_salary', 500000)  # Annual salary
                time_per_resume = data.get('time_per_resume', 30)  # Minutes
                hr_hourly_rate = data.get('hr_hourly_rate', 1000)  # ₹1000/hour
                
                # ROI calculations
                monthly_resumes = monthly_hires * 20  # 20 resumes per hire
                monthly_time_saved = monthly_resumes * (time_per_resume - 2)  # 2 minutes with AI
                monthly_cost_savings = (monthly_time_saved / 60) * hr_hourly_rate
                
                # Quality improvements
                bad_hire_cost = avg_salary * 0.3  # 30% of annual salary
                quality_improvement = 0.25  # 25% reduction in bad hires
                quality_savings = monthly_hires * bad_hire_cost * quality_improvement / 12
                
                total_monthly_savings = monthly_cost_savings + quality_savings
                annual_savings = total_monthly_savings * 12
                
                # Platform cost (estimated)
                monthly_platform_cost = 25000  # ₹25k/month enterprise
                annual_platform_cost = monthly_platform_cost * 12
                
                # ROI calculation
                net_savings = annual_savings - annual_platform_cost
                roi_percentage = (net_savings / annual_platform_cost) * 100
                
                roi_data = {
                    "input_parameters": {
                        "monthly_hires": monthly_hires,
                        "avg_salary": avg_salary,
                        "time_per_resume": time_per_resume,
                        "hr_hourly_rate": hr_hourly_rate
                    },
                    "efficiency_savings": {
                        "monthly_time_saved_hours": round(monthly_time_saved / 60, 1),
                        "monthly_cost_savings": round(monthly_cost_savings),
                        "annual_efficiency_savings": round(monthly_cost_savings * 12)
                    },
                    "quality_savings": {
                        "bad_hire_cost": round(bad_hire_cost),
                        "quality_improvement_percentage": quality_improvement * 100,
                        "monthly_quality_savings": round(quality_savings),
                        "annual_quality_savings": round(quality_savings * 12)
                    },
                    "total_roi": {
                        "annual_total_savings": round(annual_savings),
                        "annual_platform_cost": annual_platform_cost,
                        "net_annual_savings": round(net_savings),
                        "roi_percentage": round(roi_percentage, 1),
                        "payback_period_months": round(annual_platform_cost / total_monthly_savings, 1)
                    }
                }
                
                return jsonify({
                    "success": True,
                    "roi_analysis": roi_data,
                    "generated_at": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"ROI calculator error: {e}")
                return jsonify({"error": "Failed to calculate ROI"}), 500
        
        # Automation & Optimization APIs
        @self.app.route('/api/automation/process-email-triggers', methods=['POST'])
        @self.auth.require_auth  # This will be called by system, but keeping auth for security
        def process_email_triggers():
            """Process automated email triggers based on user behavior"""
            try:
                if not self.email_automation:
                    return jsonify({"error": "Email automation not available"}), 503
                
                user = self.auth.get_current_user()
                user_id = user['user_id']
                
                # Get recent usage data for trigger evaluation
                usage_data = self.credit_manager.get_user_usage_stats(user_id) if self.credit_manager else {}
                
                # Check and trigger campaigns
                self.email_automation.check_and_trigger_campaigns(user_id, usage_data)
                
                return jsonify({
                    "success": True,
                    "message": "Email triggers processed successfully"
                })
                
            except Exception as e:
                logger.error(f"Email triggers processing error: {e}")
                return jsonify({"error": "Failed to process email triggers"}), 500
                
    def is_allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in {'pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg'}
               
    def process_resume_file(self, file, user):
        """Enhanced resume processing with automatic AI analysis (matches admin upload)"""
        try:
            import os
            import uuid
            import json
            import hashlib
            import asyncio
            from werkzeug.utils import secure_filename
            from datetime import datetime
            
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(os.getcwd(), 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_dir, unique_filename)
            file.save(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Extract text from file
            resume_text = self.extract_text_from_file(file_path)
            
            # Clean up temporary file
            try:
                os.remove(file_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temporary file: {cleanup_error}")
            
            # Validate database connection
            if not self.db_manager:
                logger.error("Database manager not initialized")
                return {
                    "filename": filename,
                    "status": "error",
                    "error": "Database manager not available"
                }
            
            # Generate file hash for duplicate detection
            file_hash = hashlib.md5(resume_text.encode()).hexdigest()
            
            # Get file extension
            file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
            
            # Create user profile if needed (for hybrid storage)
            user_id = user['user_id']
            user_email = user.get('email', 'user@system.local')
            user_name = user.get('name', 'User')
            
            # Step 1: Create placeholder resume record with 'processing' status
            placeholder_content = json.dumps({
                'filename': filename,
                'text': resume_text[:1000] + '...' if len(resume_text) > 1000 else resume_text,
                'user_upload': True,
                'uploaded_by': user.get('email', 'user'),
                'upload_timestamp': datetime.utcnow().isoformat(),
                'status': 'awaiting_ai_processing'
            })
            
            # Create comprehensive resume record using hybrid database approach
            resume_uuid = str(uuid.uuid4())
            
            resume_data = {
                'id': resume_uuid,
                'user_id': user_id,
                'filename': filename,
                'file_hash': file_hash,
                'file_size': file_size,
                'file_type': file_extension,
                'compressed_content': placeholder_content,
                'raw_text': resume_text,
                'upload_date': datetime.utcnow().isoformat(),
                'processing_status': 'processing',
                'processing_started_at': datetime.utcnow().isoformat(),
                'candidate_name': '',
                'candidate_email': '',
                'candidate_phone': '',
                'skills': [],
                'experience_years': 0,
                'education_level': '',
                'overall_score': 0,
                'technical_score': 0,
                'experience_score': 0,
                'education_score': 0,
                'role_fit_score': 0,
                'ai_feedback': 'Processing with AI...',
                'ai_model_used': 'pending',
                'ai_processing_time': 0,
                'job_titles': [],
                'companies': [],
                'programming_languages': [],
                'certifications': [],
                'tags': [],
                'category': 'general',
                'priority': 0,
                'is_shortlisted': False,
                'is_archived': False,
                'notes': f'Uploaded by user: {user.get("email", "user")} - AI processing in progress',
                'analysis_result': None,
                'similarity_score': None,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Store resume using hybrid database approach
            logger.info(f"Storing user resume using hybrid database approach - Data fields: {len(resume_data)}")
            
            resume_id = None
            try:
                # Use the database manager's hybrid approach
                store_result = self.db_manager.store_resume_hybrid(resume_data)
                
                if store_result and store_result.get('id'):
                    resume_id = store_result['id']
                    logger.info(f"Hybrid database store SUCCESS - Resume ID: {resume_id}")
                else:
                    # Fallback: try direct Supabase insertion
                    logger.warning("Hybrid store returned no ID, falling back to direct Supabase")
                    supabase_data = resume_data.copy()
                    supabase_data.pop('id', None)  # Remove UUID for Supabase auto-generation
                    response = self.db_manager.supabase.admin_client.table('resumes').insert(supabase_data).execute()
                    if response.data:
                        resume_id = response.data[0]['id']
                        logger.info(f"Supabase fallback SUCCESS - Resume ID: {resume_id}")
                    else:
                        raise Exception("Both hybrid and Supabase direct insertion failed")
                        
            except Exception as db_error:
                logger.error(f"Database storage error: {db_error}")
                return {
                    "filename": filename,
                    "status": "error",
                    "error": f"Database storage failed: {str(db_error)}"
                }
            
            if resume_id:
                # Step 2: Start enhanced background AI processing with comprehensive error handling
                try:
                    logger.info(f"Starting enhanced unified AI processing for user resume {resume_id}")
                    
                    # Create task with timeout and error recovery
                    async def safe_ai_processing():
                        try:
                            await self._process_user_resume_unified_ai(resume_id, resume_text, filename, user_id)
                        except asyncio.TimeoutError:
                            logger.error(f"AI processing timeout for resume {resume_id}")
                            # Update status to timeout
                            if self.railway_db:
                                self.railway_db.execute_write(
                                    "UPDATE resumes SET processing_status = %s, processing_error = %s, processing_completed_at = NOW() WHERE id = %s",
                                    ('timeout', 'AI processing timed out after 15 minutes', resume_id)
                                )
                            # Emit timeout notification
                            if hasattr(self, 'emit_user_notification'):
                                self.emit_user_notification(user_id, 'error', 
                                    f"AI processing timed out for {filename}. Please try uploading again.")
                        except Exception as ai_error:
                            logger.error(f"AI processing error for resume {resume_id}: {ai_error}")
                            # Update status to failed
                            if self.railway_db:
                                self.railway_db.execute_write(
                                    "UPDATE resumes SET processing_status = %s, processing_error = %s, processing_completed_at = NOW() WHERE id = %s",
                                    ('failed', str(ai_error), resume_id)
                                )
                            # Emit error notification
                            if hasattr(self, 'emit_user_notification'):
                                self.emit_user_notification(user_id, 'error', 
                                    f"AI processing failed for {filename}: {str(ai_error)}")
                    
                    # Start background task with proper async handling
                    background_task = asyncio.create_task(safe_ai_processing())
                    
                    # Don't wait for completion - return immediately
                    logger.info(f"Started enhanced AI processing for user resume {resume_id} in background")
                    
                except Exception as ai_start_error:
                    logger.error(f"Failed to start AI processing: {ai_start_error}")
                    # Update resume status to indicate AI processing failed to start
                    try:
                        if self.railway_db:
                            self.railway_db.execute_write(
                                "UPDATE resumes SET processing_status = %s, processing_error = %s, processing_completed_at = NOW() WHERE id = %s",
                                ('failed', f'AI processing failed to start: {str(ai_start_error)}', resume_id)
                            )
                        elif self.db_manager:
                            self.db_manager.supabase.admin_client.table('resumes').update({
                                'processing_status': 'failed',
                                'processing_error': f'AI processing failed to start: {str(ai_start_error)}',
                                'processing_completed_at': datetime.utcnow().isoformat()
                            }).eq('id', resume_id).execute()
                    except Exception as update_error:
                        logger.error(f"Failed to update failed status: {update_error}")
                    
                    # Emit immediate error notification
                    if hasattr(self, 'emit_user_notification'):
                        self.emit_user_notification(user_id, 'error', 
                            f"Failed to start AI analysis for {filename}. Please try again.")
                    
                    return {
                        "filename": filename,
                        "status": "error",
                        "error": f"Failed to start AI processing: {str(ai_start_error)}",
                        "resume_id": resume_id,
                        "retry_recommended": True
                    }
                    
                
                # Step 3: Return immediate success response (matches admin format)
                return {
                    "resume_id": resume_id,
                    "filename": filename,
                    "status": "uploaded",
                    "processing_status": "processing",
                    "ai_processing": True,
                    "user_upload": True,
                    "file_size": file_size,
                    "text_length": len(resume_text),
                    "message": "Resume uploaded successfully and AI processing started",
                    "note": "AI analysis is running in background. Check back in a few minutes for complete analysis."
                }
            else:
                return {
                    "filename": filename,
                    "status": "error",
                    "error": "Failed to store resume in database"
                }
            
        except Exception as e:
            logger.error(f"Enhanced file processing error: {e}")
            return {
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            }
            
    def extract_text_from_file(self, file_path):
        """Extract text from uploaded file"""
        try:
            file_ext = file_path.lower().split('.')[-1]
            
            if file_ext == 'pdf':
                return self.extract_text_from_pdf(file_path)
            elif file_ext in ['docx', 'doc']:
                return self.extract_text_from_docx(file_path)
            elif file_ext in ['png', 'jpg', 'jpeg']:
                return self.extract_text_from_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
                
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            return ""
            
    def extract_text_from_pdf(self, file_path):
        """Extract text from PDF file"""
        text = ""
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
        return text
        
    def extract_text_from_docx(self, file_path):
        """Extract text from DOCX file"""
        text = ""
        try:
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
        return text
        
    def extract_text_from_image(self, file_path):
        """Extract text from image using OCR"""
        text = ""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
        return text
    
    async def _process_user_resume_ai_fallback(self, resume_id: str, resume_text: str, filename: str, user_id: str):
        """
        Fallback AI processing for user resumes when admin processing isn't available
        Simplified version of the admin AI processing
        """
        try:
            logger.info(f"Starting fallback AI processing for user resume {resume_id}")
            
            # Import AI processor and database extraction function
            from ai_processor import get_processor, extract_resume_data_for_database
            from config import Config
            
            # Initialize AI processor
            config = Config()
            ai_processor = get_processor()
            
            # Create default job requirements for general analysis
            default_job_requirements = json.loads(config.DEFAULT_JOB_REQUIREMENTS)
            
            # Run AI analysis
            start_time = datetime.utcnow()
            
            try:
                logger.info(f"Running fallback AI analysis for resume {resume_id}")
                
                # Run AI analysis
                ai_result = await ai_processor.analyze_resume(
                    resume_text, 
                    default_job_requirements, 
                    user_id
                )
                
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000  # milliseconds
                logger.info(f"Fallback AI analysis completed for resume {resume_id} in {processing_time:.0f}ms")
                
            except Exception as ai_error:
                logger.error(f"Fallback AI processing error for resume {resume_id}: {ai_error}")
                ai_result = {
                    'error': f'AI processing failed: {str(ai_error)}',
                    'overall_score': 0,
                    'processing_tier': 'error'
                }
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Extract structured data for database using new response processor
            try:
                logger.info(f"Processing AI response using new response processor for resume {resume_id}")
                
                # Use the new AI response processor
                processed_response = process_ai_response(ai_result, resume_id, user_id)
                
                # Extract railway-formatted data for PostgreSQL
                database_record = processed_response['railway_format']
                supabase_record = processed_response['supabase_format']
                
                # Add processing metadata
                database_record['ai_processing_time'] = int(processing_time)
                database_record['processing_completed_at'] = datetime.utcnow().isoformat()
                
                # Set final status based on AI result
                if 'error' in ai_result:
                    database_record['processing_status'] = 'failed'
                    database_record['processing_error'] = ai_result['error']
                    supabase_record['processing_status'] = 'failed'
                    supabase_record['processing_error'] = ai_result['error']
                else:
                    database_record['processing_status'] = 'completed'
                    database_record['processing_error'] = None
                    supabase_record['processing_status'] = 'completed'
                    supabase_record['processing_error'] = None
                
                logger.info(f"Processed response for user resume {resume_id}: score={database_record.get('overall_score', 0)}")
                
            except Exception as extract_error:
                logger.error(f"Response processing error for user resume {resume_id}: {extract_error}")
                # Create minimal update record on processing failure
                database_record = {
                    'id': resume_id,
                    'user_id': user_id,
                    'processing_status': 'failed',
                    'processing_error': f'Response processing failed: {str(extract_error)}',
                    'processing_completed_at': datetime.utcnow().isoformat(),
                    'ai_processing_time': int(processing_time),
                    'ai_feedback': f'Processing failed during response processing: {str(extract_error)}',
                    'overall_score': 60,  # Default score
                    'analysis_results': json.dumps(ai_result),
                    'skills': json.dumps([]),
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                supabase_record = database_record.copy()
            
            # Update database with AI results (dual-format support)
            try:
                if self.db_manager:
                    # Try Railway PostgreSQL update first (primary database)
                    railway_success = False
                    if hasattr(self.db_manager, 'railway_pg') and self.db_manager.railway_pg:
                        try:
                            # Use Railway-formatted data for PostgreSQL
                            self.db_manager.railway_pg.execute_write(
                                """UPDATE resumes SET 
                                   processing_status = %s,
                                   processing_error = %s,
                                   processing_completed_at = %s,
                                   ai_processing_time = %s,
                                   overall_score = %s,
                                   technical_score = %s,
                                   experience_score = %s,
                                   education_score = %s,
                                   role_fit_score = %s,
                                   skills = %s::jsonb,
                                   analysis_results = %s::jsonb,
                                   ai_feedback = %s,
                                   updated_at = NOW()
                                   WHERE id = %s""",
                                (
                                    database_record['processing_status'],
                                    database_record.get('processing_error'),
                                    database_record['processing_completed_at'],
                                    database_record['ai_processing_time'],
                                    database_record.get('overall_score', 60),
                                    database_record.get('technical_score', 60),
                                    database_record.get('experience_score', 60),
                                    database_record.get('education_score', 60),
                                    database_record.get('role_fit_score', 60),
                                    database_record.get('skills', '[]'),
                                    database_record.get('analysis_results', '{}'),
                                    database_record.get('ai_feedback', ''),
                                    resume_id
                                )
                            )
                            railway_success = True
                            logger.info(f"✅ Railway PostgreSQL updated for resume {resume_id}")
                        except Exception as railway_error:
                            logger.error(f"Railway PostgreSQL update failed for resume {resume_id}: {railway_error}")
                    
                    # Try Supabase update (secondary/backup database)
                    supabase_success = False
                    if hasattr(self.db_manager, 'supabase') and self.db_manager.supabase and self.db_manager.supabase.admin_client:
                        try:
                            # Use Supabase-formatted data
                            update_response = self.db_manager.supabase.admin_client.table('resumes').update(supabase_record).eq('id', resume_id).execute()
                            if update_response.data:
                                supabase_success = True
                                logger.info(f"✅ Supabase updated for resume {resume_id}")
                            else:
                                logger.warning(f"Supabase update returned no data for resume {resume_id}")
                        except Exception as supabase_error:
                            logger.error(f"Supabase update failed for resume {resume_id}: {supabase_error}")
                    
                    # Log overall success status
                    if railway_success or supabase_success:
                        logger.info(f"✅ Database update successful for resume {resume_id} (Railway: {railway_success}, Supabase: {supabase_success})")
                    else:
                        logger.error(f"❌ All database updates failed for resume {resume_id}")
                        
                else:
                    logger.error(f"No database manager available for user resume {resume_id}")
                    
            except Exception as db_error:
                logger.error(f"Database update error for user resume {resume_id}: {db_error}")
                
                # Try minimal status update via Supabase
                try:
                    if self.supabase:
                        self.supabase.store_analysis_result(resume_id, ai_result, user_id)
                        logger.info(f"Minimal analysis stored for user resume {resume_id}")
                except Exception:
                    logger.error(f"All database update methods failed for user resume {resume_id}")
                    
        except Exception as e:
            logger.error(f"Fallback AI processing failed for user resume {resume_id}: {e}")
            
            # Try to update status to failed
            try:
                if self.db_manager and self.db_manager.supabase:
                    self.db_manager.supabase.admin_client.table('resumes').update({
                        'processing_status': 'failed',
                        'processing_error': str(e),
                        'processing_completed_at': datetime.utcnow().isoformat()
                    }).eq('id', resume_id).execute()
            except Exception:
                pass  # Silent failure for cleanup
    
    async def _process_user_resume_unified_ai(self, resume_id: str, resume_text: str, filename: str, user_id: str):
        """Process user resume using unified AI processor with admin-configurable models"""
        try:
            logger.info(f"🤖 Starting unified AI processing for resume {resume_id} (user: {user_id})")
            
            # Get unified AI processor
            if not hasattr(self, 'unified_ai_processor') or not self.unified_ai_processor:
                self.unified_ai_processor = get_unified_processor(
                    railway_db=self.railway_db,
                    cache_manager=getattr(self, 'cache_manager', None)
                )
            
            # Process resume with user's configured AI provider
            start_time = datetime.utcnow()
            
            # Emit real-time update: processing started
            if hasattr(self, 'emit_resume_update'):
                self.emit_resume_update(resume_id, 'processing_started', {
                    'user_id': user_id,
                    'filename': filename,
                    'started_at': start_time.isoformat()
                })
            
            # Run AI analysis with user's preferred provider
            ai_result = await self.unified_ai_processor.process_resume(
                resume_text=resume_text,
                user_id=user_id,
                analysis_type="comprehensive"
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Emit real-time update: processing completed
            if hasattr(self, 'emit_resume_update'):
                self.emit_resume_update(resume_id, 'processing_completed', {
                    'user_id': user_id,
                    'processing_time_ms': processing_time,
                    'provider_used': ai_result.provider_used.value if ai_result.provider_used else 'unknown',
                    'success': ai_result.success
                })
            
            # Log AI processing for monitoring
            if self.railway_db and ai_result.provider_used:
                try:
                    self.railway_db.execute_write("""
                        INSERT INTO ai_processing_logs 
                        (user_id, resume_id, ai_provider, ai_model, processing_time_ms, tokens_used, 
                         cost_estimate, success, error_message, analysis_type, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        user_id, resume_id, ai_result.provider_used.value, ai_result.model_used,
                        int(processing_time), ai_result.tokens_used, ai_result.cost_estimate,
                        ai_result.success, ai_result.error, 'comprehensive'
                    ))
                except Exception as log_error:
                    logger.error(f"Failed to log AI processing: {log_error}")
            
            # Prepare comprehensive database record with enhanced field mapping
            if ai_result.success and ai_result.data:
                # Extract data using both new agentic format and legacy format
                data = ai_result.data
                
                # Handle nested structure from agentic format
                candidate_info = data.get('candidate_info', {})
                scores = data.get('scores', {})
                analysis = data.get('analysis', {})
                skills = data.get('skills', {})
                assessment = data.get('assessment', {})
                recommendations = data.get('recommendations', {})
                
                # Create comprehensive database record
                database_record = {
                    # Core scores (support both formats)
                    'overall_score': scores.get('overall_score', data.get('overall_score', 75)),
                    'experience_score': scores.get('experience_score', data.get('experience_score', 70)),
                    'skills_score': scores.get('skills_score', data.get('skills_score', 75)),
                    'education_score': scores.get('education_score', data.get('education_score', 70)),
                    'technical_score': scores.get('technical_score', data.get('technical_score', 65)),
                    'role_fit_score': scores.get('role_fit_score', data.get('role_fit_score', 70)),
                    
                    # Candidate information
                    'candidate_name': candidate_info.get('name', data.get('candidate_name', 'Unknown')),
                    'candidate_email': candidate_info.get('email', data.get('candidate_email', '')),
                    'candidate_phone': candidate_info.get('phone', data.get('candidate_phone', '')),
                    'candidate_location': candidate_info.get('location', data.get('location', '')),
                    
                    # Analysis details
                    'summary': analysis.get('summary', data.get('summary', '')),
                    'experience_years': analysis.get('experience_years', data.get('experience_years', 0)),
                    'seniority_level': analysis.get('seniority_level', 'unknown'),
                    'industry_fit': analysis.get('industry_fit', data.get('industry_fit', '')),
                    
                    # Skills and capabilities
                    'key_skills': skills.get('key_skills', data.get('key_skills', [])),
                    'technical_skills': skills.get('technical_skills', []),
                    'soft_skills': skills.get('soft_skills', []),
                    'certifications': skills.get('certifications', []),
                    
                    # Assessment
                    'strengths': assessment.get('strengths', data.get('strengths', [])),
                    'improvement_areas': assessment.get('improvement_areas', data.get('improvement_areas', [])),
                    'red_flags': assessment.get('red_flags', []),
                    
                    # Recommendations
                    'recommended_roles': recommendations.get('recommended_roles', data.get('recommended_roles', [])),
                    'keywords_missing': recommendations.get('keywords_missing', data.get('keywords_missing', [])),
                    'suggestions': recommendations.get('suggestions', data.get('recommendations', '')),
                    
                    # Education
                    'education': data.get('education', []),
                    
                    # Salary and market analysis
                    'salary_estimate': analysis.get('salary_estimate', data.get('salary_estimate', {})),
                    'ats_compatibility': scores.get('ats_compatibility', data.get('ats_compatibility', 75)),
                    
                    # Processing metadata
                    'analysis_complete': True,
                    'processing_status': 'completed',
                    'ai_provider_used': ai_result.provider_used.value,
                    'ai_model_used': ai_result.model_used,
                    'ai_processing_time': int(processing_time),
                    'processing_completed_at': datetime.utcnow().isoformat(),
                    
                    # Enhanced agentic fields
                    'confidence_score': data.get('metadata', {}).get('confidence_score', 0.8),
                    'analysis_type': 'comprehensive_agentic'
                }
            else:
                # Error case with comprehensive error handling
                database_record = {
                    'overall_score': 0,
                    'experience_score': 0,
                    'skills_score': 0,
                    'education_score': 0,
                    'technical_score': 0,
                    'role_fit_score': 0,
                    'processing_status': 'failed',
                    'processing_error': ai_result.error,
                    'ai_processing_time': int(processing_time),
                    'processing_completed_at': datetime.utcnow().isoformat(),
                    'analysis_complete': False,
                    'confidence_score': 0.0
                }
            
            # Update database via Railway PostgreSQL with comprehensive field mapping
            try:
                if self.railway_db:
                    # Use transaction for data consistency
                    update_query = """
                        UPDATE resumes SET 
                            overall_score = %s, experience_score = %s, skills_score = %s, education_score = %s,
                            technical_score = %s, role_fit_score = %s, candidate_name = %s, candidate_email = %s, 
                            candidate_phone = %s, candidate_location = %s, summary = %s, experience_years = %s,
                            seniority_level = %s, industry_fit = %s, key_skills = %s, technical_skills = %s,
                            soft_skills = %s, certifications = %s, strengths = %s, improvement_areas = %s,
                            red_flags = %s, recommended_roles = %s, keywords_missing = %s, suggestions = %s,
                            education = %s, salary_estimate = %s, ats_compatibility = %s, analysis_complete = %s,
                            processing_status = %s, ai_provider_used = %s, ai_model_used = %s,
                            ai_processing_time = %s, processing_completed_at = %s, confidence_score = %s,
                            analysis_type = %s, updated_at = NOW()
                        WHERE id = %s AND user_id = %s
                    """
                    
                    update_params = (
                        database_record.get('overall_score'),
                        database_record.get('experience_score'),
                        database_record.get('skills_score'),
                        database_record.get('education_score'),
                        database_record.get('technical_score'),
                        database_record.get('role_fit_score'),
                        database_record.get('candidate_name'),
                        database_record.get('candidate_email'),
                        database_record.get('candidate_phone'),
                        database_record.get('candidate_location'),
                        database_record.get('summary'),
                        database_record.get('experience_years'),
                        database_record.get('seniority_level'),
                        database_record.get('industry_fit'),
                        json.dumps(database_record.get('key_skills', [])),
                        json.dumps(database_record.get('technical_skills', [])),
                        json.dumps(database_record.get('soft_skills', [])),
                        json.dumps(database_record.get('certifications', [])),
                        json.dumps(database_record.get('strengths', [])),
                        json.dumps(database_record.get('improvement_areas', [])),
                        json.dumps(database_record.get('red_flags', [])),
                        json.dumps(database_record.get('recommended_roles', [])),
                        json.dumps(database_record.get('keywords_missing', [])),
                        database_record.get('suggestions'),
                        json.dumps(database_record.get('education', [])),
                        json.dumps(database_record.get('salary_estimate', {})),
                        database_record.get('ats_compatibility'),
                        database_record.get('analysis_complete'),
                        database_record.get('processing_status'),
                        database_record.get('ai_provider_used'),
                        database_record.get('ai_model_used'),
                        database_record.get('ai_processing_time'),
                        database_record.get('processing_completed_at'),
                        database_record.get('confidence_score'),
                        database_record.get('analysis_type'),
                        resume_id,
                        user_id
                    )
                    
                    update_result = self.railway_db.execute_write(update_query, update_params)
                    
                    if update_result:
                        logger.info(f"✅ Enhanced database updated successfully for resume {resume_id} using {ai_result.provider_used.value if ai_result.provider_used else 'unknown'}")
                        
                        # Emit comprehensive real-time update with enhanced data
                        if hasattr(self, 'emit_resume_update'):
                            enhanced_update_data = {
                                'user_id': user_id,
                                'resume_id': resume_id,
                                'status': 'analysis_complete',
                                'scores': {
                                    'overall_score': database_record.get('overall_score'),
                                    'experience_score': database_record.get('experience_score'),
                                    'skills_score': database_record.get('skills_score'),
                                    'education_score': database_record.get('education_score'),
                                    'technical_score': database_record.get('technical_score'),
                                    'role_fit_score': database_record.get('role_fit_score'),
                                    'ats_compatibility': database_record.get('ats_compatibility')
                                },
                                'candidate_info': {
                                    'name': database_record.get('candidate_name'),
                                    'email': database_record.get('candidate_email')
                                },
                                'analysis': {
                                    'summary': database_record.get('summary'),
                                    'experience_years': database_record.get('experience_years'),
                                    'seniority_level': database_record.get('seniority_level'),
                                    'industry_fit': database_record.get('industry_fit')
                                },
                                'processing_info': {
                                    'provider_used': ai_result.provider_used.value if ai_result.provider_used else 'unknown',
                                    'processing_time_ms': processing_time,
                                    'confidence_score': database_record.get('confidence_score'),
                                    'analysis_type': database_record.get('analysis_type')
                                }
                            }
                            
                            self.emit_resume_update(resume_id, 'analysis_complete', enhanced_update_data)
                            
                        # Also try to update Supabase for consistency (non-blocking)
                        try:
                            if self.db_manager and hasattr(self.db_manager, 'supabase'):
                                supabase_update_data = {
                                    k: v for k, v in database_record.items() 
                                    if k not in ['analysis_type']  # Remove Railway-specific fields
                                }
                                self.db_manager.supabase.admin_client.table('resumes').update(
                                    supabase_update_data
                                ).eq('id', resume_id).execute()
                                logger.info(f"✅ Supabase consistency update completed for resume {resume_id}")
                        except Exception as supabase_error:
                            logger.warning(f"Supabase consistency update failed (non-critical): {supabase_error}")
                            
                    else:
                        logger.error(f"Failed to update Railway database for resume {resume_id}")
                        raise Exception("Railway database update failed")
                
            except Exception as db_error:
                logger.error(f"Database update error for resume {resume_id}: {db_error}")
                
                # Try fallback to Supabase if Railway fails
                try:
                    if self.db_manager and hasattr(self.db_manager, 'supabase'):
                        logger.info(f"Attempting Supabase fallback update for resume {resume_id}")
                        fallback_data = {
                            'overall_score': database_record.get('overall_score'),
                            'experience_score': database_record.get('experience_score'),
                            'skills_score': database_record.get('skills_score'),
                            'education_score': database_record.get('education_score'),
                            'candidate_name': database_record.get('candidate_name'),
                            'processing_status': database_record.get('processing_status'),
                            'ai_provider_used': database_record.get('ai_provider_used'),
                            'processing_completed_at': database_record.get('processing_completed_at'),
                            'analysis_complete': database_record.get('analysis_complete'),
                            'updated_at': datetime.utcnow().isoformat()
                        }
                        
                        supabase_result = self.db_manager.supabase.admin_client.table('resumes').update(
                            fallback_data
                        ).eq('id', resume_id).execute()
                        
                        if supabase_result.data:
                            logger.info(f"✅ Supabase fallback successful for resume {resume_id}")
                        else:
                            raise Exception("Supabase fallback also failed")
                            
                except Exception as fallback_error:
                    logger.error(f"Both Railway and Supabase updates failed for resume {resume_id}: {fallback_error}")
                    
                    # Emit error notification to user
                    if hasattr(self, 'emit_user_notification'):
                        self.emit_user_notification(user_id, 'error', 
                            f"Failed to save analysis results for {filename}. Please contact support.")
                    
                    # Mark as processing failed but don't crash
                    if hasattr(self, 'emit_resume_update'):
                        self.emit_resume_update(resume_id, 'processing_failed', {
                            'user_id': user_id,
                            'error': 'Database storage failed',
                            'retry_possible': True
                        })
            
            logger.info(f"✅ Unified AI processing completed for resume {resume_id} in {processing_time:.0f}ms")
            
        except Exception as e:
            logger.error(f"❌ Unified AI processing failed for resume {resume_id}: {e}")
            
            # Emit error update
            if hasattr(self, 'emit_resume_update'):
                self.emit_resume_update(resume_id, 'processing_failed', {
                    'user_id': user_id,
                    'error': str(e)
                })
            
            # Update status to failed
            try:
                if self.railway_db:
                    self.railway_db.execute_write(
                        "UPDATE resumes SET processing_status = %s, processing_error = %s WHERE id = %s",
                        ('failed', str(e), resume_id)
                    )
            except Exception:
                logger.error(f"Failed to update error status for resume {resume_id}")
            
        except Exception as e:
            logger.error(f"Fallback AI processing failed for user resume {resume_id}: {e}")
            
            # Try to update status to failed
            try:
                if self.db_manager and self.db_manager.supabase:
                    self.db_manager.supabase.admin_client.table('resumes').update({
                        'processing_status': 'failed',
                        'processing_error': f'Fallback AI processing failed: {str(e)}',
                        'processing_completed_at': datetime.utcnow().isoformat()
                    }).eq('id', resume_id).execute()
            except Exception:
                pass  # Silent failure for cleanup

    def _get_resume_text(self, resume_id: str, user_id: str) -> str:
        """Helper method to get resume text for queue processing"""
        try:
            # Get resume data from Supabase
            resume_data = self.supabase.get_resume_by_id(resume_id, user_id)
            if resume_data and 'extracted_text' in resume_data:
                return resume_data['extracted_text']
            else:
                logger.warning(f"No resume text found for ID: {resume_id}")
                return ""
        except Exception as e:
            logger.error(f"Failed to get resume text for {resume_id}: {e}")
            return ""
    
    def _setup_socketio_handlers(self):
        """Setup SocketIO event handlers for real-time features"""
        if not self.socketio:
            return
            
        @self.socketio.on('connect')
        def handle_connect(auth):
            """Handle client connection"""
            try:
                # Verify user authentication
                from flask import request, emit
                from flask_socketio import join_room
                
                user = self.auth_middleware.get_current_user(request)
                if not user:
                    logger.warning("Unauthorized SocketIO connection attempt")
                    return False
                    
                logger.info(f"User {user['email']} connected to real-time features")
                emit('connected', {'status': 'success', 'user_id': user['id']})
                
                # Join user-specific room for targeted updates
                join_room(f"user_{user['id']}")
                
            except Exception as e:
                logger.error(f"SocketIO connection error: {e}")
                return False
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            logger.info("Client disconnected from real-time features")
        
        @self.socketio.on('subscribe_resume_updates')
        def handle_resume_updates(data):
            """Subscribe to resume processing updates"""
            try:
                from flask import request, emit
                from flask_socketio import join_room
                
                user = self.auth_middleware.get_current_user(request)
                if not user:
                    return
                    
                resume_id = data.get('resume_id')
                if resume_id:
                    join_room(f"resume_{resume_id}")
                    emit('subscribed', {'resume_id': resume_id})
                    
            except Exception as e:
                logger.error(f"Resume subscription error: {e}")
    
    def emit_resume_update(self, resume_id, status, data=None):
        """Emit enhanced resume processing updates to subscribed clients with retry logic"""
        if self.socketio:
            try:
                from datetime import datetime
                
                # Enhanced update payload with comprehensive data
                update_payload = {
                    'resume_id': resume_id,
                    'status': status,
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': data or {}
                }
                
                # Add status-specific enhancements
                if status == 'analysis_complete' and data:
                    update_payload['success'] = True
                    update_payload['analysis_ready'] = True
                elif status == 'processing_failed':
                    update_payload['success'] = False
                    update_payload['error'] = data.get('error', 'Processing failed')
                    update_payload['retry_possible'] = data.get('retry_possible', False)
                elif status == 'processing_started':
                    update_payload['progress'] = 10
                    update_payload['message'] = 'AI analysis started'
                
                # Emit to specific resume room and user room for redundancy
                room_name = f"resume_{resume_id}"
                self.socketio.emit('resume_update', update_payload, room=room_name)
                
                # Also emit to user room if user_id is available
                if data and data.get('user_id'):
                    user_room = f"user_{data['user_id']}"
                    self.socketio.emit('resume_update', update_payload, room=user_room)
                
                # General broadcast for admin monitoring
                self.socketio.emit('system_resume_update', {
                    'resume_id': resume_id,
                    'status': status,
                    'timestamp': datetime.utcnow().isoformat()
                }, broadcast=True)
                
                logger.info(f"✅ Enhanced WebSocket update emitted: {status} for resume {resume_id}")
                
            except Exception as e:
                logger.error(f"Failed to emit enhanced resume update: {e}")
                # Try simple fallback emission
                try:
                    self.socketio.emit('resume_update', {
                        'resume_id': resume_id,
                        'status': status,
                        'timestamp': datetime.utcnow().isoformat(),
                        'fallback': True
                    }, broadcast=True)
                    logger.info(f"✅ Fallback WebSocket update emitted for resume {resume_id}")
                except Exception as fallback_error:
                    logger.error(f"Even fallback WebSocket emission failed: {fallback_error}")
        else:
            logger.warning(f"SocketIO not available - cannot emit resume update for {resume_id}")
    
    def emit_user_notification(self, user_id, notification_type, message, data=None):
        """Emit enhanced notifications to specific user with retry logic"""
        if self.socketio:
            try:
                from datetime import datetime
                
                notification_payload = {
                    'type': notification_type,
                    'message': message,
                    'data': data or {},
                    'timestamp': datetime.utcnow().isoformat(),
                    'user_id': user_id
                }
                
                # Add type-specific enhancements
                if notification_type == 'error':
                    notification_payload['severity'] = 'high'
                    notification_payload['requires_action'] = True
                elif notification_type == 'success':
                    notification_payload['severity'] = 'low'
                    notification_payload['auto_dismiss'] = True
                elif notification_type == 'info':
                    notification_payload['severity'] = 'medium'
                    notification_payload['auto_dismiss'] = True
                
                # Emit to user-specific room
                user_room = f"user_{user_id}"
                self.socketio.emit('notification', notification_payload, room=user_room)
                
                # Also emit general notification for admin monitoring
                self.socketio.emit('system_notification', {
                    'user_id': user_id,
                    'type': notification_type,
                    'message': message,
                    'timestamp': datetime.utcnow().isoformat()
                }, broadcast=True)
                
                logger.info(f"✅ Enhanced notification emitted to user {user_id}: {notification_type}")
                
            except Exception as e:
                logger.error(f"Failed to emit enhanced user notification: {e}")
                # Try simple fallback
                try:
                    self.socketio.emit('notification', {
                        'type': notification_type,
                        'message': message,
                        'timestamp': datetime.utcnow().isoformat(),
                        'fallback': True
                    }, broadcast=True)
                except Exception as fallback_error:
                    logger.error(f"Notification fallback also failed: {fallback_error}")
        else:
            logger.warning(f"SocketIO not available - cannot emit notification to user {user_id}")
        
    def run(self):
        """Run the application with SocketIO support"""
        port = int(os.environ.get('PORT', 8000))
        
        logger.info(f"Starting HR ATS Application on port {port}")
        logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
        logger.info(f"SocketIO Support: {'✅ Enabled' if self.socketio else '❌ Disabled'}")
        
        # Run with Gunicorn in production
        if os.getenv('FLASK_ENV') == 'production':
            import subprocess
            # For production, we need eventlet worker class for SocketIO
            worker_class = 'eventlet' if self.socketio else 'sync'
            cmd = [
                'gunicorn',
                '--bind', f'0.0.0.0:{port}',
                '--workers', '2',
                '--threads', '4',
                '--timeout', '300',
                '--keep-alive', '120',
                '--worker-class', worker_class,
                'app:application'
            ]
            subprocess.run(cmd)
        else:
            # Use SocketIO run method if available, otherwise Flask run
            if self.socketio:
                logger.info("🚀 Running with SocketIO support for real-time features")
                self.socketio.run(self.app, host='0.0.0.0', port=port, debug=False)
            else:
                logger.info("🚀 Running with standard Flask (no real-time features)")
                self.app.run(host='0.0.0.0', port=port, debug=False)
    
    def _register_health_endpoints(self):
        """Register simple health check endpoints for Railway - DISABLED TO AVOID CONFLICTS"""
        logger.info("⚠️ _register_health_endpoints() called but disabled to avoid route conflicts")
        logger.info("Health endpoints are already registered by _register_critical_health_endpoints()")
        pass
        
        
        @self.app.route('/health/<service_name>', methods=['GET'])
        def service_health_check(service_name):
            """Health check for specific service"""
            try:
                from utils.service_health_manager import get_service_health_manager
                
                health_manager = get_service_health_manager()
                service_health = health_manager.get_service_health(service_name)
                
                if not service_health:
                    return jsonify({
                        'success': False,
                        'error': f'Service {service_name} not found',
                        'timestamp': datetime.utcnow().isoformat()
                    }), 404
                
                is_available = health_manager.is_service_available(service_name)
                status_message = health_manager.get_service_status_message(service_name)
                
                http_status = 200 if is_available and service_health.status.value == 'healthy' else 503
                
                return jsonify({
                    'success': True,
                    'service_name': service_name,
                    'status': service_health.status.value,
                    'available': is_available,
                    'message': status_message,
                    'response_time_ms': service_health.response_time_ms,
                    'error_count': service_health.error_count,
                    'success_count': service_health.success_count,
                    'last_check': service_health.last_check.isoformat(),
                    'last_error': service_health.last_error,
                    'metadata': service_health.metadata,
                    'timestamp': datetime.utcnow().isoformat()
                }), http_status
                
            except Exception as e:
                logger.error(f"Service health check error for {service_name}: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }), 500

# Create application instance
hr_app = HRATSApplication()
application = hr_app.app  # For WSGI servers

if __name__ == '__main__':
    hr_app.run()
