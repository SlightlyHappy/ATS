"""
Bear Systems Resume Screening Tool - Trial Management Routes
Handles trial status, usage tracking, and limitations.
"""

from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

# Create blueprint
trial_bp = Blueprint('trial', __name__, url_prefix='/api/trial')

# Global variable for user model instance
user_manager = None

def init_trial_routes(user_model):
    """Initialize trial routes with user model instance."""
    global user_manager
    user_manager = user_model

@trial_bp.route('/status', methods=['GET'])
def get_trial_status():
    """Get trial status for current user."""
    from ..middleware.auth import require_auth, get_current_user
    
    @require_auth
    def _get_trial_status():
        try:
            user = get_current_user()
            
            if not user_manager:
                return jsonify({'error': 'Trial management not available'}), 500
            
            # Get trial status
            trial_status = user_manager.check_trial_limit(user['user_id'])
            
            # Add feature restrictions info
            from ..middleware.trial_limits import get_feature_restrictions
            feature_restrictions = get_feature_restrictions()
            
            response_data = {
                'trial_status': trial_status,
                'feature_restrictions': feature_restrictions,
                'user_info': {
                    'access_type': user['access_type'],
                    'email': user['email']
                }
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Trial status error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return _get_trial_status()

@trial_bp.route('/remaining', methods=['GET'])
def get_remaining_analyses():
    """Get remaining analysis count for trial user."""
    from ..middleware.auth import require_auth, get_current_user
    
    @require_auth
    def _get_remaining():
        try:
            user = get_current_user()
            
            if not user_manager:
                return jsonify({'error': 'Trial management not available'}), 500
            
            # Get trial status
            trial_status = user_manager.check_trial_limit(user['user_id'])
            
            if user['access_type'] == 'full':
                response_data = {
                    'unlimited': True,
                    'message': 'Full access user - unlimited analyses'
                }
            else:
                response_data = {
                    'unlimited': False,
                    'remaining': trial_status['remaining'],
                    'used': trial_status.get('used', 0),
                    'total_limit': trial_status['total_limit'],
                    'can_upload': trial_status['can_upload']
                }
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Remaining analyses error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return _get_remaining()

@trial_bp.route('/track-usage', methods=['POST'])
def track_usage():
    """Manually track resume analysis usage (if needed)."""
    from ..middleware.auth import require_auth, get_current_user
    
    @require_auth
    def _track_usage():
        try:
            user = get_current_user()
            
            if not user_manager:
                return jsonify({'error': 'Trial management not available'}), 500
            
            # Only track for trial users
            if user['access_type'] == 'trial':
                success = user_manager.increment_trial_usage(user['user_id'])
                
                if success:
                    # Get updated status
                    trial_status = user_manager.check_trial_limit(user['user_id'])
                    
                    response_data = {
                        'message': 'Usage tracked successfully',
                        'trial_status': trial_status
                    }
                    
                    return jsonify(response_data)
                else:
                    return jsonify({'error': 'Failed to track usage'}), 500
            else:
                return jsonify({
                    'message': 'No tracking needed for full access users',
                    'unlimited': True
                })
            
        except Exception as e:
            logger.error(f"Track usage error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return _track_usage()

@trial_bp.route('/upgrade-info', methods=['GET'])
def get_upgrade_info():
    """Get information about upgrading to full access."""
    from ..middleware.auth import optional_auth, get_current_user
    
    @optional_auth
    def _get_upgrade_info():
        try:
            user = get_current_user()
            
            upgrade_info = {
                'company': 'Bear Systems',
                'website': 'www.bearsystems.co.in',
                'contact_email': 'info@bearsystems.co.in',
                'phone': '+91 8527186615',
                'benefits': [
                    'Unlimited resume analysis',
                    'CSV export functionality',
                    'Access to persistent resume database',
                    'Advanced HR Legal tools',
                    'Email manager integration',
                    'Priority support',
                    'Advanced analytics and reporting'
                ],
                'trial_limitations': [
                    'Maximum 100 resume analyses',
                    'No CSV export',
                    'No persistent data storage',
                    'No advanced features'
                ]
            }
            
            if user and user['access_type'] == 'trial':
                trial_status = user_manager.check_trial_limit(user['user_id']) if user_manager else {}
                upgrade_info['current_usage'] = {
                    'used': trial_status.get('used', 0),
                    'remaining': trial_status.get('remaining', 0),
                    'total_limit': trial_status.get('total_limit', 100)
                }
            
            return jsonify(upgrade_info)
            
        except Exception as e:
            logger.error(f"Upgrade info error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return _get_upgrade_info()

@trial_bp.route('/feature-access', methods=['GET'])
def get_feature_access():
    """Get detailed feature access information for current user."""
    from ..middleware.auth import require_auth, get_current_user
    
    @require_auth
    def _get_feature_access():
        try:
            user = get_current_user()
            
            from ..middleware.trial_limits import get_feature_restrictions
            feature_restrictions = get_feature_restrictions()
            
            if user['access_type'] == 'full':
                access_info = {
                    'access_level': 'full',
                    'restrictions': [],
                    'available_features': 'all',
                    'message': 'Full access - all features available'
                }
            else:
                trial_status = user_manager.check_trial_limit(user['user_id']) if user_manager else {}
                
                access_info = {
                    'access_level': 'trial',
                    'restrictions': feature_restrictions['restricted_features'],
                    'available_features': feature_restrictions['available_features'],
                    'trial_status': trial_status,
                    'message': f"Trial access - {trial_status.get('remaining', 0)} analyses remaining"
                }
            
            return jsonify(access_info)
            
        except Exception as e:
            logger.error(f"Feature access error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return _get_feature_access()

@trial_bp.route('/check-feature/<feature_name>', methods=['GET'])
def check_specific_feature(feature_name):
    """Check if user has access to a specific feature."""
    from ..middleware.auth import require_auth, get_current_user
    
    @require_auth
    def _check_feature():
        try:
            user = get_current_user()
            
            from ..middleware.trial_limits import get_feature_restrictions
            feature_restrictions = get_feature_restrictions()
            
            if user['access_type'] == 'full':
                has_access = True
                message = 'Feature available with full access'
            else:
                has_access = feature_name not in feature_restrictions['restricted_features']
                
                if has_access:
                    message = 'Feature available in trial'
                else:
                    message = f'Feature "{feature_name}" requires full access'
            
            response_data = {
                'feature': feature_name,
                'has_access': has_access,
                'user_access_level': user['access_type'],
                'message': message
            }
            
            if not has_access:
                response_data['upgrade_required'] = True
                response_data['contact_info'] = 'Contact Bear Systems: info@bearsystems.co.in | +91 8527186615'
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Check feature error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return _check_feature()

@trial_bp.route('/stats', methods=['GET'])
def get_trial_stats():
    """Get trial usage statistics (admin endpoint)."""
    from ..middleware.auth import require_admin_auth
    
    @require_admin_auth
    def _get_trial_stats():
        try:
            if not user_manager:
                return jsonify({'error': 'User management not available'}), 500
            
            from ..models.database import DatabaseManager
            db = DatabaseManager()
            stats = db.get_database_stats()
            
            response_data = {
                'user_statistics': {
                    'total_active_users': stats.get('active_users', 0),
                    'trial_users': stats.get('trial_users', 0),
                    'full_users': stats.get('full_users', 0)
                },
                'resume_statistics': {
                    'total_resumes': stats.get('total_resumes', 0),
                    'trial_resumes': stats.get('trial_resumes', 0)
                },
                'system_statistics': {
                    'active_sessions': stats.get('active_sessions', 0)
                }
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Trial stats error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return _get_trial_stats()
