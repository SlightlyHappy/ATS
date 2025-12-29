"""
Enhanced Authentication Routes for HR ATS System
Provides comprehensive authentication for users and admins
Supports session management, trial limits, and user creation
"""

from flask import Blueprint, request, jsonify, make_response, g
from datetime import datetime, timedelta
import logging
import json

# Import our enhanced models
from models.database import DatabaseManager
from models.user import User, UserSession, AdminUser

logger = logging.getLogger(__name__)

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Global instances (initialized by main app)
db_manager = None
user_manager = None
user_session_manager = None
admin_user_manager = None

def init_auth_routes(database_manager: DatabaseManager):
    """Initialize authentication routes with database manager."""
    global db_manager, user_manager, user_session_manager, admin_user_manager
    
    db_manager = database_manager
    user_manager = User(database_manager)
    user_session_manager = UserSession(database_manager)
    admin_user_manager = AdminUser(database_manager)
    
    logger.info("Authentication routes initialized successfully")

@auth_bp.route('/admin-login', methods=['POST'])
def admin_login():
    """Admin login endpoint with enhanced session management."""
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Username and password required'}), 400
        
        if not admin_user_manager:
            return jsonify({'error': 'Admin authentication not available'}), 500
        
        # Authenticate admin
        admin_data = admin_user_manager.authenticate_admin(
            data['username'], 
            data['password']
        )
        
        if not admin_data:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create admin session with enhanced tracking
        session_token = admin_user_manager.create_admin_session(
            admin_data['id'],
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            duration_hours=8  # 8-hour admin sessions
        )
        
        response_data = {
            'success': True,
            'message': 'Admin login successful',
            'token': session_token,
            'user': {
                'user_id': admin_data['id'],
                'username': admin_data['username'],
                'email': admin_data.get('email', admin_data['username']),
                'name': admin_data.get('name', admin_data['username']),
                'access_type': 'admin',
                'is_admin': True,
                'permissions': admin_data.get('permissions', ['all'])
            },
            'admin_info': {
                'id': admin_data['id'],
                'username': admin_data['username'],
                'permissions': admin_data.get('permissions', ['all'])
            }
        }
        
        # Set session token in cookie for enhanced security
        response = make_response(jsonify(response_data))
        response.set_cookie(
            'admin_session_token', 
            session_token, 
            httponly=True, 
            secure=True, 
            samesite='Strict',
            max_age=8*60*60  # 8 hours
        )
        
        logger.info(f"Admin {data['username']} logged in successfully from {request.remote_addr}")
        return response
        
    except Exception as e:
        logger.error(f"Admin login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/user-login', methods=['POST'])
def user_login():
    """Enhanced user login endpoint."""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password required'}), 400
        
        if not user_manager:
            return jsonify({'error': 'User authentication not available'}), 500
        
        # Authenticate user
        user_data = user_manager.authenticate_user(
            data['email'], 
            data['password']
        )
        
        if not user_data:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create user session
        session_token = user_session_manager.create_session(
            user_data['id'],
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            duration_hours=24  # 24-hour user sessions
        )
        
        # Get trial limits information
        resume_limits = user_manager.check_trial_limit(user_data['id'], 'resume')
        legal_limits = user_manager.check_trial_limit(user_data['id'], 'legal')
        
        response_data = {
            'success': True,
            'message': 'User login successful',
            'token': session_token,
            'user': {
                'user_id': user_data['id'],
                'email': user_data['email'],
                'name': user_data['name'],
                'access_type': user_data['access_type'],
                'is_admin': False,
                'is_trial': user_data['is_trial'],
                'trial_info': {
                    'resume_limits': resume_limits,
                    'legal_limits': legal_limits
                }
            }
        }
        
        # Set session token in cookie
        response = make_response(jsonify(response_data))
        response.set_cookie(
            'user_session_token', 
            session_token, 
            httponly=True, 
            secure=True, 
            samesite='Strict',
            max_age=24*60*60  # 24 hours
        )
        
        logger.info(f"User {data['email']} logged in successfully from {request.remote_addr}")
        return response
        
    except Exception as e:
        logger.error(f"User login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/create-user', methods=['POST'])
def create_user():
    """Admin endpoint to create new users with enhanced trial management."""
    try:
        # Check admin authentication
        admin_token = request.headers.get('Authorization')
        if not admin_token:
            admin_token = request.cookies.get('admin_session_token')
        else:
            admin_token = admin_token.replace('Bearer ', '')
        
        if not admin_token:
            return jsonify({'error': 'Admin authentication required'}), 401
        
        # Validate admin session
        admin_session = admin_user_manager.validate_admin_session(admin_token)
        if not admin_session:
            return jsonify({'error': 'Invalid or expired admin session'}), 401
        
        data = request.get_json()
        
        required_fields = ['email', 'name', 'password']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Email, name, and password required'}), 400
        
        # Extract user creation parameters
        email = data.get('email')
        name = data.get('name')
        password = data.get('password')
        access_type = data.get('access_type', 'trial')
        trial_resume_limit = data.get('trial_resume_limit', 100)
        trial_legal_limit = data.get('trial_legal_limit', 50)
        
        # Validate access type
        if access_type not in ['trial', 'full']:
            return jsonify({'error': 'Invalid access type. Must be "trial" or "full"'}), 400
        
        # Create user
        user_id = user_manager.create_user(
            email=email,
            name=name,
            password=password,
            access_type=access_type,
            created_by_admin=admin_session['username'],
            trial_resume_limit=trial_resume_limit,
            trial_legal_limit=trial_legal_limit
        )
        
        if user_id:
            # Get created user data
            user_data = user_manager.get_user_by_id(user_id)
            
            response_data = {
                'success': True,
                'message': f'User {email} created successfully',
                'user': {
                    'id': user_id,
                    'email': email,
                    'name': name,
                    'access_type': access_type,
                    'trial_resume_limit': trial_resume_limit,
                    'trial_legal_limit': trial_legal_limit,
                    'created_by_admin': admin_session['username'],
                    'created_at': user_data['created_at'] if user_data else None
                }
            }
            
            logger.info(f"Admin {admin_session['username']} created user {email}")
            return jsonify(response_data), 201
        else:
            return jsonify({'error': 'User with this email already exists'}), 409
            
    except Exception as e:
        logger.error(f"User creation error: {e}")
        return jsonify({'error': 'Failed to create user'}), 500

@auth_bp.route('/session', methods=['GET'])
def validate_session():
    """Validate current session and return user/admin data."""
    try:
        # Check for user session token
        user_token = request.headers.get('Authorization')
        if not user_token:
            user_token = request.cookies.get('user_session_token')
        else:
            user_token = user_token.replace('Bearer ', '')
        
        # Check for admin session token
        admin_token = request.headers.get('Admin-Authorization')
        if not admin_token:
            admin_token = request.cookies.get('admin_session_token')
        
        # Validate user session
        if user_token:
            user_session = user_session_manager.validate_session(user_token)
            if user_session:
                # Get updated trial limits
                resume_limits = user_manager.check_trial_limit(user_session['user_id'], 'resume')
                legal_limits = user_manager.check_trial_limit(user_session['user_id'], 'legal')
                
                return jsonify({
                    'success': True,
                    'session_type': 'user',
                    'user': {
                        'user_id': user_session['user_id'],
                        'email': user_session['email'],
                        'name': user_session['name'],
                        'access_type': user_session['access_type'],
                        'is_admin': False,
                        'is_trial': user_session['is_trial'],
                        'trial_info': {
                            'resume_limits': resume_limits,
                            'legal_limits': legal_limits
                        }
                    }
                })
        
        # Validate admin session
        if admin_token:
            admin_session = admin_user_manager.validate_admin_session(admin_token)
            if admin_session:
                return jsonify({
                    'success': True,
                    'session_type': 'admin',
                    'user': {
                        'user_id': admin_session['admin_id'],
                        'username': admin_session['username'],
                        'email': admin_session.get('email', admin_session['username']),
                        'name': admin_session.get('name', admin_session['username']),
                        'access_type': 'admin',
                        'is_admin': True,
                        'permissions': admin_session.get('permissions', ['all'])
                    }
                })
        
        return jsonify({'error': 'No valid session found'}), 401
        
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        return jsonify({'error': 'Session validation failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user or admin and invalidate session."""
    try:
        # Check for user session token
        user_token = request.headers.get('Authorization')
        if not user_token:
            user_token = request.cookies.get('user_session_token')
        else:
            user_token = user_token.replace('Bearer ', '')
        
        # Check for admin session token
        admin_token = request.headers.get('Admin-Authorization')
        if not admin_token:
            admin_token = request.cookies.get('admin_session_token')
        
        logout_success = False
        
        # Logout user session
        if user_token:
            logout_success = user_session_manager.delete_session(user_token)
        
        # Logout admin session
        if admin_token:
            logout_success = admin_user_manager.delete_admin_session(admin_token)
        
        if logout_success:
            response = make_response(jsonify({
                'success': True,
                'message': 'Logged out successfully'
            }))
            
            # Clear cookies
            response.set_cookie('user_session_token', '', expires=0)
            response.set_cookie('admin_session_token', '', expires=0)
            
            return response
        else:
            return jsonify({'error': 'No active session found'}), 404
            
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user/admin information."""
    try:
        # This endpoint reuses the session validation logic
        return validate_session()
        
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        return jsonify({'error': 'Failed to get user information'}), 500

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change user password (for logged-in users)."""
    try:
        # Get current session
        user_token = request.headers.get('Authorization')
        if not user_token:
            user_token = request.cookies.get('user_session_token')
        else:
            user_token = user_token.replace('Bearer ', '')
        
        if not user_token:
            return jsonify({'error': 'Authentication required'}), 401
        
        user_session = user_session_manager.validate_session(user_token)
        if not user_session:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        data = request.get_json()
        if not data or 'current_password' not in data or 'new_password' not in data:
            return jsonify({'error': 'Current password and new password required'}), 400
        
        # Verify current password by attempting authentication
        user_data = user_manager.authenticate_user(
            user_session['email'], 
            data['current_password']
        )
        
        if not user_data:
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update password (would need to add this method to User model)
        # For now, return not implemented
        return jsonify({'error': 'Password change not yet implemented'}), 501
        
    except Exception as e:
        logger.error(f"Change password error: {e}")
        return jsonify({'error': 'Password change failed'}), 500

# Health check endpoint for auth system
@auth_bp.route('/health', methods=['GET'])
def auth_health():
    """Authentication system health check."""
    try:
        health_status = {
            'auth_system': True,
            'database': db_manager.health_check() if db_manager else False,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Auth health check error: {e}")
        return jsonify({
            'auth_system': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
