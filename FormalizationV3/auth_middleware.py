#!/usr/bin/env python3
"""
Enhanced Authentication Middleware for HR ATS System
Supports both database-based sessions and JWT tokens
Handles user and admin authentication with trial limits
"""

import os
import jwt
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional
import logging
from flask import request, jsonify, g

logger = logging.getLogger(__name__)

class AuthMiddleware:
    """Enhanced authentication and authorization middleware"""
    
    def __init__(self, db_manager=None):
        """Initialize enhanced authentication middleware"""
        self.jwt_secret = os.getenv('SUPABASE_JWT_SECRET', self._generate_secret())
        self.trial_limits = {
            'resumes': int(os.getenv('TRIAL_RESUME_LIMIT', 100)),
            'legal_queries': int(os.getenv('TRIAL_LEGAL_QUERIES_LIMIT', 50))
        }
        
        # Initialize database-based authentication
        self.db_manager = db_manager
        if self.db_manager:
            from models.user import User, UserSession, AdminUser
            self.user_manager = User(self.db_manager)
            self.user_session_manager = UserSession(self.db_manager)
            self.admin_user_manager = AdminUser(self.db_manager)
            self.db_auth_enabled = True
            logger.info("Database-based authentication enabled")
        else:
            self.db_auth_enabled = False
            logger.warning("Database authentication not available, using JWT only")
        
    def _generate_secret(self) -> str:
        """Generate JWT secret if not provided"""
        import secrets
        return secrets.token_urlsafe(32)
        
    def require_auth(self, f):
        """Enhanced decorator to require authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Try database-based authentication first
                if self.db_auth_enabled:
                    user = self._authenticate_with_database()
                    if user:
                        g.current_user = user
                        return f(*args, **kwargs)
                
                # Fallback to JWT authentication
                user = self._authenticate_with_jwt()
                if user:
                    g.current_user = user
                    return f(*args, **kwargs)
                
                return jsonify({"error": "Authentication required"}), 401
                
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                return jsonify({"error": "Authentication failed"}), 401
                
        return decorated_function
    
    def _authenticate_with_database(self) -> Optional[Dict[str, Any]]:
        """Authenticate using database sessions"""
        try:
            # Check for session token in Authorization header
            auth_header = request.headers.get('Authorization')
            session_token = None
            
            if auth_header and auth_header.startswith('Bearer '):
                session_token = auth_header.split(' ')[1]
            else:
                # Check cookies
                session_token = request.cookies.get('user_session_token')
            
            if not session_token:
                return None
            
            # Validate session
            user_session = self.user_session_manager.validate_session(session_token)
            if user_session:
                return user_session
            
            return None
            
        except Exception as e:
            logger.error(f"Database authentication error: {e}")
            return None
    
    def _authenticate_with_jwt(self) -> Optional[Dict[str, Any]]:
        """Authenticate using JWT tokens (fallback)"""
        try:
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return None
                
            # Extract token
            token = auth_header.split(' ')[1]
            
            # Verify token and get user
            user = self._verify_jwt_token(token)
            return user
            
        except Exception as e:
            logger.error(f"JWT authentication error: {e}")
            return None
        
    def require_admin(self, f):
        """Enhanced decorator to require admin privileges with detailed logging"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Log the request for debugging
                logger.debug(f"Admin access attempt for {request.endpoint} from {request.remote_addr}")
                
                # Try database-based admin authentication first
                if self.db_auth_enabled:
                    logger.debug("Attempting database-based admin authentication...")
                    admin = self._authenticate_admin_with_database()
                    if admin:
                        logger.info(f"Admin authenticated via database: {admin.get('username', 'unknown')}")
                        g.current_user = admin
                        return f(*args, **kwargs)
                    logger.debug("Database admin authentication failed, trying JWT fallback...")
                
                # Fallback to JWT-based admin check
                logger.debug("Attempting JWT-based admin authentication...")
                user = self._authenticate_with_jwt()
                if user:
                    logger.debug(f"JWT user authenticated: {user.get('email', user.get('username', 'unknown'))}")
                    is_admin = self._is_admin(user)
                    logger.debug(f"Admin privilege check result: {is_admin}")
                    
                    if is_admin:
                        logger.info(f"Admin access granted via JWT: {user.get('email', user.get('username', 'unknown'))}")
                        g.current_user = user
                        return f(*args, **kwargs)
                    else:
                        logger.warning(f"User authenticated but lacks admin privileges: {user.get('email', user.get('username', 'unknown'))}")
                        return jsonify({
                            "error": "Admin privileges required", 
                            "message": "Your account does not have administrative access"
                        }), 403
                else:
                    logger.warning("JWT authentication failed - no valid token found")
                
                logger.warning(f"Admin access denied for {request.endpoint} - authentication failed")
                return jsonify({
                    "error": "Admin privileges required",
                    "message": "Authentication required for administrative access"
                }), 403
                
            except Exception as e:
                logger.error(f"Admin authorization error for {request.endpoint}: {e}")
                return jsonify({
                    "error": "Authorization failed",
                    "message": "An error occurred during authentication"
                }), 403
                
        return decorated_function
    
    def _authenticate_admin_with_database(self) -> Optional[Dict[str, Any]]:
        """Authenticate admin using database sessions"""
        try:
            # Check for admin session token - support multiple header formats
            admin_token = request.headers.get('Admin-Authorization')
            
            # Fallback to standard Authorization header for admin requests
            if not admin_token:
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    admin_token = auth_header.split(' ')[1]
            
            # Final fallback to cookies
            if not admin_token:
                admin_token = request.cookies.get('admin_session_token')
            else:
                # Clean up Bearer prefix if present
                admin_token = admin_token.replace('Bearer ', '')
            
            if not admin_token:
                logger.debug("No admin token found in headers or cookies")
                return None
            
            # Validate admin session
            admin_session = self.admin_user_manager.validate_admin_session(admin_token)
            if admin_session:
                logger.debug(f"Admin session validated for user: {admin_session.get('username', 'unknown')}")
                return admin_session
            
            logger.debug("Admin session validation failed")
            return None
            
        except Exception as e:
            logger.error(f"Database admin authentication error: {e}")
            return None
        
    def _verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user data (legacy method)"""
        return self._verify_jwt_token(token)
        
    def _verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user data with enhanced logging"""
        try:
            logger.debug(f"Attempting JWT verification for token: {token[:20]}...")
            
            # Decode JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            logger.debug(f"JWT payload decoded successfully: {list(payload.keys())}")
            
            # Extract user information
            user_id = payload.get('sub')  # Supabase uses 'sub' for user ID
            email = payload.get('email')
            
            if not user_id or not email:
                logger.warning(f"JWT missing required fields - user_id: {bool(user_id)}, email: {bool(email)}")
                return None
                
            # Return user data in expected format
            user_data = {
                'user_id': user_id,
                'email': email,
                'name': payload.get('name', email.split('@')[0]),
                'username': payload.get('username', email.split('@')[0]),
                'access_type': payload.get('access_type', 'trial'),
                'is_admin': payload.get('is_admin', False),
                'is_trial': payload.get('access_type', 'trial') == 'trial',
                'permissions': payload.get('permissions', []),
                'user_metadata': payload.get('user_metadata', {})
            }
            
            logger.debug(f"JWT user extracted: {user_data.get('email')} (admin: {user_data.get('is_admin')})")
            return user_data
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT token invalid: {e}")
            return None
        except Exception as e:
            logger.error(f"JWT verification error: {e}")
            return None
        
    def _is_admin(self, user: Dict[str, Any]) -> bool:
        """Check if user has admin privileges with enhanced detection"""
        try:
            # Check for admin flag in user data
            if user.get('is_admin') or user.get('access_type') == 'admin':
                return True
            
            # Check for admin role in Supabase metadata
            metadata = user.get('user_metadata', {})
            if metadata.get('role') == 'admin':
                return True
            
            # Check username/email for hardcoded admin (temporary fallback)
            username = user.get('username', '').lower()
            email = user.get('email', '').lower()
            
            # Hardcoded admin usernames and emails for fallback
            admin_identifiers = ['admin', 'administrator', 'admin@admin.com']
            
            if username in admin_identifiers or email in admin_identifiers:
                logger.info(f"Admin access granted via hardcoded identifier: {username or email}")
                return True
            
            # Check for admin permissions in permissions array
            permissions = user.get('permissions', [])
            if 'admin' in permissions or 'all' in permissions:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Admin check error: {e}")
            return False
            
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user from request context"""
        return getattr(g, 'current_user', None)
        
    def check_trial_limits(self, user_id: str, usage_type: str = 'resume') -> bool:
        """Enhanced trial limits checking"""
        try:
            # If database authentication is available, use it
            if self.db_auth_enabled:
                user_data = self.user_manager.get_user_by_id(int(user_id))
                if user_data:
                    limits = self.user_manager.check_trial_limit(int(user_id), usage_type)
                    return limits.get('can_use', False)
            
            # Fallback to basic checking (for JWT-only mode)
            current_user = self.get_current_user()
            if not current_user:
                return False
                
            # If user is not trial, allow unlimited usage
            if not current_user.get('is_trial', True):
                return True
                
            # For trial users, implement basic checking
            # This would need to be enhanced with persistent storage
            logger.warning("Trial limits checking limited in JWT-only mode")
            return True  # Default to allowing for now
            
        except Exception as e:
            logger.error(f"Trial limits check error: {e}")
            return False
            
    def increment_trial_usage(self, user_id: str, usage_type: str = 'resume') -> bool:
        """Increment trial usage counter"""
        try:
            # If database authentication is available, use it
            if self.db_auth_enabled:
                return self.user_manager.increment_trial_usage(int(user_id), usage_type)
            
            # For JWT-only mode, this would need external storage
            logger.warning("Trial usage tracking limited in JWT-only mode")
            return True
            
        except Exception as e:
            logger.error(f"Trial usage increment error: {e}")
            return False
            
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            if self.db_auth_enabled:
                self.db_manager.cleanup_expired_sessions()
                logger.info("Expired sessions cleaned up")
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
            
    def health_check(self) -> Dict[str, Any]:
        """Authentication system health check"""
        try:
            health = {
                'auth_middleware': True,
                'jwt_secret_configured': bool(self.jwt_secret),
                'database_auth_enabled': self.db_auth_enabled,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if self.db_auth_enabled:
                health['database'] = self.db_manager.health_check()
            
            return health
            
        except Exception as e:
            logger.error(f"Auth health check error: {e}")
            return {
                'auth_middleware': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


# Global auth instance for route decorators
_global_auth_instance = None

def _get_auth_instance():
    """Get or create global auth instance for route decorators"""
    global _global_auth_instance
    if _global_auth_instance is None:
        try:
            # Try to import and use existing database manager
            from models.database import DatabaseManager
            db_manager = DatabaseManager()
            _global_auth_instance = AuthMiddleware(db_manager)
            logger.info("Global auth instance created with database support")
        except Exception as e:
            logger.warning(f"Creating auth instance without database: {e}")
            _global_auth_instance = AuthMiddleware()
    return _global_auth_instance

def require_auth(f):
    """Standalone require_auth decorator for route imports"""
    auth_instance = _get_auth_instance()
    return auth_instance.require_auth(f)

def require_admin(f):
    """Standalone require_admin decorator for route imports"""
    auth_instance = _get_auth_instance()
    return auth_instance.require_admin(f)

def require_admin_auth(f):
    """Alias for require_admin to support existing imports"""
    return require_admin(f)

def get_current_user():
    """Standalone get_current_user function for route imports"""
    auth_instance = _get_auth_instance()
    return auth_instance.get_current_user()
