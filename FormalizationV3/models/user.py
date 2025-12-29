"""
Enhanced User Models for HR ATS System
Comprehensive user and session management with Supabase integration
Supports trial users, full users, and admin users with advanced features
"""

import hashlib
import secrets
import sqlite3
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
import json

from .database import DatabaseManager

logger = logging.getLogger(__name__)

class User:
    """Enhanced user model with dual SQLite/Supabase support."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Enhanced password hashing using bcrypt."""
        try:
            # Use bcrypt for better security than SHA-256
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        except Exception:
            # Fallback to SHA-256 for compatibility
            return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        try:
            # Try bcrypt first
            if password_hash.startswith('$2b$'):
                return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
            else:
                # Fallback to SHA-256
                return hashlib.sha256(password.encode()).hexdigest() == password_hash
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def create_user(self, email: str, name: str, password: str, 
                   access_type: str = 'trial', created_by_admin: str = None,
                   trial_resume_limit: int = 100, trial_legal_limit: int = 50) -> Optional[int]:
        """Create a new user with enhanced trial management."""
        try:
            password_hash = self.hash_password(password)
            
            # Try Supabase first if available
            supabase_id = None
            if self.db.supabase:
                try:
                    supabase_result = self.db.supabase.create_user(email, name, password, access_type)
                    if supabase_result:
                        supabase_id = supabase_result.get('id')
                except Exception as e:
                    logger.warning(f"Supabase user creation failed, using local only: {e}")
            
            # Create in local database
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO users (supabase_id, email, name, password_hash, access_type, 
                                     created_by_admin, trial_resume_limit, trial_legal_limit)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (supabase_id, email, name, password_hash, access_type, 
                     created_by_admin, trial_resume_limit, trial_legal_limit))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Created user {email} with ID {user_id} (Supabase ID: {supabase_id})")
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
        """Enhanced user authentication with password verification."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, supabase_id, email, name, password_hash, access_type, 
                           trial_resumes_analyzed, trial_legal_queries, 
                           trial_resume_limit, trial_legal_limit, status, created_at
                    FROM users 
                    WHERE email = ? AND status = 'active'
                """, (email,))
                
                user_row = cursor.fetchone()
                
                if user_row and self.verify_password(password, user_row['password_hash']):
                    # Update last login
                    conn.execute("""
                        UPDATE users SET last_login = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    """, (user_row['id'],))
                    conn.commit()
                    
                    # Convert Row to dictionary with enhanced fields
                    user_data = {
                        'id': user_row['id'],
                        'supabase_id': user_row['supabase_id'],
                        'email': user_row['email'],
                        'name': user_row['name'],
                        'access_type': user_row['access_type'],
                        'trial_resumes_analyzed': user_row['trial_resumes_analyzed'],
                        'trial_legal_queries': user_row['trial_legal_queries'],
                        'trial_resume_limit': user_row['trial_resume_limit'],
                        'trial_legal_limit': user_row['trial_legal_limit'],
                        'status': user_row['status'],
                        'created_at': user_row['created_at'],
                        'is_trial': user_row['access_type'] == 'trial',
                        'is_admin': False
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
        """Get user by ID with enhanced fields."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, supabase_id, email, name, access_type, 
                           trial_resumes_analyzed, trial_legal_queries,
                           trial_resume_limit, trial_legal_limit, 
                           status, created_at, last_login, created_by_admin
                    FROM users 
                    WHERE id = ? AND status = 'active'
                """, (user_id,))
                
                user_row = cursor.fetchone()
                
                if user_row:
                    return {
                        'id': user_row['id'],
                        'supabase_id': user_row['supabase_id'],
                        'email': user_row['email'],
                        'name': user_row['name'],
                        'access_type': user_row['access_type'],
                        'trial_resumes_analyzed': user_row['trial_resumes_analyzed'],
                        'trial_legal_queries': user_row['trial_legal_queries'],
                        'trial_resume_limit': user_row['trial_resume_limit'],
                        'trial_legal_limit': user_row['trial_legal_limit'],
                        'status': user_row['status'],
                        'created_at': user_row['created_at'],
                        'last_login': user_row['last_login'],
                        'created_by_admin': user_row['created_by_admin'],
                        'is_trial': user_row['access_type'] == 'trial',
                        'is_admin': False
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def increment_trial_usage(self, user_id: int, usage_type: str = 'resume') -> bool:
        """Increment trial usage count for user (resume or legal query)."""
        try:
            field_name = 'trial_resumes_analyzed' if usage_type == 'resume' else 'trial_legal_queries'
            
            with self.db.get_connection() as conn:
                cursor = conn.execute(f"""
                    UPDATE users 
                    SET {field_name} = {field_name} + 1
                    WHERE id = ? AND status = 'active'
                """, (user_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Incremented {usage_type} trial usage for user {user_id}")
                    return True
                else:
                    logger.warning(f"Failed to increment {usage_type} trial usage for user {user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error incrementing {usage_type} trial usage for user {user_id}: {e}")
            return False
    
    def check_trial_limit(self, user_id: int, usage_type: str = 'resume') -> Dict[str, Any]:
        """Check if user has reached trial limit for specific usage type."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT access_type, trial_resumes_analyzed, trial_legal_queries,
                           trial_resume_limit, trial_legal_limit
                    FROM users 
                    WHERE id = ? AND status = 'active'
                """, (user_id,))
                
                user_row = cursor.fetchone()
                
                if user_row:
                    if user_row['access_type'] == 'full':
                        return {
                            'can_use': True,
                            'is_trial': False,
                            'remaining': -1,  # Unlimited
                            'total_limit': -1,
                            'usage_type': usage_type
                        }
                    else:
                        if usage_type == 'resume':
                            used = user_row['trial_resumes_analyzed']
                            limit = user_row['trial_resume_limit']
                        else:  # legal
                            used = user_row['trial_legal_queries']
                            limit = user_row['trial_legal_limit']
                        
                        remaining = limit - used
                        return {
                            'can_use': remaining > 0,
                            'is_trial': True,
                            'remaining': max(0, remaining),
                            'total_limit': limit,
                            'used': used,
                            'usage_type': usage_type
                        }
                else:
                    return {
                        'can_use': False,
                        'is_trial': True,
                        'remaining': 0,
                        'total_limit': 0,
                        'usage_type': usage_type
                    }
                    
        except Exception as e:
            logger.error(f"Error checking {usage_type} trial limit for user {user_id}: {e}")
            return {
                'can_use': False,
                'is_trial': True,
                'remaining': 0,
                'total_limit': 0,
                'usage_type': usage_type
            }
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (admin function) with enhanced information."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, supabase_id, email, name, access_type, 
                           trial_resumes_analyzed, trial_legal_queries,
                           trial_resume_limit, trial_legal_limit,
                           status, created_at, created_by_admin, last_login
                    FROM users 
                    ORDER BY created_at DESC
                """)
                
                users = []
                for row in cursor.fetchall():
                    users.append({
                        'id': row['id'],
                        'supabase_id': row['supabase_id'],
                        'email': row['email'],
                        'name': row['name'],
                        'access_type': row['access_type'],
                        'trial_resumes_analyzed': row['trial_resumes_analyzed'],
                        'trial_legal_queries': row['trial_legal_queries'],
                        'trial_resume_limit': row['trial_resume_limit'],
                        'trial_legal_limit': row['trial_legal_limit'],
                        'status': row['status'],
                        'created_at': row['created_at'],
                        'created_by_admin': row['created_by_admin'],
                        'last_login': row['last_login'],
                        'is_trial': row['access_type'] == 'trial'
                    })
                
                return users
                
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    def update_user(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """Update user information."""
        try:
            if not updates:
                return False
            
            # Build dynamic update query
            set_clauses = []
            values = []
            
            allowed_fields = ['name', 'access_type', 'trial_resume_limit', 'trial_legal_limit', 'status']
            
            for field, value in updates.items():
                if field in allowed_fields:
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
            
            if not set_clauses:
                logger.warning("No valid fields to update")
                return False
            
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"
            
            with self.db.get_connection() as conn:
                cursor = conn.execute(query, values)
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Updated user {user_id} with {len(set_clauses)} fields")
                    return True
                else:
                    logger.warning(f"No user found with ID {user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """Soft delete user (set status to inactive)."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE users SET status = 'inactive' WHERE id = ?
                """, (user_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Soft deleted user {user_id}")
                    return True
                else:
                    logger.warning(f"No user found with ID {user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False


class UserSession:
    """Enhanced user session management with improved security."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_session(self, user_id: int, ip_address: str = None, 
                      user_agent: str = None, duration_hours: int = 24) -> str:
        """Create a new user session with enhanced tracking."""
        try:
            session_token = secrets.token_urlsafe(48)  # Longer token for better security
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
        """Validate session token and return enhanced user data."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT s.user_id, s.expires_at, s.ip_address, s.user_agent,
                           u.email, u.name, u.access_type, u.trial_resumes_analyzed, 
                           u.trial_legal_queries, u.trial_resume_limit, u.trial_legal_limit, u.status
                    FROM user_sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.session_token = ? AND s.expires_at > datetime('now') 
                          AND s.is_active = TRUE AND u.status = 'active'
                """, (session_token,))
                
                session_row = cursor.fetchone()
                
                if session_row:
                    return {
                        'user_id': session_row['user_id'],
                        'email': session_row['email'],
                        'name': session_row['name'],
                        'access_type': session_row['access_type'],
                        'trial_resumes_analyzed': session_row['trial_resumes_analyzed'],
                        'trial_legal_queries': session_row['trial_legal_queries'],
                        'trial_resume_limit': session_row['trial_resume_limit'],
                        'trial_legal_limit': session_row['trial_legal_limit'],
                        'status': session_row['status'],
                        'expires_at': session_row['expires_at'],
                        'session_ip': session_row['ip_address'],
                        'session_user_agent': session_row['user_agent'],
                        'is_trial': session_row['access_type'] == 'trial',
                        'is_admin': False
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
                    UPDATE user_sessions SET is_active = FALSE WHERE session_token = ?
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
                    UPDATE user_sessions SET is_active = FALSE WHERE user_id = ?
                """, (user_id,))
                
                conn.commit()
                logger.info(f"Cleaned up {cursor.rowcount} sessions for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up sessions for user {user_id}: {e}")


class AdminUser:
    """Enhanced admin user management with improved security."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def authenticate_admin(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate admin user with enhanced security."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, username, email, name, password_hash, permissions, created_at, last_login
                    FROM admin_users 
                    WHERE username = ? AND status = 'active'
                """, (username,))
                
                admin_row = cursor.fetchone()
                
                if admin_row and User.verify_password(password, admin_row['password_hash']):
                    # Update last login
                    conn.execute("""
                        UPDATE admin_users SET last_login = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    """, (admin_row['id'],))
                    conn.commit()
                    
                    admin_data = {
                        'id': admin_row['id'],
                        'username': admin_row['username'],
                        'email': admin_row['email'],
                        'name': admin_row['name'],
                        'permissions': json.loads(admin_row['permissions']) if admin_row['permissions'] else ['all'],
                        'created_at': admin_row['created_at'],
                        'last_login': admin_row['last_login'],
                        'is_admin': True
                    }
                    
                    logger.info(f"Admin {username} authenticated successfully")
                    return admin_data
                else:
                    logger.warning(f"Admin authentication failed for {username}")
                    return None
                    
        except Exception as e:
            logger.error(f"Admin authentication error for {username}: {e}")
            return None
    
    def create_admin_session(self, admin_id: int, ip_address: str = None, 
                           user_agent: str = None, duration_hours: int = 8) -> str:
        """Create admin session with enhanced tracking."""
        try:
            session_token = secrets.token_urlsafe(48)
            expires_at = datetime.now() + timedelta(hours=duration_hours)
            
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO admin_sessions (admin_id, session_token, expires_at, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?)
                """, (admin_id, session_token, expires_at.isoformat(), ip_address, user_agent))
                
                conn.commit()
                
                logger.info(f"Created admin session for admin {admin_id}")
                return session_token
                
        except Exception as e:
            logger.error(f"Failed to create admin session for admin {admin_id}: {e}")
            raise e
    
    def validate_admin_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate admin session with enhanced data."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT s.admin_id, s.expires_at, s.ip_address, s.user_agent,
                           a.username, a.email, a.name, a.permissions
                    FROM admin_sessions s
                    JOIN admin_users a ON s.admin_id = a.id
                    WHERE s.session_token = ? AND s.expires_at > datetime('now') 
                          AND s.is_active = TRUE AND a.status = 'active'
                """, (session_token,))
                
                session_row = cursor.fetchone()
                
                if session_row:
                    return {
                        'admin_id': session_row['admin_id'],
                        'username': session_row['username'],
                        'email': session_row['email'],
                        'name': session_row['name'],
                        'permissions': json.loads(session_row['permissions']) if session_row['permissions'] else ['all'],
                        'expires_at': session_row['expires_at'],
                        'session_ip': session_row['ip_address'],
                        'session_user_agent': session_row['user_agent'],
                        'is_admin': True
                    }
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Admin session validation error: {e}")
            return None
    
    def delete_admin_session(self, session_token: str) -> bool:
        """Delete admin session (logout)."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE admin_sessions SET is_active = FALSE WHERE session_token = ?
                """, (session_token,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info("Admin session deleted successfully")
                    return True
                else:
                    logger.warning("Admin session not found for deletion")
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting admin session: {e}")
            return False
