"""
Enhanced Security Middleware for Bear Systems Resume Screening Application
Provides comprehensive security checks and trial validation
"""

from functools import wraps
from flask import request, jsonify, g
import time
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Global rate limiting storage (in production, use Redis)
rate_limits = defaultdict(lambda: deque())

# Security configuration
SECURITY_CONFIG = {
    'MAX_REQUESTS_PER_MINUTE': 60,
    'MAX_ADMIN_REQUESTS_PER_MINUTE': 120,
    'MAX_UPLOAD_SIZE': 10 * 1024 * 1024,  # 10MB
    'SESSION_TIMEOUT_HOURS': 8,
    'TRIAL_HARD_LIMIT': 100,
    'TRIAL_DAILY_LIMIT': 20
}

def rate_limit_check(key: str, limit: int, window_minutes: int = 1) -> bool:
    """Check if request is within rate limits"""
    now = time.time()
    window_start = now - (window_minutes * 60)
    
    # Clean old entries
    while rate_limits[key] and rate_limits[key][0] < window_start:
        rate_limits[key].popleft()
    
    # Check limit
    if len(rate_limits[key]) >= limit:
        return False
    
    # Add current request
    rate_limits[key].append(now)
    return True

def get_client_identifier():
    """Get client identifier for rate limiting"""
    return f"{request.remote_addr}:{request.headers.get('User-Agent', '')[:50]}"

def security_headers():
    """Apply security headers to response"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # Add security headers
            if hasattr(response, 'headers'):
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['X-Frame-Options'] = 'DENY'
                response.headers['X-XSS-Protection'] = '1; mode=block'
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
                response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            return response
        return decorated_function
    return decorator

def enhanced_trial_validation(f):
    """Enhanced trial validation with server-side enforcement"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = getattr(g, 'current_user', None)
        
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Skip validation for admin users
        if user.get('access_type') == 'admin' or user.get('is_admin'):
            return f(*args, **kwargs)
        
        # Skip validation for full access users
        if user.get('access_type') == 'full':
            return f(*args, **kwargs)
        
        # Validate trial users
        if user.get('access_type') == 'trial':
            # Get current usage from database (server-side source of truth)
            from backend.middleware.auth import user_session_manager
            if user_session_manager and hasattr(user_session_manager, 'user_manager'):
                trial_status = user_session_manager.user_manager.check_trial_limit(user['user_id'])
                
                if trial_status.get('at_limit', False):
                    return jsonify({
                        'error': 'Trial limit exceeded',
                        'message': f'You have reached your trial limit of {SECURITY_CONFIG["TRIAL_HARD_LIMIT"]} resume analyses.',
                        'upgrade_required': True,
                        'contact_info': 'Contact support@bearsystems.co.in to upgrade'
                    }), 403
                
                # Check daily limit as well
                daily_usage = trial_status.get('daily_usage', 0)
                if daily_usage >= SECURITY_CONFIG['TRIAL_DAILY_LIMIT']:
                    return jsonify({
                        'error': 'Daily trial limit exceeded',
                        'message': f'You have reached your daily limit of {SECURITY_CONFIG["TRIAL_DAILY_LIMIT"]} analyses. Please try again tomorrow.',
                        'retry_after': 'tomorrow',
                        'upgrade_available': True
                    }), 429
        
        return f(*args, **kwargs)
    return decorated_function

def admin_security_check(f):
    """Enhanced admin security validation"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Rate limiting for admin endpoints
        client_id = f"admin:{get_client_identifier()}"
        if not rate_limit_check(client_id, SECURITY_CONFIG['MAX_ADMIN_REQUESTS_PER_MINUTE']):
            logger.warning(f"Admin rate limit exceeded for {request.remote_addr}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Validate admin session
        user = getattr(g, 'current_user', None)
        if not user:
            logger.warning(f"Admin endpoint accessed without authentication from {request.remote_addr}")
            return jsonify({'error': 'Admin authentication required'}), 401
        
        if not (user.get('is_admin') or user.get('access_type') == 'admin'):
            logger.warning(f"Non-admin user {user.get('email', 'unknown')} attempted admin access from {request.remote_addr}")
            return jsonify({'error': 'Admin privileges required'}), 403
        
        # Log admin actions
        logger.info(f"Admin action: {request.method} {request.path} by {user.get('username', user.get('email', 'unknown'))}")
        
        return f(*args, **kwargs)
    return decorated_function

def request_validation():
    """Validate incoming requests for security"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Content-Length validation
            if request.content_length and request.content_length > SECURITY_CONFIG['MAX_UPLOAD_SIZE']:
                return jsonify({'error': 'Request too large'}), 413
            
            # Content-Type validation for JSON endpoints
            if request.method in ['POST', 'PUT', 'PATCH'] and request.path.startswith('/api/'):
                if not request.is_json and 'multipart/form-data' not in request.content_type:
                    return jsonify({'error': 'Invalid content type'}), 400
            
            # Rate limiting
            client_id = get_client_identifier()
            if not rate_limit_check(client_id, SECURITY_CONFIG['MAX_REQUESTS_PER_MINUTE']):
                logger.warning(f"Rate limit exceeded for {request.remote_addr}")
                return jsonify({'error': 'Rate limit exceeded. Please slow down.'}), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def audit_log(action: str, details: dict = None):
    """Enhanced audit logging"""
    user = getattr(g, 'current_user', None)
    
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'action': action,
        'user_id': user.get('user_id') if user else None,
        'user_email': user.get('email') if user else None,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'endpoint': f"{request.method} {request.path}",
        'details': details or {}
    }
    
    # Log security events
    logger.info(f"AUDIT: {action} - {log_entry}")
    
    # In production, also send to security monitoring system
    if action in ['login_failed', 'admin_access_denied', 'trial_limit_exceeded']:
        logger.warning(f"SECURITY_EVENT: {log_entry}")

def input_sanitization():
    """Sanitize and validate input data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.is_json:
                data = request.get_json()
                if data:
                    # Remove potentially dangerous keys
                    dangerous_keys = ['__proto__', 'constructor', 'prototype']
                    for key in dangerous_keys:
                        if key in data:
                            del data[key]
                    
                    # Sanitize string values
                    for key, value in data.items():
                        if isinstance(value, str):
                            # Basic XSS protection
                            data[key] = value.replace('<script', '&lt;script').replace('javascript:', '')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Combined security decorator for critical endpoints
def secure_endpoint(require_admin=False, require_trial_check=True):
    """Combined security decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Apply all security checks
            decorators = [
                security_headers(),
                request_validation(),
                input_sanitization()
            ]
            
            if require_admin:
                decorators.append(admin_security_check)
            
            if require_trial_check and not require_admin:
                decorators.append(enhanced_trial_validation)
            
            # Apply decorators in reverse order
            for decorator in reversed(decorators):
                f = decorator(f)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# File upload security
def secure_file_upload():
    """Secure file upload validation"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'file' in request.files:
                file = request.files['file']
                
                # File size validation
                if file.content_length and file.content_length > SECURITY_CONFIG['MAX_UPLOAD_SIZE']:
                    return jsonify({'error': 'File too large'}), 413
                
                # File type validation
                allowed_extensions = {'.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png'}
                file_ext = '.' + file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                
                if file_ext not in allowed_extensions:
                    return jsonify({'error': 'File type not allowed'}), 400
                
                # Basic filename sanitization
                if '../' in file.filename or file.filename.startswith('.'):
                    return jsonify({'error': 'Invalid filename'}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
