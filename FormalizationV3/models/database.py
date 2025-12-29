"""
Enhanced Database Manager for HR ATS System
Handles both SQLite (local) and Supabase (cloud) database operations
Provides seamless integration for user management and authentication
"""

import sqlite3
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import hashlib
import json
import threading
from contextlib import contextmanager
import queue
import time

# Import our existing Supabase client
from supabase_client import SupabaseClient

logger = logging.getLogger(__name__)

class RailwayOptimizedConnectionPool:
    """Railway-optimized SQLite connection pool for 8GB RAM environment"""
    
    def __init__(self, db_path: str, pool_size: int = 20, timeout: int = 30):
        self.db_path = db_path
        self.pool_size = pool_size
        self.timeout = timeout
        self._pool = queue.Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._created_connections = 0
        
        # Pre-create initial connections for Railway performance
        self._init_pool()
        
        logger.info(f"Railway connection pool initialized: {pool_size} connections")
    
    def _init_pool(self):
        """Initialize connection pool with Railway-optimized settings"""
        for _ in range(min(5, self.pool_size)):  # Start with 5 connections
            conn = self._create_connection()
            if conn:
                self._pool.put(conn)
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Create Railway-optimized SQLite connection with WAL mode"""
        try:
            conn = sqlite3.connect(
                self.db_path, 
                timeout=self.timeout,
                check_same_thread=False,  # Allow multi-threading for Railway
                isolation_level='DEFERRED'  # Better concurrency
            )
            
            # Railway performance optimizations - WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for concurrency
            conn.execute("PRAGMA synchronous=NORMAL")  # Balance speed/safety for Railway
            conn.execute("PRAGMA cache_size=10000")  # 10MB cache for 8GB RAM
            conn.execute("PRAGMA temp_store=MEMORY")  # Use RAM for temp tables
            conn.execute("PRAGMA mmap_size=134217728")  # 128MB mmap for Railway
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA busy_timeout=30000")  # 30s timeout for Railway concurrency
            
            # Additional Railway optimizations - Week 4 Database Preparation
            conn.execute("PRAGMA wal_autocheckpoint=1000")  # Auto-checkpoint every 1000 pages
            conn.execute("PRAGMA journal_size_limit=67108864")  # 64MB journal limit
            conn.execute("PRAGMA incremental_vacuum(1000)")  # Incremental vacuum for maintenance
            conn.execute("PRAGMA optimize")  # Optimize database statistics
            
            self._created_connections += 1
            logger.debug(f"Created Railway-optimized SQLite connection (total: {self._created_connections})")
            return conn
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            return None
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool with Railway timeout handling"""
        conn = None
        start_time = time.time()
        
        try:
            # Try to get connection from pool
            try:
                conn = self._pool.get(timeout=5)  # 5 second timeout for Railway
            except queue.Empty:
                # Create new connection if pool is empty and under limit
                with self._lock:
                    if self._created_connections < self.pool_size:
                        conn = self._create_connection()
                        if not conn:
                            raise Exception("Failed to create new connection")
                    else:
                        # Wait a bit more if we're at limit
                        try:
                            conn = self._pool.get(timeout=10)
                        except queue.Empty:
                            raise Exception("Connection pool exhausted - Railway limit reached")
            
            yield conn
            
        except Exception as e:
            logger.error(f"Connection pool error: {e}")
            raise
        finally:
            if conn:
                # Return connection to pool if it's still good
                try:
                    # Test connection before returning to pool
                    conn.execute("SELECT 1")
                    self._pool.put(conn)
                except:
                    # Connection is bad, don't return to pool
                    logger.warning("Discarding bad connection from pool")
                    with self._lock:
                        self._created_connections -= 1
    
    @contextmanager
    def get_transaction(self):
        """Get connection with transaction isolation for Railway concurrency"""
        with self.get_connection() as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")  # Immediate lock for consistency
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction failed: {e}")
                raise
    
    def execute_with_retry(self, query: str, params: tuple = (), max_retries: int = 3):
        """Execute query with retry logic for Railway concurrency"""
        for attempt in range(max_retries):
            try:
                with self.get_connection() as conn:
                    cursor = conn.execute(query, params)
                    conn.commit()
                    return cursor.fetchall()
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying attempt {attempt + 1}")
                    time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                    continue
                raise
            except Exception as e:
                logger.error(f"Database execute error: {e}")
                raise
            # Return connection to pool if valid
            if conn:
                try:
                    # Quick health check
                    conn.execute("SELECT 1")
                    self._pool.put(conn)
                except:
                    # Connection is bad, don't return to pool
                    with self._lock:
                        self._created_connections -= 1
                    try:
                        conn.close()
                    except:
                        pass
            
            # Log slow queries for Railway monitoring
            duration = time.time() - start_time
            if duration > 5:
                logger.warning(f"Slow database operation: {duration:.2f}s")

class DatabaseManager:
    """Enhanced database manager with Railway-optimized connection pooling."""
    
    def __init__(self, db_path: str = "data/local.db", use_supabase: bool = True):
        """Initialize database manager with Railway optimization."""
        self.db_path = db_path
        self.storage_dir = os.path.dirname(db_path)
        self.use_supabase = use_supabase
        
        # Initialize Railway-optimized connection pool (REDUCED for Railway Pro)
        self.connection_pool = RailwayOptimizedConnectionPool(
            db_path=db_path,
            pool_size=5,   # REDUCED from 20 - Railway Pro PostgreSQL connection limit
            timeout=30
        )
        
        # Initialize Supabase client if available
        self.supabase = None
        if use_supabase:
            try:
                self.supabase = SupabaseClient()
                logger.info("Supabase integration enabled")
            except Exception as e:
                logger.warning(f"Supabase not available, using local SQLite: {e}")
                self.use_supabase = False
        
        # Initialize Railway PostgreSQL if DATABASE_URL is available
        self.railway_pg = None
        self.backup_sync = None
        if os.getenv('DATABASE_URL'):
            try:
                from railway_database import RailwayPostgreSQL
                from backup_sync import BackupSyncManager
                
                self.railway_pg = RailwayPostgreSQL()
                logger.info("Railway PostgreSQL integration enabled")
                
                # Initialize backup sync if both Railway and Supabase are available
                if self.supabase and os.getenv('BACKUP_SYNC_ENABLED', 'true').lower() == 'true':
                    self.backup_sync = BackupSyncManager(self.railway_pg, self.supabase)
                    self.backup_sync.start_background_sync()
                    logger.info("Backup sync to Supabase started")
                    
            except Exception as e:
                logger.warning(f"Railway PostgreSQL not available: {e}")
        
        # Database routing configuration
        self.primary_db = os.getenv('PRIMARY_DB', 'railway')  # 'railway' or 'supabase' - Railway PostgreSQL as default
        self.dual_write = os.getenv('DUAL_WRITE', 'false').lower() == 'true'
        
        # Ensure local storage directory exists
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Initialize local database as backup/cache
        self._init_local_database()
        
        # Create default admin if needed
        self.create_default_admin()
        
        # Schedule database optimization for Railway
        self._schedule_maintenance()
    
    def _schedule_maintenance(self):
        """Schedule Railway-optimized database maintenance"""
        import threading
        import time
        
        def maintenance_worker():
            while True:
                try:
                    # Wait 1 hour between maintenance cycles
                    time.sleep(3600)
                    
                    # Run maintenance during low-traffic periods
                    current_hour = datetime.now().hour
                    if 2 <= current_hour <= 6:  # 2 AM - 6 AM maintenance window
                        self._run_maintenance()
                        
                except Exception as e:
                    logger.error(f"Database maintenance error: {e}")
                    time.sleep(600)  # Wait 10 minutes on error
        
        maintenance_thread = threading.Thread(target=maintenance_worker, daemon=True)
        maintenance_thread.start()
        logger.info("Railway database maintenance scheduler started")
    
    def _run_maintenance(self):
        """Run Railway-optimized database maintenance"""
        try:
            with self.get_connection() as conn:
                logger.info("Starting Railway database maintenance...")
                
                # Optimize database
                conn.execute("PRAGMA optimize")
                
                # WAL checkpoint for Railway efficiency
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                
                # Analyze database statistics
                conn.execute("ANALYZE")
                
                # Vacuum if needed (only if significant changes)
                vacuum_result = conn.execute("PRAGMA incremental_vacuum(1000)").fetchone()
                
                logger.info("Railway database maintenance completed")
                
        except Exception as e:
            logger.error(f"Database maintenance error: {e}")
    
    def get_connection(self):
        """Get Railway-optimized database connection"""
        return self.connection_pool.get_connection()
    
    def _init_local_database(self):
        """Initialize local SQLite database with all required tables."""
        with self.get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Enhanced users table with trial management
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supabase_id VARCHAR(255) UNIQUE,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    password_hash VARCHAR(255),
                    access_type VARCHAR(50) DEFAULT 'trial',
                    trial_resumes_analyzed INTEGER DEFAULT 0,
                    trial_legal_queries INTEGER DEFAULT 0,
                    trial_resume_limit INTEGER DEFAULT 100,
                    trial_legal_limit INTEGER DEFAULT 50,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by_admin VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'active',
                    last_login TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Enhanced user sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            
            # Enhanced admin users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    name VARCHAR(255),
                    permissions TEXT DEFAULT '["all"]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'active',
                    metadata TEXT
                )
            """)
            
            # Enhanced admin sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER NOT NULL,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (admin_id) REFERENCES admin_users (id) ON DELETE CASCADE
                )
            """)
            
            # System analytics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name VARCHAR(255) NOT NULL,
                    metric_value TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Admin activity log table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS admin_activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activity_type VARCHAR(255) NOT NULL,
                    user_id INTEGER,
                    admin_user VARCHAR(255) NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
                )
            """)
            
            # API usage tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    admin_id INTEGER,
                    endpoint VARCHAR(255) NOT NULL,
                    method VARCHAR(10) NOT NULL,
                    status_code INTEGER,
                    response_time_ms INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    user_agent TEXT
                )
            """)
            
            # Performance indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)",
                "CREATE INDEX IF NOT EXISTS idx_users_supabase_id ON users(supabase_id)",
                "CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token)",
                "CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at)",
                "CREATE INDEX IF NOT EXISTS idx_admin_sessions_token ON admin_sessions(session_token)",
                "CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires ON admin_sessions(expires_at)",
                "CREATE INDEX IF NOT EXISTS idx_analytics_metric ON system_analytics(metric_name)",
                "CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON system_analytics(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint)",
                "CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage(timestamp)"
            ]
            
            for index in indexes:
                conn.execute(index)
            
            conn.commit()
            logger.info("Local database initialized successfully")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get local database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_default_admin(self, username: str = "admin", password: str = "Benzie1!Benzie1!Benzie1!"):
        """Create default admin user if none exists."""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        with self.get_connection() as conn:
            try:
                # Check if admin already exists by both username and email
                cursor = conn.execute("""
                    SELECT id FROM admin_users 
                    WHERE username = ? OR email = ?
                """, (username, "admin@bearsystems.co.in"))
                
                if cursor.fetchone():
                    logger.info(f"Admin user '{username}' or admin email already exists - skipping creation")
                    return
                
                # Create admin user
                conn.execute("""
                    INSERT INTO admin_users (username, email, password_hash, name, permissions)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, "admin@bearsystems.co.in", password_hash, "System Administrator", 
                     json.dumps(["all"])))
                
                conn.commit()
                logger.info(f"Default admin user '{username}' created successfully")
                logger.info(f"Admin email set to: admin@bearsystems.co.in")
                
            except Exception as e:
                # Check if it's a duplicate constraint error
                if "UNIQUE constraint failed" in str(e):
                    logger.info(f"Admin user already exists (caught constraint error): {e}")
                    return
                else:
                    logger.error(f"Failed to create default admin: {e}")
                    raise
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions from both local and Supabase."""
        now = datetime.now().isoformat()
        
        with self.get_connection() as conn:
            # Clean up local user sessions
            cursor = conn.execute("""
                DELETE FROM user_sessions WHERE expires_at < ? OR is_active = FALSE
            """, (now,))
            user_sessions_deleted = cursor.rowcount
            
            # Clean up local admin sessions
            cursor = conn.execute("""
                DELETE FROM admin_sessions WHERE expires_at < ? OR is_active = FALSE
            """, (now,))
            admin_sessions_deleted = cursor.rowcount
            
            conn.commit()
            
            if user_sessions_deleted > 0 or admin_sessions_deleted > 0:
                logger.info(f"Cleaned up {user_sessions_deleted} user sessions and {admin_sessions_deleted} admin sessions")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        stats = {}
        
        with self.get_connection() as conn:
            # User statistics
            cursor = conn.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
            result = cursor.fetchone()
            stats['active_users'] = result[0] if result else 0
            
            cursor = conn.execute("SELECT COUNT(*) FROM users WHERE access_type = 'trial'")
            result = cursor.fetchone()
            stats['trial_users'] = result[0] if result else 0
            
            cursor = conn.execute("SELECT COUNT(*) FROM users WHERE access_type = 'full'")
            result = cursor.fetchone()
            stats['full_users'] = result[0] if result else 0
            
            # Session statistics
            cursor = conn.execute("SELECT COUNT(*) FROM user_sessions WHERE expires_at > datetime('now')")
            result = cursor.fetchone()
            stats['active_sessions'] = result[0] if result else 0
            
            cursor = conn.execute("SELECT COUNT(*) FROM admin_sessions WHERE expires_at > datetime('now')")
            result = cursor.fetchone()
            stats['active_admin_sessions'] = result[0] if result else 0
            
            # Trial usage statistics
            cursor = conn.execute("""
                SELECT 
                    SUM(trial_resumes_analyzed) as total_analyzed,
                    AVG(trial_resumes_analyzed) as avg_analyzed,
                    COUNT(CASE WHEN trial_resumes_analyzed >= trial_resume_limit THEN 1 END) as at_limit
                FROM users 
                WHERE access_type = 'trial' AND status = 'active'
            """)
            trial_stats = cursor.fetchone()
            stats['trial_stats'] = {
                'total_analyzed': trial_stats[0] if trial_stats and trial_stats[0] else 0,
                'avg_analyzed': trial_stats[1] if trial_stats and trial_stats[1] else 0,
                'at_limit': trial_stats[2] if trial_stats and trial_stats[2] else 0
            }
        
        # Add Supabase stats if available
        if self.supabase:
            try:
                supabase_stats = self.supabase.get_admin_stats()
                stats['supabase'] = supabase_stats
            except Exception as e:
                logger.warning(f"Could not get Supabase stats: {e}")
                stats['supabase'] = {'error': str(e)}
        
        return stats
    
    def log_api_usage(self, user_id: Optional[int] = None, admin_id: Optional[int] = None,
                     endpoint: str = "", method: str = "", status_code: int = 200,
                     response_time_ms: int = 0, ip_address: str = "", user_agent: str = ""):
        """Log API usage for analytics."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO api_usage 
                    (user_id, admin_id, endpoint, method, status_code, response_time_ms, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, admin_id, endpoint, method, status_code, response_time_ms, ip_address, user_agent))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log API usage: {e}")
    
    def record_system_metric(self, metric_name: str, metric_value: Any, metadata: Optional[Dict] = None):
        """Record system metrics for monitoring."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO system_analytics (metric_name, metric_value, metadata)
                    VALUES (?, ?, ?)
                """, (metric_name, json.dumps(metric_value), json.dumps(metadata) if metadata else None))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to record system metric: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health = {
            'local_db': False,
            'supabase': False,
            'timestamp': datetime.now().isoformat()
        }
        
        # Check local database
        try:
            with self.get_connection() as conn:
                conn.execute("SELECT 1")
                health['local_db'] = True
        except Exception as e:
            logger.error(f"Local database health check failed: {e}")
            health['local_db_error'] = str(e)
        
        # Check Supabase
        if self.supabase:
            try:
                health['supabase'] = self.supabase.health_check()
            except Exception as e:
                logger.error(f"Supabase health check failed: {e}")
                health['supabase_error'] = str(e)
        
        return health

    def get_resume_content(self, resume_id: str, user_id: str = None) -> Optional[str]:
        """Get resume content by ID."""
        try:
            if self.supabase:
                # Get resume data from Supabase
                resume_data = self.supabase.get_resume_by_id(resume_id, user_id)
                if resume_data and 'extracted_text' in resume_data:
                    return resume_data['extracted_text']
            
            logger.warning(f"No resume content found for ID: {resume_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get resume content for {resume_id}: {e}")
            return None

    # ==================== HYBRID DATABASE METHODS ====================
    
    def _execute_hybrid_write_custom(self, operation_name: str, railway_func, supabase_func, record_id=None):
        """Execute write operation with hybrid Railway + Supabase support (custom version without kwargs passing)"""
        
        if self.primary_db == 'railway' and self.railway_pg:
            try:
                # Primary write to Railway
                result = railway_func()
                
                # Queue backup sync to Supabase if enabled
                if self.backup_sync and record_id:
                    self.backup_sync.queue_sync('resumes', record_id, 'upsert', result)
                
                logger.debug(f"Railway {operation_name} successful")
                return result
                
            except Exception as e:
                logger.error(f"Railway {operation_name} failed: {e}")
                
                # Automatic fallback to Supabase
                if self.supabase:
                    logger.info(f"Falling back to Supabase for {operation_name}")
                    try:
                        return supabase_func()
                    except Exception as supabase_error:
                        logger.error(f"Supabase fallback also failed: {supabase_error}")
                        raise Exception(f"Both Railway and Supabase failed for {operation_name}")
                else:
                    raise e
        
        elif self.supabase:
            # Primary write to Supabase
            result = supabase_func()
            
            # Dual write to Railway if enabled
            if self.dual_write and self.railway_pg:
                try:
                    railway_func()
                    logger.debug(f"Dual write to Railway successful for {operation_name}")
                except Exception as e:
                    logger.warning(f"Dual write to Railway failed for {operation_name}: {e}")
            
            return result
        
        else:
            raise Exception(f"No database available for {operation_name}")
    
    def _execute_hybrid_write(self, operation_name: str, railway_func, supabase_func, *args, **kwargs):
        """Execute write operation with hybrid Railway + Supabase support"""
        
        if self.primary_db == 'railway' and self.railway_pg:
            try:
                # Primary write to Railway
                result = railway_func(*args, **kwargs)
                
                # Queue backup sync to Supabase if enabled
                if self.backup_sync and 'table' in kwargs and 'record_id' in kwargs:
                    self.backup_sync.queue_sync(
                        kwargs['table'], 
                        kwargs['record_id'], 
                        'upsert',
                        result
                    )
                
                logger.debug(f"Railway {operation_name} successful")
                return result
                
            except Exception as e:
                logger.error(f"Railway {operation_name} failed: {e}")
                
                # Automatic fallback to Supabase
                if self.supabase:
                    logger.info(f"Falling back to Supabase for {operation_name}")
                    try:
                        return supabase_func(*args, **kwargs)
                    except Exception as supabase_error:
                        logger.error(f"Supabase fallback also failed: {supabase_error}")
                        raise Exception(f"Both Railway and Supabase failed for {operation_name}")
                else:
                    raise e
        
        elif self.supabase:
            # Primary write to Supabase
            result = supabase_func(*args, **kwargs)
            
            # Dual write to Railway if enabled
            if self.dual_write and self.railway_pg:
                try:
                    railway_func(*args, **kwargs)
                    logger.debug(f"Dual write to Railway successful for {operation_name}")
                except Exception as e:
                    logger.warning(f"Dual write to Railway failed for {operation_name}: {e}")
            
            return result
        
        else:
            raise Exception(f"No database available for {operation_name}")
    
    def _execute_hybrid_read(self, operation_name: str, railway_func, supabase_func, *args, **kwargs):
        """Execute read operation with hybrid Railway + Supabase support"""
        
        if self.primary_db == 'railway' and self.railway_pg:
            try:
                result = railway_func(*args, **kwargs)
                logger.debug(f"Railway {operation_name} successful")
                return result
            except Exception as e:
                logger.warning(f"Railway {operation_name} failed, using Supabase: {e}")
                
                # Fallback to Supabase
                if self.supabase:
                    return supabase_func(*args, **kwargs)
                else:
                    raise e
        
        elif self.supabase:
            return supabase_func(*args, **kwargs)
        
        else:
            raise Exception(f"No database available for {operation_name}")
    
    def store_user_profile_hybrid(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store user profile using hybrid database approach"""
        
        def railway_operation():
            return self.railway_pg.store_user_profile(user_data)
        
        def supabase_operation():
            # Adapt data format for Supabase if needed
            return self.supabase.store_user_profile(user_data)
        
        return self._execute_hybrid_write(
            'store_user_profile',
            railway_operation,
            supabase_operation,
            table='user_profiles',
            record_id=user_data.get('id')
        )
    
    def store_resume_hybrid(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store resume using hybrid database approach"""
        
        def railway_operation():
            return self.railway_pg.store_resume(resume_data)
        
        def supabase_operation():
            # Use the correct Supabase method for inserting a complete resume record
            # Remove the UUID for Supabase auto-generation, but keep all other fields
            supabase_data = resume_data.copy()
            supabase_data.pop('id', None)  # Let Supabase generate the ID
            
            # Try inserting the complete resume record using admin client (bypasses RLS)
            try:
                response = self.supabase.admin_client.table('resumes').insert(supabase_data).execute()
                
                if response.data:
                    return {'id': response.data[0]['id'], 'success': True}
                else:
                    raise Exception("Failed to insert resume into Supabase")
            except Exception as e:
                # If foreign key constraint fails, try with minimal data approach
                logger.warning(f"Full resume insert failed ({e}), trying minimal data approach")
                
                # Create minimal resume record that doesn't rely on user_profiles
                minimal_data = {
                    'filename': supabase_data.get('filename', 'admin_upload.pdf'),
                    'processed_content': supabase_data.get('processed_content', ''),
                    'processing_status': supabase_data.get('processing_status', 'completed'),
                    'created_at': supabase_data.get('created_at'),
                    'updated_at': supabase_data.get('updated_at')
                }
                
                # If user_id causes issues, omit it for admin uploads
                if 'user_id' in supabase_data:
                    try:
                        # Try with user_id first
                        minimal_data['user_id'] = supabase_data['user_id']
                        response = self.supabase.admin_client.table('resumes').insert(minimal_data).execute()
                        if response.data:
                            return {'id': response.data[0]['id'], 'success': True}
                    except:
                        # If user_id still fails, omit it completely
                        minimal_data.pop('user_id', None)
                        response = self.supabase.admin_client.table('resumes').insert(minimal_data).execute()
                        if response.data:
                            return {'id': response.data[0]['id'], 'success': True, 'note': 'Stored without user_id'}
                
                raise Exception("Failed to store resume with any approach")
        
        return self._execute_hybrid_write_custom(
            'store_resume',
            railway_operation,
            supabase_operation,
            resume_data.get('id')
        )
    
    def get_user_resumes_hybrid(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user resumes using hybrid database approach"""
        
        def railway_operation():
            return self.railway_pg.get_user_resumes(user_id)
        
        def supabase_operation():
            return self.supabase.get_user_resumes(user_id)
        
        return self._execute_hybrid_read(
            'get_user_resumes',
            railway_operation,
            supabase_operation
        )
    
    def store_legal_query_hybrid(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store HR legal query using hybrid database approach"""
        
        def railway_operation():
            return self.railway_pg.store_legal_query(query_data)
        
        def supabase_operation():
            return self.supabase.store_legal_query(
                query_data.get('query_text'),
                query_data.get('response_text'),
                query_data.get('user_id'),
                query_data.get('category'),
                query_data.get('confidence_score')
            )
        
        return self._execute_hybrid_write(
            'store_legal_query',
            railway_operation,
            supabase_operation,
            table='hr_legal_queries',
            record_id=query_data.get('id')
        )
    
    def store_user_activity_hybrid(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store user activity using hybrid database approach"""
        
        def railway_operation():
            return self.railway_pg.store_user_activity(activity_data)
        
        def supabase_operation():
            return self.supabase.store_user_activity(
                activity_data.get('user_id'),
                activity_data.get('activity_type'),
                activity_data.get('details')
            )
        
        return self._execute_hybrid_write(
            'store_user_activity',
            railway_operation,
            supabase_operation,
            table='user_activity',
            record_id=activity_data.get('id')
        )
    
    def get_database_health_hybrid(self) -> Dict[str, Any]:
        """Get comprehensive health status of all databases"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'primary_db': self.primary_db,
            'dual_write': self.dual_write
        }
        
        # Check Railway PostgreSQL
        if self.railway_pg:
            try:
                health['railway'] = self.railway_pg.health_check()
            except Exception as e:
                health['railway_error'] = str(e)
        
        # Check Supabase
        if self.supabase:
            try:
                health['supabase'] = self.supabase.health_check()
            except Exception as e:
                health['supabase_error'] = str(e)
        
        # Check backup sync status
        if self.backup_sync:
            try:
                health['backup_sync'] = self.backup_sync.get_sync_status()
            except Exception as e:
                health['backup_sync_error'] = str(e)
        
        # Check local SQLite
        try:
            with self.get_connection() as conn:
                conn.execute("SELECT 1")
                health['local_sqlite'] = True
        except Exception as e:
            health['local_sqlite_error'] = str(e)
        
        return health

# Week 4: Database Optimization Integration
class OptimizedDatabaseManager(DatabaseManager):
    """Enhanced DatabaseManager with Week 4 optimizations"""
    
    def __init__(self, db_path: str = "data/local.db", supabase_enabled: bool = True):
        super().__init__(db_path, supabase_enabled)
        self.optimizer = None
        self.dual_db = None
        
        # Initialize Week 4 optimizations
        self._initialize_optimizations()
    
    def _initialize_optimizations(self):
        """Initialize Week 4 database optimizations"""
        try:
            # Add the current directory to the path for imports
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            
            # Import and initialize SQLite optimizer
            from database_optimizer import SQLiteOptimizer, DualDatabaseSupport
            
            # Initialize SQLite optimizer
            self.optimizer = SQLiteOptimizer(self.db_path)
            logger.info("✅ Week 4 SQLite optimizer initialized")
            
            # Initialize dual database support (SQLite + PostgreSQL)
            pg_config = {
                'host': os.getenv('PGHOST'),
                'port': os.getenv('PGPORT', 5432),
                'database': os.getenv('PGDATABASE'),
                'user': os.getenv('PGUSER'),
                'password': os.getenv('PGPASSWORD')
            }
            
            self.dual_db = DualDatabaseSupport(self.db_path, pg_config)
            logger.info("✅ Week 4 dual database support initialized")
            
        except ImportError:
            logger.warning("⚠️ Week 4 database optimizations not available")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Week 4 optimizations: {e}")
    
    def create_backup(self, backup_name: str = None):
        """Create database backup using Week 4 optimizer"""
        if self.optimizer:
            return self.optimizer.create_backup(backup_name)
        else:
            logger.warning("Database optimizer not available for backup")
            return None
    
    def get_optimized_connection(self):
        """Get database connection with Week 4 optimizations"""
        if self.dual_db:
            return self.dual_db.get_connection()
        else:
            return self.get_connection()

# Create global optimized database manager instance
db_manager = OptimizedDatabaseManager()
