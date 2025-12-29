"""
Authentication API endpoints.
Handles user registration, login, logout, and token management.
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import logging
from app import db
from app.models import User
from app.models.admin import AdminUser
from app.services.auth_manager import auth_manager, session_manager, get_current_user, require_auth
from app.services.error_handler import ValidationError, AuthenticationError

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

@auth_bp.route('/register', methods=['POST'])
def register_user():
    """Register a new user account."""
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required")
        
        # Validate required fields
        required_fields = ['email', 'password']
        for field in required_fields:
            if not data.get(field):
                raise ValidationError(f"{field} is required")
        
        email = data['email'].lower().strip()
        password = data['password']
        username = data.get('username', email.split('@')[0])
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            raise ValidationError("User with this email already exists")
        
        # Validate password strength
        password_errors = auth_manager.validate_password_strength(password)
        if password_errors:
            raise ValidationError(f"Password validation failed: {', '.join(password_errors)}")
        
        # Create new user
        user = User(
            email=email,
            username=username,
            password_hash=auth_manager.hash_password(password),
            first_name=first_name,
            last_name=last_name,
            is_admin=False,
            is_active=True,
            credits_balance=10  # Default free credits
        )
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {email}")
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': str(user.id),
            'credits_balance': user.credits_balance
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login_user():
    """Authenticate user and return JWT tokens."""
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required")
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not email or not password:
            raise ValidationError("Email and password are required")
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            auth_manager.record_failed_login(email)
            raise AuthenticationError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")
        
        # Verify password
        if not auth_manager.verify_password(password, user.password_hash):
            auth_manager.record_failed_login(email)
            raise AuthenticationError("Invalid email or password")
        
        # Generate JWT tokens
        tokens = auth_manager.generate_tokens(user)
        
        # Create session
        session_manager.create_session(user)
        
        # Get user profile data
        user_data = {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_admin': user.is_admin,
            'credits_balance': user.credits_balance,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
        
        # Add admin profile if user is admin
        if user.is_admin:
            admin_profile = AdminUser.query.filter_by(user_id=user.id).first()
            if admin_profile:
                user_data['admin_profile'] = {
                    'role': admin_profile.role,
                    'access_level': admin_profile.access_level,
                    'permissions': admin_profile.get_dashboard_permissions()
                }
        
        logger.info(f"User logged in: {email}")
        
        return jsonify({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'token_type': 'Bearer',
            'expires_in': 86400,  # 24 hours
            'user': user_data
        }), 200
        
    except (ValidationError, AuthenticationError) as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token using refresh token."""
    try:
        data = request.get_json()
        
        if not data or not data.get('refresh_token'):
            raise ValidationError("Refresh token is required")
        
        refresh_token_value = data['refresh_token']
        
        # Generate new tokens
        tokens = auth_manager.refresh_access_token(refresh_token_value)
        
        # tokens is a dict from generate_tokens with keys: access_token, refresh_token, token_type, expires_in
        return jsonify({
            'access_token': tokens.get('access_token'),
            'refresh_token': tokens.get('refresh_token', refresh_token_value),
            'token_type': tokens.get('token_type', 'Bearer'),
            'expires_in': tokens.get('expires_in', 86400)
        }), 200
        
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except AuthenticationError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'error': 'Token refresh failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout_user():
    """Logout user and invalidate tokens."""
    try:
        user = get_current_user()
        
        if user:
            session_manager.end_session(user)
            logger.info(f"User logged out: {user.email}")
        
        return jsonify({
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user_info():
    """Get current user information."""
    try:
        user = get_current_user()
        
        if not user:
            raise AuthenticationError("User not found")
        
        user_data = {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_admin': user.is_admin,
            'credits_balance': user.credits_balance,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
        
        # Add admin profile if user is admin
        if user.is_admin:
            admin_profile = AdminUser.query.filter_by(user_id=user.id).first()
            if admin_profile:
                user_data['admin_profile'] = {
                    'role': admin_profile.role,
                    'access_level': admin_profile.access_level,
                    'permissions': admin_profile.get_dashboard_permissions()
                }
        
        return jsonify(user_data), 200
        
    except AuthenticationError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logger.error(f"Get user info error: {str(e)}")
        return jsonify({'error': 'Failed to get user info'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change user password."""
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required")
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            raise ValidationError("Current password and new password are required")
        
        # Verify current password
        if not auth_manager.verify_password(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")
        
        # Validate new password strength
        password_errors = auth_manager.validate_password_strength(new_password)
        if password_errors:
            raise ValidationError(f"New password validation failed: {', '.join(password_errors)}")
        
        # Update password
        user.password_hash = auth_manager.hash_password(new_password)
        db.session.commit()
        
        logger.info(f"Password changed for user: {user.email}")
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except (ValidationError, AuthenticationError) as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Password change failed'}), 500
