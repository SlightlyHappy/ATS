"""
Railway PostgreSQL Database Implementation
Handles PostgreSQL operations for HR ATS System with Railway Pro optimization
"""

import os
import json
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
import threading
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Union
import json

logger = logging.getLogger(__name__)

class RailwayPostgreSQL:
    """Railway PostgreSQL implementation with connection pooling and health monitoring"""
    
    def __init__(self, database_url: str = None):
        """Initialize Railway PostgreSQL with optimized connection pooling"""
        # Use public URL by default for external connections, internal for Railway deployment
        if database_url:
            self.database_url = database_url
        else:
            # Try internal URL first (for Railway deployment), fallback to public URL
            internal_url = os.getenv('DATABASE_URL')
            public_url = os.getenv('DATABASE_PUBLIC_URL')
            
            # Check if we're running on Railway (has internal network access)
            try:
                import socket
                socket.gethostbyname('postgres.railway.internal')
                self.database_url = internal_url  # Use internal URL on Railway
            except:
                self.database_url = public_url or internal_url  # Use public URL locally
        
        if not self.database_url:
            raise ValueError("DATABASE_URL or DATABASE_PUBLIC_URL environment variable is required")
        
        # Enhance database URL with SSL settings for Railway PostgreSQL
        self.database_url = self._enhance_connection_string(self.database_url)
        
        # Railway Pro optimized connection pool (reduced for stability)
        # Solution 1: Advanced Connection Pool with Circuit Breaker
        self.circuit_breaker = {
            "failure_count": 0,
            "failure_threshold": 3,
            "recovery_timeout": 60,
            "last_failure": None,
            "state": "closed"  # closed, open, half-open
        }
        
        try:
            self.pool = ThreadedConnectionPool(
                minconn=3,    # FURTHER REDUCED - Railway Pro has multiple competing pools
                maxconn=12,   # REDUCED from 25 - Multiple pools competing for connections
                dsn=self.database_url,
                # Enhanced connection parameters for Railway Pro tier with optimized timeouts
                options="-c statement_timeout=45000 -c idle_in_transaction_session_timeout=90000",  # 45s query, 1.5min idle
                connect_timeout=20,   # Slightly higher for Railway Pro
                # Connection keepalive optimized for Railway Pro high-performance environment
                keepalives_idle=600,     # 10 minutes - more aggressive with more resources
                keepalives_interval=30,  # 30 seconds between keepalives
                keepalives_count=3       # Standard retry count
            )
            logger.info("Railway Pro connection pool initialized: 3-12 connections (Pro tier - multi-pool optimized)")
        except Exception as e:
            logger.error(f"Failed to create Railway Pro connection pool: {e}")
            self._circuit_breaker_trip("Pool initialization failed")
            # Fallback to single connection for critical operations
            self.pool = None
            raise
        
        # Health monitoring
        self.health_check_lock = threading.Lock()
        self.last_health_check = None
        self.health_cache_ttl = 30  # seconds
        
        # Performance metrics with detailed logging
        self.query_count = 0
        self.error_count = 0
        self.avg_response_time = 0.0
        self.connection_errors = {
            "timeout": 0,
            "reset_by_peer": 0,
            "unexpected_eof": 0,
            "too_many_clients": 0,
            "other": 0
        }
        
        logger.info("Railway PostgreSQL initialized with enhanced monitoring and error tracking")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with circuit breaker and retry logic"""
        # Check circuit breaker first
        if not self._circuit_breaker_check():
            raise Exception("Circuit breaker is OPEN - Railway PostgreSQL temporarily disabled")
            
        conn = None
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                if not self.pool:
                    raise Exception("Connection pool not available")
                    
                conn = self.pool.getconn()
                
                # Validate connection before use (Solution 3)
                if conn.closed or not self._validate_connection(conn):
                    logger.warning("Invalid or closed connection detected, requesting new connection")
                    try:
                        self.pool.putconn(conn, close=True)  # Force close invalid connection
                    except Exception as ve:
                        logger.warning(f"Error closing invalid connection: {ve}")
                    
                    # Get a fresh connection
                    conn = self.pool.getconn()
                    
                    # Validate the fresh connection too
                    if not self._validate_connection(conn):
                        raise Exception("Fresh connection also invalid - potential Railway issue")
                
                # Success - reset circuit breaker
                self._circuit_breaker_success()
                yield conn
                return
                
            except Exception as e:
                self.error_count += 1
                error_msg = str(e)
                
                # Check for specific error types and handle gracefully (Solution 4 & 5)
                if "connection reset by peer" in error_msg.lower():
                    self.connection_errors["reset_by_peer"] += 1
                    logger.warning(f"Connection reset by peer (#{self.connection_errors['reset_by_peer']}) - likely network issue, retrying with fresh connection")
                    self._force_pool_refresh()
                elif "unexpected eof" in error_msg.lower():
                    self.connection_errors["unexpected_eof"] += 1
                    logger.warning(f"Unexpected EOF (#{self.connection_errors['unexpected_eof']}) - connection dropped, retrying with fresh connection")
                    self._force_pool_refresh()
                elif "too many clients" in error_msg.lower():
                    self.connection_errors["too_many_clients"] += 1
                    logger.error(f"Railway PostgreSQL: Too many clients (#{self.connection_errors['too_many_clients']}) - triggering circuit breaker")
                    self._circuit_breaker_trip(error_msg)
                elif "timeout" in error_msg.lower():
                    self.connection_errors["timeout"] += 1
                    logger.warning(f"Query timeout detected (#{self.connection_errors['timeout']}) - may need to optimize query or increase timeout")
                else:
                    self.connection_errors["other"] += 1
                    logger.warning(f"Generic connection error (#{self.connection_errors['other']}): {error_msg}")
                
                if conn:
                    try:
                        self.pool.putconn(conn)
                    except:
                        pass  # Connection already bad
                    conn = None
                
                if attempt < max_retries - 1:
                    logger.warning(f"Railway connection attempt {attempt + 1} failed: {e}. Retrying in {retry_delay}s...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff with jitter
                    retry_delay += (retry_delay * 0.1 * (attempt + 1))  # Add jitter
                else:
                    logger.error(f"Railway PostgreSQL connection failed after {max_retries} attempts: {e}")
                    self._circuit_breaker_trip(error_msg)
                    raise
                    
        # Cleanup in finally block
        if conn:
            try:
                self.pool.putconn(conn)
            except:
                pass
    
    def execute_write(self, query: str, params: Union[Dict, tuple] = None) -> Dict[str, Any]:
        """Execute write operation with connection pooling and enhanced error handling"""
        start_time = datetime.now()
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params or ())
                    conn.commit()  # Explicit commit to prevent idle-in-transaction
                    
                    # Track performance
                    self.query_count += 1
                    response_time = (datetime.now() - start_time).total_seconds()
                    self._update_response_time(response_time)
                    
                    # Return result if available
                    if cursor.rowcount > 0:
                        try:
                            result = cursor.fetchone()
                            return dict(result) if result else {"affected_rows": cursor.rowcount}
                        except:
                            return {"affected_rows": cursor.rowcount}
                    
                    return {"affected_rows": cursor.rowcount}
                    
        except Exception as e:
            self.error_count += 1
            logger.error(f"Railway write operation failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def execute_read(self, query: str, params: Union[Dict, tuple] = None) -> List[Dict[str, Any]]:
        """Execute read operation with connection pooling and enhanced transaction management"""
        start_time = datetime.now()
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params or ())
                    results = cursor.fetchall()
                    # Explicit commit even for reads to clear transaction state
                    conn.commit()
                    
                    # Track performance
                    self.query_count += 1
                    response_time = (datetime.now() - start_time).total_seconds()
                    self._update_response_time(response_time)
                    
                    return [dict(row) for row in results]
                    
        except Exception as e:
            self.error_count += 1
            logger.error(f"Railway read operation failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def execute_many(self, query: str, params_list: List[Union[Dict, tuple]]) -> int:
        """Execute batch operations for better performance with explicit transaction management"""
        start_time = datetime.now()
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.executemany(query, params_list)
                    conn.commit()  # Explicit commit to prevent idle-in-transaction
                    
                    # Track performance
                    self.query_count += len(params_list)
                    response_time = (datetime.now() - start_time).total_seconds()
                    self._update_response_time(response_time)
                    
                    return cursor.rowcount
                    
        except Exception as e:
            self.error_count += 1
            logger.error(f"Railway batch operation failed: {e}")
            # Explicit rollback on error
            try:
                conn.rollback()
            except:
                pass
            raise
    
    def bulk_insert(self, table: str, records: List[Dict[str, Any]]) -> int:
        """Optimized bulk insert using COPY for maximum performance"""
        if not records:
            return 0
        
        start_time = datetime.now()
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Use COPY for maximum performance on Railway
                    columns = list(records[0].keys())
                    copy_query = f"COPY {table} ({','.join(columns)}) FROM STDIN WITH CSV HEADER"
                    
                    # Convert records to CSV format
                    import io
                    import csv
                    
                    output = io.StringIO()
                    writer = csv.DictWriter(output, fieldnames=columns)
                    writer.writeheader()
                    writer.writerows(records)
                    output.seek(0)
                    
                    cursor.copy_expert(copy_query, output)
                    conn.commit()
                    
                    # Track performance
                    self.query_count += len(records)
                    response_time = (datetime.now() - start_time).total_seconds()
                    self._update_response_time(response_time)
                    
                    return len(records)
                    
        except Exception as e:
            self.error_count += 1
            logger.error(f"Railway bulk insert failed: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health with caching to reduce overhead"""
        with self.health_check_lock:
            now = datetime.now()
            
            # Return cached result if still valid
            if (self.last_health_check and 
                (now - self.last_health_check).seconds < self.health_cache_ttl):
                return {
                    "status": "healthy",
                    "cached": True,
                    "query_count": self.query_count,
                    "error_count": self.error_count,
                    "avg_response_time": self.avg_response_time,
                    "connection_errors": self.connection_errors,
                    "circuit_breaker_state": self.circuit_breaker["state"]
                }
            
            try:
                with self.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT version(), current_timestamp, current_database()")
                        result = cursor.fetchone()
                        
                        self.last_health_check = now
                        return {
                            "status": "healthy",
                            "version": result[0],
                            "timestamp": str(result[1]),
                            "database": result[2],
                            "pool_size": self.pool.minconn,
                            "pool_max": self.pool.maxconn,
                            "pool_status": f"{self.pool.minconn}-{self.pool.maxconn} connections (optimized for Railway)",
                            "query_count": self.query_count,
                            "error_count": self.error_count,
                            "avg_response_time": self.avg_response_time,
                            "connection_errors": self.connection_errors,
                            "circuit_breaker_state": self.circuit_breaker["state"],
                            "circuit_breaker_failures": self.circuit_breaker["failure_count"],
                            "cached": False,
                            "optimization_status": "Railway production optimized - 5-20 connections, 16 thread limit"
                        }
                        
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "query_count": self.query_count,
                    "error_count": self.error_count
                }
    
    def _update_response_time(self, response_time: float):
        """Update average response time with exponential moving average"""
        if self.avg_response_time == 0:
            self.avg_response_time = response_time
        else:
            # Exponential moving average (alpha = 0.1)
            self.avg_response_time = 0.9 * self.avg_response_time + 0.1 * response_time
    
    def _circuit_breaker_trip(self, error_msg: str):
        """Trip the circuit breaker on failure"""
        self.circuit_breaker["failure_count"] += 1
        self.circuit_breaker["last_failure"] = datetime.now()
        
        if self.circuit_breaker["failure_count"] >= self.circuit_breaker["failure_threshold"]:
            self.circuit_breaker["state"] = "open"
            logger.warning(f"Circuit breaker OPEN: {error_msg}")
        
    def _circuit_breaker_check(self) -> bool:
        """Check if circuit breaker allows operation"""
        if self.circuit_breaker["state"] == "closed":
            return True
            
        if self.circuit_breaker["state"] == "open":
            # Check if recovery timeout has passed
            if (datetime.now() - self.circuit_breaker["last_failure"]).seconds > self.circuit_breaker["recovery_timeout"]:
                self.circuit_breaker["state"] = "half-open"
                logger.info("Circuit breaker entering HALF-OPEN state")
                return True
            return False
            
        # half-open state - allow one test request
        return True
    
    def _circuit_breaker_success(self):
        """Reset circuit breaker on successful operation"""
        if self.circuit_breaker["state"] in ["half-open", "open"]:
            self.circuit_breaker["state"] = "closed"
            self.circuit_breaker["failure_count"] = 0
            logger.info("Circuit breaker CLOSED - Railway connection recovered")
    
    def _validate_connection(self, conn):
        """Validate that a connection is still alive and responsive"""
        try:
            # Quick health check with minimal query and short timeout
            with conn.cursor() as cur:
                # Set a very short statement timeout for validation
                cur.execute("SET statement_timeout = '2s'")
                cur.execute("SELECT 1")
                result = cur.fetchone()
                # Reset to normal timeout
                cur.execute("SET statement_timeout = '30s'")
                
                # Ensure no transaction is left hanging
                conn.commit()
                
                return result and result[0] == 1
        except Exception as e:
            logger.warning(f"Connection validation failed: {e}")
            try:
                # Attempt to clear any hanging transaction
                conn.rollback()
            except:
                pass
            return False
    
    def _force_pool_refresh(self):
        """Force refresh of connection pool to recover from network issues"""
        try:
            logger.info("Forcing connection pool refresh due to network issues")
            
            # Close all existing connections
            if hasattr(self.pool, '_pool'):
                for conn in list(self.pool._pool):
                    try:
                        conn.close()
                    except:
                        pass
                self.pool._pool.clear()
            
            if hasattr(self.pool, '_used'):
                for conn in list(self.pool._used.values()):
                    try:
                        conn.close()
                    except:
                        pass
                self.pool._used.clear()
                
            logger.info("Connection pool refreshed successfully")
            
        except Exception as e:
            logger.error(f"Error refreshing connection pool: {e}")
            # Reset circuit breaker to allow retry
            self.circuit_breaker["failure_count"] = max(0, self.circuit_breaker["failure_count"] - 1)
    
    def _enhance_connection_string(self, database_url: str) -> str:
        """Enhance database URL with SSL and connection optimizations for Railway"""
        import urllib.parse as urlparse
        
        try:
            # Parse the URL
            parsed = urlparse.urlparse(database_url)
            
            # Extract components
            scheme = parsed.scheme
            username = parsed.username
            password = parsed.password
            hostname = parsed.hostname
            port = parsed.port
            database = parsed.path.lstrip('/')
            
            # Build query parameters with Railway-optimized SSL settings
            query_params = {}
            
            # Parse existing query parameters
            if parsed.query:
                query_params.update(urlparse.parse_qs(parsed.query, keep_blank_values=True))
            
            # Add/override SSL and connection parameters for Railway PostgreSQL
            ssl_params = {
                'sslmode': 'require',  # Force SSL for Railway
                'connect_timeout': '20',  # 20 second connection timeout
                'application_name': 'hr_ats_railway',  # For monitoring
                # Removed problematic options parameter that was causing DSN parsing issues
            }
            
            # Update query parameters (flatten lists from parse_qs)
            for key, value in ssl_params.items():
                if value is not None:
                    query_params[key] = [value] if isinstance(value, str) else value
            
            # Build the enhanced URL (simplified without problematic options)
            enhanced_params = []
            for key, value in query_params.items():
                if value is not None:
                    val = value[0] if isinstance(value, list) else value
                    enhanced_params.append(f"{key}={val}")
            
            enhanced_query = '&'.join(enhanced_params)
            enhanced_url = f"{scheme}://{username}:{password}@{hostname}:{port}/{database}?{enhanced_query}"
            
            logger.info("Enhanced Railway database URL with SSL and optimized connection parameters")
            return enhanced_url
            
        except Exception as e:
            logger.warning(f"Failed to enhance database URL: {e}, using original URL")
            return database_url

    def close(self):
        """Close all connections in the pool"""
        try:
            self.pool.closeall()
            logger.info("Railway PostgreSQL connection pool closed")
        except Exception as e:
            logger.error(f"Error closing Railway connection pool: {e}")

    # HR ATS Specific Methods
    
    def store_user_profile(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store user profile in Railway PostgreSQL"""
        query = """
            INSERT INTO user_profiles (id, email, full_name, access_type, trial_usage, trial_limit, created_at, updated_at)
            VALUES (%(id)s, %(email)s, %(full_name)s, %(access_type)s, %(trial_usage)s, %(trial_limit)s, %(created_at)s, %(updated_at)s)
            ON CONFLICT (id) DO UPDATE SET
                email = EXCLUDED.email,
                full_name = EXCLUDED.full_name,
                access_type = EXCLUDED.access_type,
                trial_usage = EXCLUDED.trial_usage,
                trial_limit = EXCLUDED.trial_limit,
                updated_at = EXCLUDED.updated_at
            RETURNING *
        """
        return self.execute_write(query, user_data)
    
    def store_resume(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store resume data in Railway PostgreSQL with comprehensive AI fields"""
        
        # Ensure analysis_result is JSON string for JSONB field
        if 'analysis_result' in resume_data and isinstance(resume_data['analysis_result'], dict):
            resume_data['analysis_result'] = json.dumps(resume_data['analysis_result'])
        
        query = """
            INSERT INTO resumes (
                id, user_id, filename, file_hash, file_size, file_type, compressed_content, raw_text,
                upload_date, processing_status, processing_started_at, processing_completed_at, processing_error,
                candidate_name, candidate_email, candidate_phone, skills, experience_years, education_level,
                overall_score, technical_score, experience_score, education_score, role_fit_score,
                ai_feedback, ai_model_used, ai_processing_time, job_titles, companies, programming_languages, 
                certifications, tags, category, priority, is_shortlisted, is_archived, notes,
                analysis_result, similarity_score, created_at, updated_at
            )
            VALUES (
                %(id)s, %(user_id)s, %(filename)s, %(file_hash)s, %(file_size)s, %(file_type)s, 
                %(compressed_content)s, %(raw_text)s, %(upload_date)s, %(processing_status)s, 
                %(processing_started_at)s, %(processing_completed_at)s, %(processing_error)s,
                %(candidate_name)s, %(candidate_email)s, %(candidate_phone)s, %(skills)s, 
                %(experience_years)s, %(education_level)s, %(overall_score)s, %(technical_score)s, 
                %(experience_score)s, %(education_score)s, %(role_fit_score)s, %(ai_feedback)s, 
                %(ai_model_used)s, %(ai_processing_time)s, %(job_titles)s, %(companies)s, 
                %(programming_languages)s, %(certifications)s, %(tags)s, %(category)s, %(priority)s, 
                %(is_shortlisted)s, %(is_archived)s, %(notes)s, %(analysis_result)s, %(similarity_score)s,
                %(created_at)s, %(updated_at)s
            )
            ON CONFLICT (id) DO UPDATE SET
                filename = EXCLUDED.filename,
                file_hash = EXCLUDED.file_hash,
                file_size = EXCLUDED.file_size,
                file_type = EXCLUDED.file_type,
                compressed_content = EXCLUDED.compressed_content,
                raw_text = EXCLUDED.raw_text,
                processing_status = EXCLUDED.processing_status,
                processing_started_at = EXCLUDED.processing_started_at,
                processing_completed_at = EXCLUDED.processing_completed_at,
                processing_error = EXCLUDED.processing_error,
                candidate_name = EXCLUDED.candidate_name,
                candidate_email = EXCLUDED.candidate_email,
                candidate_phone = EXCLUDED.candidate_phone,
                skills = EXCLUDED.skills,
                experience_years = EXCLUDED.experience_years,
                education_level = EXCLUDED.education_level,
                overall_score = EXCLUDED.overall_score,
                technical_score = EXCLUDED.technical_score,
                experience_score = EXCLUDED.experience_score,
                education_score = EXCLUDED.education_score,
                role_fit_score = EXCLUDED.role_fit_score,
                ai_feedback = EXCLUDED.ai_feedback,
                ai_model_used = EXCLUDED.ai_model_used,
                ai_processing_time = EXCLUDED.ai_processing_time,
                job_titles = EXCLUDED.job_titles,
                companies = EXCLUDED.companies,
                programming_languages = EXCLUDED.programming_languages,
                certifications = EXCLUDED.certifications,
                tags = EXCLUDED.tags,
                category = EXCLUDED.category,
                priority = EXCLUDED.priority,
                is_shortlisted = EXCLUDED.is_shortlisted,
                is_archived = EXCLUDED.is_archived,
                notes = EXCLUDED.notes,
                analysis_result = EXCLUDED.analysis_result,
                similarity_score = EXCLUDED.similarity_score,
                updated_at = EXCLUDED.updated_at
            RETURNING *
        """
        return self.execute_write(query, resume_data)
    
    def get_user_resumes(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all resumes for a user from Railway PostgreSQL"""
        query = """
            SELECT id, user_id, filename, upload_date, analysis_result, similarity_score
            FROM resumes 
            WHERE user_id = %s 
            ORDER BY upload_date DESC
        """
        return self.execute_read(query, (user_id,))
    
    def store_legal_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store HR legal query in Railway PostgreSQL"""
        query = """
            INSERT INTO hr_legal_queries (id, user_id, query_text, response_text, category, confidence_score, created_at)
            VALUES (%(id)s, %(user_id)s, %(query_text)s, %(response_text)s, %(category)s, %(confidence_score)s, %(created_at)s)
            RETURNING *
        """
        return self.execute_write(query, query_data)
    
    def store_user_activity(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store user activity in Railway PostgreSQL"""
        query = """
            INSERT INTO user_activity (id, user_id, activity_type, details, timestamp)
            VALUES (%(id)s, %(user_id)s, %(activity_type)s, %(details)s, %(timestamp)s)
            RETURNING *
        """
        return self.execute_write(query, activity_data)

# Create a default instance for import convenience
railway_db = None

def get_railway_db():
    """Get or create Railway database instance"""
    global railway_db
    if railway_db is None:
        railway_db = RailwayPostgreSQL()
    return railway_db
