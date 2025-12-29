"""
Authentication and Authorization Utilities
Handles JWT tokens, session management, and access control
"""

import os
import jwt
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Dict, Any, Optional, Callable
from flask import request, jsonify, g

from supabase_manager import supabase_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthManager:
    """Handles authentication and authorization"""
    
    def __init__(self):
        """Initialize auth manager"""
        self.secret_key = os.getenv('SECRET_KEY', 'hr-resume-screening-flask-secret-key-2025-temp')
        self.jwt_expiration = int(os.getenv('JWT_EXPIRATION_DELTA', 7200))  # 2 hours
        self.algorithm = 'HS256'
        
        logger.info("Auth manager initialized")
    
    def generate_token(self, user_id: str, email: str, user_type: str = 'user') -> str:
        """Generate JWT token for user"""
        try:
            payload = {
                'user_id': user_id,
                'email': email,
                'user_type': user_type,
                'exp': datetime.now(timezone.utc) + timedelta(seconds=self.jwt_expiration),
                'iat': datetime.now(timezone.utc)
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token
            
        except Exception as e:
            logger.error(f"Token generation error: {str(e)}")
            raise Exception(f"Failed to generate token: {str(e)}")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return {'valid': True, 'payload': payload}
            
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token has expired'}
        except jwt.InvalidTokenError:
            return {'valid': False, 'error': 'Invalid token'}
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return {'valid': False, 'error': str(e)}
    
    def extract_token_from_header(self, auth_header: str) -> Optional[str]:
        """Extract token from Authorization header"""
        try:
            if not auth_header:
                return None
            
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return None
            
            return parts[1]
            
        except Exception as e:
            logger.error(f"Token extraction error: {str(e)}")
            return None

# Global auth manager instance
auth_manager = AuthManager()

def require_auth(user_types: list = None):
    """Decorator to require authentication"""
    if user_types is None:
        user_types = ['user', 'admin']
    
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            try:
                # Get authorization header
                auth_header = request.headers.get('Authorization')
                if not auth_header:
                    return jsonify({'error': 'Authorization header required'}), 401
                
                # Extract token
                token = auth_manager.extract_token_from_header(auth_header)
                if not token:
                    return jsonify({'error': 'Invalid authorization header format'}), 401
                
                # Verify token
                verification = auth_manager.verify_token(token)
                if not verification['valid']:
                    return jsonify({'error': verification['error']}), 401
                
                payload = verification['payload']
                
                # Check user type if specified
                if user_types and payload.get('user_type') not in user_types:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                # Store user info in Flask's g object
                g.current_user = {
                    'user_id': payload.get('user_id'),
                    'email': payload.get('email'),
                    'user_type': payload.get('user_type'),
                    'token': token
                }
                
                # Get user profile for additional context
                if payload.get('user_type') == 'user':
                    profile = await supabase_manager.get_user_profile(payload.get('user_id'))
                    g.current_user['profile'] = profile
                
                return await f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Authentication error: {str(e)}")
                return jsonify({'error': 'Authentication failed'}), 401
        
        return decorated_function
    return decorator

def require_admin():
    """Decorator to require admin authentication"""
    return require_auth(['admin'])

def require_user():
    """Decorator to require user authentication"""
    return require_auth(['user'])

def optional_auth():
    """Decorator for optional authentication (doesn't fail if no auth)"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            try:
                # Try to get authorization header
                auth_header = request.headers.get('Authorization')
                if auth_header:
                    token = auth_manager.extract_token_from_header(auth_header)
                    if token:
                        verification = auth_manager.verify_token(token)
                        if verification['valid']:
                            payload = verification['payload']
                            g.current_user = {
                                'user_id': payload.get('user_id'),
                                'email': payload.get('email'),
                                'user_type': payload.get('user_type'),
                                'token': token
                            }
                
                # Continue with function even if auth fails
                if not hasattr(g, 'current_user'):
                    g.current_user = None
                
                return await f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Optional auth error: {str(e)}")
                g.current_user = None
                return await f(*args, **kwargs)
        
        return decorated_function
    return decorator

def check_trial_limits(required_action: str = 'resume_analysis'):
    """Decorator to check trial limitations"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            try:
                # Only check for regular users, not admins
                if g.current_user and g.current_user.get('user_type') == 'user':
                    profile = g.current_user.get('profile')
                    
                    if profile and profile.get('access_type') == 'trial':
                        trial_status = await supabase_manager.get_trial_status(g.current_user['user_id'])
                        
                        if trial_status.get('remaining', 0) <= 0:
                            return jsonify({
                                'error': 'Trial limit exceeded',
                                'message': 'You have reached your trial limit. Please upgrade to continue.',
                                'trial_status': trial_status
                            }), 403
                
                return await f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Trial check error: {str(e)}")
                return jsonify({'error': 'Trial validation failed'}), 500
        
        return decorated_function
    return decorator

async def get_current_user_context() -> Dict[str, Any]:
    """Get current user context with profile and trial info"""
    try:
        if not hasattr(g, 'current_user') or not g.current_user:
            return {'authenticated': False}
        
        user_info = {
            'authenticated': True,
            'user_id': g.current_user['user_id'],
            'email': g.current_user['email'],
            'user_type': g.current_user['user_type']
        }
        
        # Add profile info for regular users
        if g.current_user.get('user_type') == 'user':
            profile = g.current_user.get('profile')
            if profile:
                user_info['profile'] = profile
                
                # Add trial status
                if profile.get('access_type') == 'trial':
                    trial_status = await supabase_manager.get_trial_status(g.current_user['user_id'])
                    user_info['trial_status'] = trial_status
        
        return user_info
        
    except Exception as e:
        logger.error(f"User context error: {str(e)}")
        return {'authenticated': False, 'error': str(e)}

def validate_session_token(token: str) -> Dict[str, Any]:
    """Validate session token and return user info"""
    try:
        verification = auth_manager.verify_token(token)
        if not verification['valid']:
            return {'valid': False, 'error': verification['error']}
        
        payload = verification['payload']
        return {
            'valid': True,
            'user_id': payload.get('user_id'),
            'email': payload.get('email'),
            'user_type': payload.get('user_type'),
            'expires': payload.get('exp')
        }
        
    except Exception as e:
        logger.error(f"Session validation error: {str(e)}")
        return {'valid': False, 'error': str(e)}
