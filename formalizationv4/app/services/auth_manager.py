"""
Production-ready authentication and session management system.
Implements JWT tokens, password hashing, and session validation.
"""
import jwt
import bcrypt
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app, g
import uuid
import os
from app.services.error_handler import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)

class AuthenticationManager:
    """Manages user authentication, tokens, and sessions."""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize authentication for Flask app."""
        # Set default configuration
        app.config.setdefault('JWT_SECRET_KEY', os.getenv('JWT_SECRET_KEY', self.generate_secret_key()))
        app.config.setdefault('JWT_EXPIRATION_HOURS', 24)
        app.config.setdefault('JWT_REFRESH_EXPIRATION_DAYS', 30)
        app.config.setdefault('PASSWORD_MIN_LENGTH', 8)
        app.config.setdefault('SESSION_TIMEOUT_MINUTES', 480)  # 8 hours
        
        # Add authentication middleware
        app.before_request(self.authenticate_request)
    
    def generate_secret_key(self):
        """Generate a secure secret key for JWT tokens."""
        return os.urandom(32).hex()
    
    def hash_password(self, password):
        """Hash password using bcrypt."""
        if len(password) < current_app.config['PASSWORD_MIN_LENGTH']:
            raise AuthenticationError(
                f"Password must be at least {current_app.config['PASSWORD_MIN_LENGTH']} characters long"
            )
        
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password, hashed_password):
        """Verify password against hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False
    
    def generate_tokens(self, user):
        """Generate JWT access and refresh tokens for user."""
        now = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            'user_id': str(user.id),
            'email': user.email,
            'is_admin': user.is_admin,
            'iat': now,
            'exp': now + timedelta(hours=current_app.config['JWT_EXPIRATION_HOURS']),
            'type': 'access'
        }
        
        # Refresh token payload
        refresh_payload = {
            'user_id': str(user.id),
            'iat': now,
            'exp': now + timedelta(days=current_app.config['JWT_REFRESH_EXPIRATION_DAYS']),
            'type': 'refresh'
        }
        
        try:
            access_token = jwt.encode(
                access_payload,
                current_app.config['JWT_SECRET_KEY'],
                algorithm='HS256'
            )
            
            refresh_token = jwt.encode(
                refresh_payload,
                current_app.config['JWT_SECRET_KEY'],
                algorithm='HS256'
            )
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': current_app.config['JWT_EXPIRATION_HOURS'] * 3600
            }
            
        except Exception as e:
            raise AuthenticationError(f"Token generation failed: {str(e)}")
    
    def verify_token(self, token):
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
    
    def refresh_access_token(self, refresh_token):
        """Generate new access token using refresh token."""
        payload = self.verify_token(refresh_token)
        
        if payload.get('type') != 'refresh':
            raise AuthenticationError("Invalid token type for refresh")
        
        # Get user from database
        from app.models import User
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        
        # Generate new access token
        return self.generate_tokens(user)
    
    def authenticate_request(self):
        """Authenticate incoming request."""
        # Skip authentication for certain endpoints
        exempt_endpoints = [
            'api.health_check',
            'api.simple_health_check', 
            'api.database_health',
            'api.ollama_health',
            'api.agents_health',
            'api.register_user',
            'api.login_user',
            'auth.register_user',           # Auth blueprint endpoints
            'auth.login_user',
            'monitoring.get_monitoring_status',      # Public monitoring status
            'monitoring.get_basic_metrics',          # Public basic metrics  
            'monitoring.monitoring_health',          # Public health check
            'websocket.get_system_stats'             # Public stats
        ]
        
        # Also check for URL patterns that should be exempt
        exempt_paths = [
            '/api/v1/auth/login',
            '/api/v1/auth/register', 
            '/api/v1/monitoring/status',
            '/api/v1/monitoring/metrics',
            '/api/v1/monitoring/health',
            '/health',
            '/'
        ]
        
        if request.endpoint in exempt_endpoints or request.path in exempt_paths:
            return
        
        # Extract token from request
        try:
            token = self.extract_token_from_request()
            if not token:
                # No token provided - let decorators handle this
                g.auth_error = "No authentication token provided"
                return
            
            payload = self.verify_token(token)
            
            # Load user into request context with error handling
            try:
                from app.models import User
                user = User.query.get(payload['user_id'])
                if not user or not user.is_active:
                    g.auth_error = "User not found or inactive"
                    return
                
                # Check for account security issues
                self._check_account_security(user)
                
                g.current_user = user
                g.current_user_id = str(user.id)
                g.auth_error = None  # Clear any auth errors
                
                # Update last activity for session management
                self.update_user_activity(user)
                
            except Exception as db_error:
                # Log database/model errors
                logger.error(f"Database error during authentication: {str(db_error)}")
                g.auth_error = "Authentication database error"
                
        except AuthenticationError as auth_error:
            # Set authentication error for decorators to handle
            g.auth_error = str(auth_error)
            logger.warning(f"Authentication failed: {str(auth_error)}")
        except Exception as e:
            # Log unexpected authentication errors
            logger.error(f"Unexpected error in authenticate_request: {str(e)}")
            g.auth_error = "Authentication system error"
    
    def _check_account_security(self, user):
        """Check for account security issues."""
        # Check for suspicious login patterns
        if hasattr(user, 'failed_login_attempts') and user.failed_login_attempts >= 5:
            # Check if account should be temporarily locked
            if hasattr(user, 'last_failed_login') and user.last_failed_login:
                time_since_last_failure = datetime.utcnow() - user.last_failed_login
                if time_since_last_failure.seconds < 300:  # 5 minutes
                    raise AuthenticationError("Account temporarily locked due to multiple failed attempts")
        
        # Reset failed attempts on successful auth
        if hasattr(user, 'failed_login_attempts'):
            user.failed_login_attempts = 0
    
    def record_failed_login(self, identifier):
        """Record failed login attempt and write to access logs."""
        try:
            from app.models import User
            from app.models.api_management import AccessLog
            user = User.query.filter(
                (User.email == identifier) | (User.username == identifier)
            ).first()
            user_email = identifier
            user_name = None
            if user:
                if not hasattr(user, 'failed_login_attempts'):
                    user.failed_login_attempts = 0
                user.failed_login_attempts += 1
                user.last_failed_login = datetime.utcnow()
                user_email = user.email
                user_name = f"{user.first_name} {user.last_name}".strip()
                from app import db as _db
                _db.session.commit()
            # write access log
            try:
                from app import db as _db
                log = AccessLog(
                    user_email=user_email,
                    user_name=user_name,
                    action='Failed Login',
                    ip_address=request.remote_addr if request else None,
                    success=False
                )
                _db.session.add(log)
                _db.session.commit()
                # emit websocket event if available
                try:
                    from app.services.websocket_service import websocket_service
                    if websocket_service:
                        websocket_service.socketio.emit('access_log_created', log.to_dict(), room='admin_dashboard')
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Failed to write access log: {e}")
        except Exception as e:
            from app import db as _db
            _db.session.rollback()
            logger.error(f"Error recording failed login: {str(e)}")
    
    def validate_password_strength(self, password):
        """Validate password meets security requirements."""
        errors = []
        
        if len(password) < current_app.config.get('PASSWORD_MIN_LENGTH', 8):
            errors.append(f"Password must be at least {current_app.config.get('PASSWORD_MIN_LENGTH', 8)} characters long")
        
        # Check for uppercase letter
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for lowercase letter
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check for digit
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        # Check for special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            errors.append("Password must contain at least one special character")
        
        return errors
    
    def extract_token_from_request(self):
        """Extract JWT token from request headers."""
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Also check for API key in headers (for external integrations)
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return self.validate_api_key(api_key)
        
        return None
    
    def validate_api_key(self, api_key):
        """Validate API key and return corresponding JWT token or user context.
        On success, returns a dict with user_id. On failure, returns None.
        """
        try:
            from app.models.api_management import ApiKey
            from app.models import User
            key_hash = ApiKey.hash_key(api_key)
            record = ApiKey.query.filter_by(key_hash=key_hash, status='active').first()
            if not record:
                return None
            # expiration
            if record.expires_at and record.expires_at < datetime.utcnow():
                record.status = 'expired'
                from app import db as _db
                _db.session.commit()
                return None
            # simple rate limit counter (per-day reset handled elsewhere)
            record.requests_today = (record.requests_today or 0) + 1
            record.last_used = datetime.utcnow()
            from app import db as _db
            _db.session.commit()
            # Attach user to context for middleware
            user = User.query.get(record.user_id)
            if user and user.is_active:
                return self.generate_tokens(user)['access_token']
            return None
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return None
    
    def update_user_activity(self, user):
        """Update user's last activity timestamp."""
        try:
            user.last_login = datetime.utcnow()
            from app import db
            db.session.commit()
        except Exception:
            # Don't fail the request if activity update fails
            pass
    
    def generate_api_key(self, user):
        """Generate API key for user."""
        api_key = f"ak_{uuid.uuid4().hex}"
        
        # Store API key in database (you'd need to create an ApiKey model)
        # For now, just return the key
        return api_key

def get_current_user():
    """Get current authenticated user from request context."""
    if not hasattr(g, 'current_user'):
        return None
    return g.current_user

def require_auth(f):
    """Decorator to require authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check if authentication failed
            if hasattr(g, 'auth_error') and g.auth_error:
                raise AuthenticationError(g.auth_error)
            
            # Check if user is available
            if not hasattr(g, 'current_user') or g.current_user is None:
                raise AuthenticationError("Authentication required")
                
            return f(*args, **kwargs)
        except AuthenticationError:
            # Re-raise authentication errors
            raise
        except Exception as e:
            # Log unexpected errors in auth decorator
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error in require_auth decorator: {str(e)}")
            # Convert to authentication error to avoid 500
            raise AuthenticationError("Authentication failed")
    return decorated_function

def require_admin(f):
    """Decorator to require admin privileges for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check if authentication failed
            if hasattr(g, 'auth_error') and g.auth_error:
                raise AuthenticationError(g.auth_error)
            
            # Check if user is available
            if not hasattr(g, 'current_user') or g.current_user is None:
                raise AuthenticationError("Authentication required")
            
            # Check admin privileges
            if not g.current_user.is_admin:
                raise AuthorizationError("Admin privileges required")
            
            return f(*args, **kwargs)
        except (AuthenticationError, AuthorizationError):
            # Re-raise auth/authz errors
            raise
        except Exception as e:
            # Log unexpected errors in auth decorator
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error in require_admin decorator: {str(e)}")
            # Convert to authentication error to avoid 500
            raise AuthenticationError("Authentication failed")
    return decorated_function

def require_credits(credits_required=1):
    """Decorator to require sufficient credits for a route."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                raise AuthenticationError("Authentication required")
            
            if not g.current_user.has_sufficient_credits(credits_required):
                raise AuthorizationError(
                    f"Insufficient credits. Required: {credits_required}, Available: {g.current_user.credits_balance}"
                )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class SessionManager:
    """Manages user sessions and activity tracking."""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize session management."""
        pass
    
    def create_session(self, user, login_info=None):
        """Create new user session and write access log."""
        from app.models import AdminUser
        from app.models.api_management import AccessLog
        # Update user login info
        user.last_login = datetime.utcnow()
        # If user is admin, update admin profile
        if user.is_admin:
            admin_profile = AdminUser.query.filter_by(user_id=user.id).first()
            if admin_profile:
                admin_profile.update_login_info(
                    success=True,
                    ip_address=request.remote_addr if request else None
                )
        from app import db as _db
        _db.session.commit()
        # access log
        try:
            log = AccessLog(
                user_email=user.email,
                user_name=f"{user.first_name} {user.last_name}".strip(),
                action='Login',
                ip_address=request.remote_addr if request else None,
                success=True
            )
            _db.session.add(log)
            _db.session.commit()
            try:
                from app.services.websocket_service import websocket_service
                if websocket_service:
                    websocket_service.socketio.emit('access_log_created', log.to_dict(), room='admin_dashboard')
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Failed to write login access log: {e}")

    def end_session(self, user):
        """End user session and write access log."""
        # Update last activity
        if hasattr(user, 'last_activity'):
            user.last_activity = datetime.utcnow()
            from app import db as _db
            _db.session.commit()
        # access log
        try:
            from app.models.api_management import AccessLog
            from app import db as _db
            log = AccessLog(
                user_email=user.email,
                user_name=f"{user.first_name} {user.last_name}".strip(),
                action='Logout',
                ip_address=request.remote_addr if request else None,
                success=True
            )
            _db.session.add(log)
            _db.session.commit()
            try:
                from app.services.websocket_service import websocket_service
                if websocket_service:
                    websocket_service.socketio.emit('access_log_created', log.to_dict(), room='admin_dashboard')
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Failed to write logout access log: {e}")
    
    def is_session_valid(self, user):
        """Check if user session is still valid."""
        if not hasattr(user, 'last_login') or not user.last_login:
            return False
        
        timeout_minutes = current_app.config.get('SESSION_TIMEOUT_MINUTES', 480)
        session_expiry = user.last_login + timedelta(minutes=timeout_minutes)
        
        return datetime.utcnow() < session_expiry

# Global instances
auth_manager = AuthenticationManager()
session_manager = SessionManager()
