from flask import Blueprint, send_from_directory, current_app, jsonify
import os

# Create API blueprint
api_bp = Blueprint('api', __name__)

# Import route modules in specific order - specific routes BEFORE generic routes
from . import analysis  # Import first: has /resumes/<resume_id>/analyses 
from . import resumes   # Import second: has /resumes/<resume_id>
from . import health, sales, pipeline, auth, monitoring, admin, queue, websocket, communication, legal

@api_bp.route('/')
def api_info():
    """API information endpoint."""
    return {
        'message': 'HR Tool API v1',
        'version': '1.3',
        'status': 'active',
        'endpoints': {
            'auth': '/api/v1/auth',
            'health': '/api/v1/health',
            'monitoring': '/api/v1/monitoring',
            'analysis': '/api/v1/analysis',
            'resumes': '/api/v1/resumes',
            'sales': '/api/v1/sales',
            'admin': '/api/v1/admin'
        }
    }

@api_bp.route('/dashboard')
def dashboard():
    """Serve the live dashboard HTML page."""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'dashboard.html')

@api_bp.route('/admin-dashboard')
def admin_dashboard():
    """Serve the admin dashboard HTML page."""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'admin-dashboard.html')

# Error handlers for the API blueprint
@api_bp.errorhandler(401)
def handle_unauthorized(error):
    """Handle 401 Unauthorized errors."""
    return jsonify({
        'success': False,
        'error': {
            'code': 'UNAUTHORIZED',
            'message': 'Authentication required',
            'category': 'authentication'
        }
    }), 401

@api_bp.errorhandler(403)
def handle_forbidden(error):
    """Handle 403 Forbidden errors."""
    return jsonify({
        'success': False,
        'error': {
            'code': 'FORBIDDEN',
            'message': 'Insufficient privileges',
            'category': 'authorization'
        }
    }), 403

# Import error classes and add specific handlers
try:
    from app.services.error_handler import AuthenticationError, AuthorizationError, ApplicationError
    
    @api_bp.errorhandler(AuthenticationError)
    def handle_authentication_error(error):
        """Handle authentication errors."""
        return jsonify({
            'success': False,
            'error': {
                'code': error.error_code,
                'message': error.user_message,
                'category': 'authentication'
            }
        }), 401
    
    @api_bp.errorhandler(AuthorizationError)
    def handle_authorization_error(error):
        """Handle authorization errors."""
        return jsonify({
            'success': False,
            'error': {
                'code': error.error_code,
                'message': error.user_message,
                'category': 'authorization'
            }
        }), 403

except ImportError:
    # If error classes aren't available, skip
    pass

__all__ = ['api_bp']
