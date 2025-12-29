"""
Bear Systems Resume Screening Tool - Database Manager
Handles database connections and migrations for user management.
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and schema updates."""
    
    def __init__(self, db_path: str = "resume_storage/resumes.db"):
        """Initialize database manager."""
        self.db_path = db_path
        self.storage_dir = os.path.dirname(db_path)
        
        # Ensure storage directory exists
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Initialize database with new schema
        self._init_database()
    
    def _init_database(self):
        """Initialize database with all required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Create users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    password_hash VARCHAR(255),
                    access_type VARCHAR(50) DEFAULT 'trial',
                    trial_resumes_analyzed INTEGER DEFAULT 0,
                    trial_limit INTEGER DEFAULT 100,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by_admin VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'active',
                    last_login TIMESTAMP
                )
            """)
            
            # Create user sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            
            # Update existing resumes table to add user tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS resumes_backup AS 
                SELECT * FROM resumes WHERE 1=0
            """)
            
            # Check if user_id column exists in resumes table
            cursor = conn.execute("PRAGMA table_info(resumes)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns:
                conn.execute("ALTER TABLE resumes ADD COLUMN user_id INTEGER")
                logger.info("Added user_id column to resumes table")
            
            if 'is_trial_upload' not in columns:
                conn.execute("ALTER TABLE resumes ADD COLUMN is_trial_upload BOOLEAN DEFAULT FALSE")
                logger.info("Added is_trial_upload column to resumes table")
            
            if 'access_level' not in columns:
                conn.execute("ALTER TABLE resumes ADD COLUMN access_level VARCHAR(50) DEFAULT 'trial'")
                logger.info("Added access_level column to resumes table")
            
            # Create admin users table for admin authentication
            conn.execute("""
                CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'active'
                )
            """)
            
            # Create admin sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER NOT NULL,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (admin_id) REFERENCES admin_users (id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_admin_sessions_token ON admin_sessions(session_token)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id)")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        return conn
    
    def create_default_admin(self, username: str = "Admin", password_hash: str = None):
        """Create default admin user if none exists."""
        if password_hash is None:
            # Bear Systems default admin credentials (temporary)
            import hashlib
            password_hash = hashlib.sha256("Admin1232048".encode()).hexdigest()
            logger.info("Using Bear Systems default admin credentials. Change this in production!")
        
        with self.get_connection() as conn:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO admin_users (username, password_hash)
                    VALUES (?, ?)
                """, (username, password_hash))
                conn.commit()
                logger.info(f"Bear Systems admin user '{username}' created")
            except Exception as e:
                logger.error(f"Failed to create default admin: {e}")
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions from database."""
        with self.get_connection() as conn:
            now = datetime.now().isoformat()
            
            # Clean up user sessions
            cursor = conn.execute("""
                DELETE FROM user_sessions WHERE expires_at < ?
            """, (now,))
            user_sessions_deleted = cursor.rowcount
            
            # Clean up admin sessions
            cursor = conn.execute("""
                DELETE FROM admin_sessions WHERE expires_at < ?
            """, (now,))
            admin_sessions_deleted = cursor.rowcount
            
            conn.commit()
            
            if user_sessions_deleted > 0 or admin_sessions_deleted > 0:
                logger.info(f"Cleaned up {user_sessions_deleted} user sessions and {admin_sessions_deleted} admin sessions")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.get_connection() as conn:
            stats = {}
            
            # User statistics
            cursor = conn.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
            stats['active_users'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM users WHERE access_type = 'trial'")
            stats['trial_users'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM users WHERE access_type = 'full'")
            stats['full_users'] = cursor.fetchone()[0]
            
            # Resume statistics
            cursor = conn.execute("SELECT COUNT(*) FROM resumes")
            stats['total_resumes'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM resumes WHERE is_trial_upload = TRUE")
            stats['trial_resumes'] = cursor.fetchone()[0]
            
            # Session statistics
            cursor = conn.execute("SELECT COUNT(*) FROM user_sessions WHERE expires_at > datetime('now')")
            stats['active_sessions'] = cursor.fetchone()[0]
            
            return stats
