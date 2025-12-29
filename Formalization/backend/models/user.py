"""
Bear Systems Resume Screening Tool - User Models
User and session management for trial and full access users.
"""

import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from .database import DatabaseManager

logger = logging.getLogger(__name__)

class User:
    """User model for Bear Systems Resume Screening Tool."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, email: str, name: str, password: str, 
                   access_type: str = 'trial', created_by_admin: str = None) -> Optional[int]:
        """Create a new user."""
        try:
            password_hash = self.hash_password(password)
            
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO users (email, name, password_hash, access_type, created_by_admin)
                    VALUES (?, ?, ?, ?, ?)
                """, (email, name, password_hash, access_type, created_by_admin))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Created user {email} with ID {user_id}")
                return user_id
                
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: users.email" in str(e):
                logger.warning(f"User with email {email} already exists")
                return None
            raise e
        except Exception as e:
            logger.error(f"Failed to create user {email}: {e}")
            raise e
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data."""
        try:
            password_hash = self.hash_password(password)
            
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, email, name, access_type, trial_resumes_analyzed, 
                           trial_limit, status, created_at
                    FROM users 
                    WHERE email = ? AND password_hash = ? AND status = 'active'
                """, (email, password_hash))
                
                user_row = cursor.fetchone()
                
                if user_row:
                    # Update last login
                    conn.execute("""
                        UPDATE users SET last_login = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    """, (user_row['id'],))
                    conn.commit()
                    
                    # Convert Row to dictionary
                    user_data = {
                        'id': user_row['id'],
                        'email': user_row['email'],
                        'name': user_row['name'],
                        'access_type': user_row['access_type'],
                        'trial_resumes_analyzed': user_row['trial_resumes_analyzed'],
                        'trial_limit': user_row['trial_limit'],
                        'status': user_row['status'],
                        'created_at': user_row['created_at']
                    }
                    
                    logger.info(f"User {email} authenticated successfully")
                    return user_data
                else:
                    logger.warning(f"Authentication failed for {email}")
                    return None
                    
        except Exception as e:
            logger.error(f"Authentication error for {email}: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, email, name, access_type, trial_resumes_analyzed, 
                           trial_limit, status, created_at, last_login
                    FROM users 
                    WHERE id = ? AND status = 'active'
                """, (user_id,))
                
                user_row = cursor.fetchone()
                
                if user_row:
                    return {
                        'id': user_row['id'],
                        'email': user_row['email'],
                        'name': user_row['name'],
                        'access_type': user_row['access_type'],
                        'trial_resumes_analyzed': user_row['trial_resumes_analyzed'],
                        'trial_limit': user_row['trial_limit'],
                        'status': user_row['status'],
                        'created_at': user_row['created_at'],
                        'last_login': user_row['last_login']
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def increment_trial_usage(self, user_id: int) -> bool:
        """Increment trial resume count for user."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE users 
                    SET trial_resumes_analyzed = trial_resumes_analyzed + 1
                    WHERE id = ? AND status = 'active'
                """, (user_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Incremented trial usage for user {user_id}")
                    return True
                else:
                    logger.warning(f"Failed to increment trial usage for user {user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error incrementing trial usage for user {user_id}: {e}")
            return False
    
    def check_trial_limit(self, user_id: int) -> Dict[str, Any]:
        """Check if user has reached trial limit."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT access_type, trial_resumes_analyzed, trial_limit
                    FROM users 
                    WHERE id = ? AND status = 'active'
                """, (user_id,))
                
                user_row = cursor.fetchone()
                
                if user_row:
                    if user_row['access_type'] == 'full':
                        return {
                            'can_upload': True,
                            'is_trial': False,
                            'remaining': -1,  # Unlimited
                            'total_limit': -1
                        }
                    else:
                        remaining = user_row['trial_limit'] - user_row['trial_resumes_analyzed']
                        return {
                            'can_upload': remaining > 0,
                            'is_trial': True,
                            'remaining': max(0, remaining),
                            'total_limit': user_row['trial_limit'],
                            'used': user_row['trial_resumes_analyzed']
                        }
                else:
                    return {
                        'can_upload': False,
                        'is_trial': True,
                        'remaining': 0,
                        'total_limit': 0
                    }
                    
        except Exception as e:
            logger.error(f"Error checking trial limit for user {user_id}: {e}")
            return {
                'can_upload': False,
                'is_trial': True,
                'remaining': 0,
                'total_limit': 0
            }
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (admin function)."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, email, name, access_type, trial_resumes_analyzed, 
                           trial_limit, status, created_at, created_by_admin, last_login
                    FROM users 
                    ORDER BY created_at DESC
                """)
                
                users = []
                for row in cursor.fetchall():
                    users.append({
                        'id': row['id'],
                        'email': row['email'],
                        'name': row['name'],
                        'access_type': row['access_type'],
                        'trial_resumes_analyzed': row['trial_resumes_analyzed'],
                        'trial_limit': row['trial_limit'],
                        'status': row['status'],
                        'created_at': row['created_at'],
                        'created_by_admin': row['created_by_admin'],
                        'last_login': row['last_login']
                    })
                
                return users
                
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []


class UserSession:
    """User session management."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_session(self, user_id: int, ip_address: str = None, 
                      user_agent: str = None, duration_hours: int = 24) -> str:
        """Create a new user session."""
        try:
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=duration_hours)
            
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, session_token, expires_at.isoformat(), ip_address, user_agent))
                
                conn.commit()
                
                logger.info(f"Created session for user {user_id}")
                return session_token
                
        except Exception as e:
            logger.error(f"Failed to create session for user {user_id}: {e}")
            raise e
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate session token and return user data."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT s.user_id, s.expires_at, u.email, u.name, u.access_type, 
                           u.trial_resumes_analyzed, u.trial_limit, u.status
                    FROM user_sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.session_token = ? AND s.expires_at > datetime('now') AND u.status = 'active'
                """, (session_token,))
                
                session_row = cursor.fetchone()
                
                if session_row:
                    return {
                        'user_id': session_row['user_id'],
                        'email': session_row['email'],
                        'name': session_row['name'],
                        'access_type': session_row['access_type'],
                        'trial_resumes_analyzed': session_row['trial_resumes_analyzed'],
                        'trial_limit': session_row['trial_limit'],
                        'status': session_row['status'],
                        'expires_at': session_row['expires_at']
                    }
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None
    
    def delete_session(self, session_token: str) -> bool:
        """Delete a session (logout)."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM user_sessions WHERE session_token = ?
                """, (session_token,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info("Session deleted successfully")
                    return True
                else:
                    logger.warning("Session not found for deletion")
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    def cleanup_user_sessions(self, user_id: int):
        """Clean up all sessions for a user."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM user_sessions WHERE user_id = ?
                """, (user_id,))
                
                conn.commit()
                logger.info(f"Cleaned up {cursor.rowcount} sessions for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up sessions for user {user_id}: {e}")


class AdminUser:
    """Admin user management for Bear Systems."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def authenticate_admin(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate admin user."""
        try:
            password_hash = User.hash_password(password)
            
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, username, created_at, last_login
                    FROM admin_users 
                    WHERE username = ? AND password_hash = ? AND status = 'active'
                """, (username, password_hash))
                
                admin_row = cursor.fetchone()
                
                if admin_row:
                    # Update last login
                    conn.execute("""
                        UPDATE admin_users SET last_login = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    """, (admin_row['id'],))
                    conn.commit()
                    
                    admin_data = {
                        'id': admin_row['id'],
                        'username': admin_row['username'],
                        'created_at': admin_row['created_at'],
                        'last_login': admin_row['last_login']
                    }
                    
                    logger.info(f"Admin {username} authenticated successfully")
                    return admin_data
                else:
                    logger.warning(f"Admin authentication failed for {username}")
                    return None
                    
        except Exception as e:
            logger.error(f"Admin authentication error for {username}: {e}")
            return None
    
    def create_admin_session(self, admin_id: int, duration_hours: int = 8) -> str:
        """Create admin session."""
        try:
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=duration_hours)
            
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO admin_sessions (admin_id, session_token, expires_at)
                    VALUES (?, ?, ?)
                """, (admin_id, session_token, expires_at.isoformat()))
                
                conn.commit()
                
                logger.info(f"Created admin session for admin {admin_id}")
                return session_token
                
        except Exception as e:
            logger.error(f"Failed to create admin session for admin {admin_id}: {e}")
            raise e
    
    def validate_admin_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate admin session."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT s.admin_id, s.expires_at, a.username
                    FROM admin_sessions s
                    JOIN admin_users a ON s.admin_id = a.id
                    WHERE s.session_token = ? AND s.expires_at > datetime('now') AND a.status = 'active'
                """, (session_token,))
                
                session_row = cursor.fetchone()
                
                if session_row:
                    return {
                        'admin_id': session_row['admin_id'],
                        'username': session_row['username'],
                        'expires_at': session_row['expires_at']
                    }
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Admin session validation error: {e}")
            return None
