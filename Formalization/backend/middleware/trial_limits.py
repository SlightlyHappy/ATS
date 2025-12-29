"""
Bear Systems Resume Screening Tool - Trial Limitations Middleware
Handles trial user limitations and usage tracking.
"""

from functools import wraps
from flask import jsonify, g
import logging

logger = logging.getLogger(__name__)

# Global variable to store user model instance
user_manager = None

def init_trial_middleware(user_model):
    """Initialize trial middleware with user model instance."""
    global user_manager
    user_manager = user_model

def check_trial_limits(f):
    """Decorator to check trial limits before allowing resume upload."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from .auth import get_current_user
        
        user = get_current_user()
        
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Admin users bypass trial limits
        if user.get('access_type') == 'admin' or user.get('is_admin') or user.get('admin_session'):
            logger.info(f"Admin user {user.get('username', user.get('email'))} bypassing trial limits")
            # Set unlimited trial status for admin
            g.trial_status = {
                'can_upload': True,
                'is_trial': False,
                'remaining': -1,  # Unlimited
                'total_limit': -1,
                'is_admin': True
            }
            return f(*args, **kwargs)
        
        if not user_manager:
            logger.error("User manager not initialized")
            return jsonify({'error': 'Trial system not available'}), 500
        
        # Check trial limits for regular users
        trial_status = user_manager.check_trial_limit(user['user_id'])
        
        if not trial_status['can_upload']:
            return jsonify({
                'error': 'Trial limit reached',
                'trial_status': trial_status,
                'upgrade_required': True,
                'message': f'You have reached your trial limit of {trial_status["total_limit"]} resume analyses. Upgrade to continue using the tool.'
            }), 403
        
        # Store trial status in g for use in the route
        g.trial_status = trial_status
        
        return f(*args, **kwargs)
    
    return decorated_function

def track_resume_analysis(f):
    """Decorator to track resume analysis for trial users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from .auth import get_current_user
        
        user = get_current_user()
        
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Admin users don't need tracking
        if user.get('access_type') == 'admin' or user.get('is_admin') or user.get('admin_session'):
            logger.info(f"Admin user {user.get('username', user.get('email'))} bypassing usage tracking")
            return f(*args, **kwargs)
        
        if not user_manager:
            logger.error("User manager not initialized")
            return jsonify({'error': 'Trial system not available'}), 500
        
        # Execute the original function
        result = f(*args, **kwargs)
        
        # If the function was successful and user is trial, increment counter
        if (hasattr(result, 'status_code') and result.status_code == 200) or \
           (isinstance(result, tuple) and len(result) > 1 and result[1] == 200) or \
           (not hasattr(result, 'status_code') and not isinstance(result, tuple)):
            
            if user['access_type'] == 'trial':
                success = user_manager.increment_trial_usage(user['user_id'])
                if success:
                    logger.info(f"Incremented trial usage for user {user['email']}")
                else:
                    logger.warning(f"Failed to increment trial usage for user {user['email']}")
        
        return result
    
    return decorated_function

def get_trial_status():
    """Get trial status for current user."""
    from .auth import get_current_user
    
    user = get_current_user()
    
    if not user or not user_manager:
        return {
            'is_trial': True,
            'can_upload': False,
            'remaining': 0,
            'total_limit': 0
        }
    
    return user_manager.check_trial_limit(user['user_id'])

def require_full_access(f):
    """Decorator to require full access (block trial users)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from .auth import get_current_user
        
        user = get_current_user()
        
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        if user['access_type'] != 'full':
            return jsonify({
                'error': 'Full access required',
                'upgrade_required': True,
                'message': 'This feature is only available to full access users. Please upgrade your account.'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def add_trial_info_to_response(response_data):
    """Add trial information to API response."""
    from .auth import get_current_user
    
    user = get_current_user()
    
    if user and user['access_type'] == 'trial' and user_manager:
        trial_status = user_manager.check_trial_limit(user['user_id'])
        
        if isinstance(response_data, dict):
            response_data['trial_info'] = {
                'is_trial_user': True,
                'remaining_analyses': trial_status['remaining'],
                'total_limit': trial_status['total_limit'],
                'used_analyses': trial_status.get('used', 0)
            }
    elif user and user['access_type'] == 'full':
        if isinstance(response_data, dict):
            response_data['trial_info'] = {
                'is_trial_user': False,
                'unlimited_access': True
            }
    
    return response_data

def get_feature_restrictions():
    """Get list of restricted features for current user."""
    from .auth import get_current_user
    
    user = get_current_user()
    
    if not user or user['access_type'] == 'trial':
        return {
            'restricted_features': [
                'csv_export',
                'bulk_download', 
                'advanced_analytics',
                'hr_legal',
                'email_manager',
                'persistent_storage',
                'unlimited_uploads'
            ],
            'available_features': [
                'basic_resume_analysis',
                'ai_scoring',
                'resume_parsing',
                'basic_dashboard'
            ]
        }
    else:
        return {
            'restricted_features': [],
            'available_features': 'all'
        }

def check_export_access(f):
    """Decorator specifically for export functionality."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from .auth import get_current_user
        
        user = get_current_user()
        
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        if user['access_type'] == 'trial':
            return jsonify({
                'error': 'Export functionality not available in trial',
                'upgrade_required': True,
                'message': 'CSV export and bulk download features are only available to full access users.',
                'contact_info': 'Contact Bear Systems to upgrade your account.'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function
