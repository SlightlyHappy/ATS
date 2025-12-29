"""
Bear Systems Resume Screening Tool - Authentication Middleware
Handles user and admin authentication with session management.
Enhanced with security features.
"""

from functools import wraps
from flask import request, jsonify, g
import logging
from .security import audit_log, admin_security_check, enhanced_trial_validation

logger = logging.getLogger(__name__)

# Global variables to store model instances
user_session_manager = None
admin_user_manager = None
supabase_manager = None

def init_auth_middleware(user_session, admin_user, supabase=None):
    """Initialize authentication middleware with model instances."""
    global user_session_manager, admin_user_manager, supabase_manager
    user_session_manager = user_session
    admin_user_manager = admin_user
    supabase_manager = supabase

def get_session_token():
    """Extract session token from request headers."""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    
    # Also check for token in cookies
    return request.cookies.get('session_token')

def require_auth(f):
    """Decorator to require user or admin authentication - Supabase Primary with SQLite Fallback. Enhanced with security checks."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = get_session_token()
        
        if not session_token:
            logger.warning("No authentication token provided")
            audit_log('auth_no_token', {'ip': request.remote_addr})
            return jsonify({'error': 'No authentication token provided'}), 401
        
        # Detect token type based on format
        # Supabase JWT tokens are much longer and contain dots (JWT format)
        # Our custom tokens are shorter (base64-encoded random strings)
        is_supabase_token = len(session_token) > 200 and '.' in session_token
        
        logger.info(f"Token received: length={len(session_token)}, is_supabase={is_supabase_token}")
        
        # Step 1: Try Supabase session validation first (Primary) - but only for Supabase tokens
        if supabase_manager and is_supabase_token:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                supabase_result = loop.run_until_complete(
                    supabase_manager.validate_session(session_token)
                )
                
                if supabase_result.get('valid'):
                    user_data = supabase_result.get('user')
                    user_data['provider'] = 'supabase'
                    
                    # Store user data in Flask's g object for use in the route
                    g.current_user = user_data
                    g.session_token = session_token
                    
                    # Apply trial validation if needed
                    return enhanced_trial_validation(f)(*args, **kwargs)
                    
            except Exception as e:
                logger.error(f"❌ Supabase session validation error: {e}")
        
        # Step 2: Try admin session validation first (for admin tokens)
        if admin_user_manager:
            admin_data = admin_user_manager.validate_admin_session(session_token)
            if admin_data:
                # Convert admin data to user-compatible format
                user_data = {
                    'user_id': admin_data['admin_id'],
                    'id': admin_data['admin_id'],
                    'username': admin_data['username'],
                    'email': admin_data.get('email', admin_data['username']),
                    'name': admin_data.get('name', admin_data['username']),
                    'access_type': 'admin',
                    'is_admin': True,
                    'provider': 'sqlite_admin',
                    'admin_session': True
                }
                
                # Store user data in Flask's g object for use in the route
                g.current_user = user_data
                g.session_token = session_token
                
                logger.info(f"Admin authenticated via SQLite: {admin_data['username']}")
                # Admin users bypass trial validation
                return f(*args, **kwargs)
        
        # Step 3: SQLite user session validation (for custom backend tokens or Supabase fallback)
        if not user_session_manager:
            logger.error("Authentication system not available")
            audit_log('auth_system_error', {'error': 'Authentication system not available'})
            return jsonify({'error': 'Authentication system not available'}), 500
        
        user_data = user_session_manager.validate_session(session_token)
        
        if not user_data:
            logger.warning(f"Invalid session token: {session_token[:10]}...")
            audit_log('auth_invalid_token', {'ip': request.remote_addr})
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        logger.info(f"User authenticated via SQLite: {user_data.get('email', 'unknown')}")
        user_data['provider'] = 'sqlite'
        user_data['needs_supabase_sync'] = True
        
        # Store user data in Flask's g object for use in the route
        g.current_user = user_data
        g.session_token = session_token
        
        # Apply trial validation if needed
        return enhanced_trial_validation(f)(*args, **kwargs)
    
    return decorated_function

def require_admin_auth(f):
    """Decorator to require admin authentication with enhanced security."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not admin_user_manager:
            logger.error("Admin user manager not initialized")
            audit_log('admin_auth_system_error', {'error': 'Admin user manager not initialized'})
            return jsonify({'error': 'Admin authentication system not available'}), 500
        
        session_token = get_session_token()
        
        if not session_token:
            audit_log('admin_auth_no_token', {'ip': request.remote_addr})
            return jsonify({'error': 'No authentication token provided'}), 401
        
        admin_data = admin_user_manager.validate_admin_session(session_token)
        
        if not admin_data:
            audit_log('admin_auth_invalid_token', {'ip': request.remote_addr})
            return jsonify({'error': 'Invalid or expired admin session'}), 401
        
        # Store admin data in Flask's g object
        g.current_admin = admin_data
        g.admin_session_token = session_token
        
        # Also store in current_user format for compatibility with security middleware
        g.current_user = {
            'user_id': admin_data['admin_id'],
            'id': admin_data['admin_id'],
            'username': admin_data['username'],
            'email': admin_data.get('email', admin_data['username']),
            'name': admin_data.get('name', admin_data['username']),
            'access_type': 'admin',
            'is_admin': True
        }
        
        # Apply additional security checks
        return admin_security_check(f)(*args, **kwargs)
    
    return decorated_function

def get_current_user():
    """Get current authenticated user from Flask's g object."""
    return getattr(g, 'current_user', None)

def get_current_admin():
    """Get current authenticated admin from Flask's g object."""
    return getattr(g, 'current_admin', None)

def optional_auth(f):
    """Decorator for optional authentication - doesn't fail if no auth provided."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not user_session_manager:
            # No auth system available, continue without user data
            g.current_user = None
            return f(*args, **kwargs)
        
        session_token = get_session_token()
        
        if session_token:
            user_data = user_session_manager.validate_session(session_token)
            g.current_user = user_data
        else:
            g.current_user = None
        
        return f(*args, **kwargs)
    
    return decorated_function

def check_feature_access(feature: str):
    """Decorator to check if user has access to a specific feature."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            
            if not user:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Full access users can access everything
            if user['access_type'] == 'full':
                return f(*args, **kwargs)
            
            # Trial users have restricted access
            restricted_features = [
                'csv_export',
                'bulk_download',
                'advanced_analytics',
                'hr_legal',
                'email_manager',
                'persistent_storage'
            ]
            
            if feature in restricted_features:
                return jsonify({
                    'error': 'Feature not available in trial version',
                    'feature': feature,
                    'upgrade_required': True,
                    'message': f'Upgrade to full access to use {feature.replace("_", " ").title()}'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def log_user_action(action: str):
    """Decorator to log user actions for analytics."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            
            if user:
                logger.info(f"User {user['email']} performed action: {action}")
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
