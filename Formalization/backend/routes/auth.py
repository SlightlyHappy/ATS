"""
Bear Systems Resume Screening Tool - Authentication Routes
Handles user and admin login, session management, and user creation.
"""

from flask import Blueprint, request, jsonify, make_response
import logging

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Global variables for model instances (will be initialized by main app)
user_manager = None
user_session_manager = None
admin_user_manager = None
supabase_manager = None

def init_auth_routes(user_model, user_session_model, admin_user_model, supabase_model=None):
    """Initialize auth routes with model instances."""
    global user_manager, user_session_manager, admin_user_manager, supabase_manager
    user_manager = user_model
    user_session_manager = user_session_model
    admin_user_manager = admin_user_model
    supabase_manager = supabase_model

@auth_bp.route('/admin-login', methods=['POST'])
def admin_login():
    """Admin login endpoint."""
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
        
        # Create admin session
        session_token = admin_user_manager.create_admin_session(admin_data['id'])
        
        response_data = {
            'success': True,
            'message': 'Admin login successful',
            'token': session_token,  # Changed from session_token to token for consistency
            'user': {  # Frontend expects 'user' field
                'user_id': admin_data['id'],
                'username': admin_data['username'],
                'email': admin_data.get('email', admin_data['username']),
                'name': admin_data.get('name', admin_data['username']),
                'access_type': 'admin',
                'is_admin': True
            },
            'admin_info': {
                'id': admin_data['id'],
                'username': admin_data['username']
            }
        }
        
        # Set session token in cookie
        response = make_response(jsonify(response_data))
        response.set_cookie('session_token', session_token, httponly=True, secure=True, samesite='Strict')
        
        logger.info(f"Admin {data['username']} logged in successfully")
        return response
        
    except Exception as e:
        logger.error(f"Admin login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/create-user', methods=['POST'])
def create_user():
    """Admin endpoint to create new users - Supabase Primary with SQLite Sync."""
    from middleware.auth import require_admin_auth, get_current_admin
    
    @require_admin_auth
    def _create_user():
        try:
            data = request.get_json()
            
            required_fields = ['email', 'name', 'password']
            if not data or not all(field in data for field in required_fields):
                return jsonify({'error': 'Email, name, and password required'}), 400
            
            admin = get_current_admin()
            access_type = data.get('access_type', 'trial')
            
            # Step 1: Try to create user in Supabase first (Primary)
            supabase_success = False
            supabase_user_id = None
            
            if supabase_manager:
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    supabase_result = loop.run_until_complete(
                        supabase_manager.create_user(
                            email=data['email'],
                            password=data['password'],
                            full_name=data['name'],
                            access_type=access_type,
                            created_by_admin=admin['username']
                        )
                    )
                    
                    if supabase_result.get('success'):
                        supabase_success = True
                        supabase_user_id = supabase_result.get('user_id')
                        logger.info(f"✅ User created in Supabase: {data['email']}")
                    else:
                        logger.warning(f"⚠️  Supabase user creation failed: {supabase_result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"❌ Supabase user creation error: {e}")
            
            # Step 2: Create user in SQLite (for sync/backup)
            sqlite_success = False
            sqlite_user_id = None
            
            if user_manager:
                try:
                    sqlite_user_id = user_manager.create_user(
                        email=data['email'],
                        name=data['name'],
                        password=data['password'],
                        access_type=access_type,
                        created_by_admin=admin['username']
                    )
                    
                    if sqlite_user_id:
                        sqlite_success = True
                        logger.info(f"✅ User synced to SQLite: {data['email']}")
                    else:
                        logger.warning(f"⚠️  SQLite user creation failed (user may already exist)")
                        
                except Exception as e:
                    logger.error(f"❌ SQLite user creation error: {e}")
            
            # Step 3: Determine response based on results
            if supabase_success:
                # Primary success - Supabase user created
                response_data = {
                    'success': True,
                    'message': 'User created successfully in Supabase',
                    'user': {
                        'id': supabase_user_id,
                        'email': data['email'],
                        'name': data['name'],
                        'access_type': access_type,
                        'provider': 'supabase',
                        'synced_to_sqlite': sqlite_success
                    }
                }
                
                logger.info(f"✅ Admin {admin['username']} created user {data['email']} (Supabase Primary)")
                return jsonify(response_data), 201
                
            elif sqlite_success:
                # Fallback success - SQLite user created
                response_data = {
                    'success': True,
                    'message': 'User created successfully in local database (Supabase unavailable)',
                    'user': {
                        'id': sqlite_user_id,
                        'email': data['email'],
                        'name': data['name'],
                        'access_type': access_type,
                        'provider': 'sqlite',
                        'needs_supabase_sync': True
                    }
                }
                
                logger.info(f"⚠️  Admin {admin['username']} created user {data['email']} (SQLite Fallback)")
                return jsonify(response_data), 201
                
            else:
                # Both failed
                return jsonify({'error': 'User already exists or creation failed'}), 409
                
        except Exception as e:
            logger.error(f"User creation error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return _create_user()

@auth_bp.route('/user-login', methods=['POST'])
def user_login():
    """User login endpoint - Supabase Primary with SQLite Fallback."""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password required'}), 400
        
        # Step 1: Try Supabase authentication first (Primary)
        if supabase_manager:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                supabase_result = loop.run_until_complete(
                    supabase_manager.authenticate_user(data['email'], data['password'])
                )
                
                if supabase_result.get('success'):
                    user_data = supabase_result.get('user')
                    session = supabase_result.get('session')
                    
                    response_data = {
                        'success': True,
                        'message': 'Login successful',
                        'token': session.get('access_token'),
                        'user': {
                            'user_id': user_data.get('id'),
                            'id': user_data.get('id'),
                            'email': user_data.get('email'),
                            'name': user_data.get('name', user_data.get('full_name')),
                            'access_type': user_data.get('access_type', 'trial'),
                            'is_admin': user_data.get('access_type') == 'admin',
                            'provider': 'supabase'
                        },
                        'trial_status': {
                            'trial_resumes_analyzed': user_data.get('trial_resumes_analyzed', 0),
                            'trial_limit': user_data.get('trial_limit', 100)
                        }
                    }
                    
                    response = make_response(jsonify(response_data))
                    response.set_cookie('session_token', session.get('access_token'), 
                                      httponly=True, secure=True, samesite='Strict')
                    
                    logger.info(f"✅ User {data['email']} logged in via Supabase")
                    return response
                    
                else:
                    logger.info(f"⚠️  Supabase login failed for {data['email']}: {supabase_result.get('error')}")
                    
            except Exception as e:
                logger.error(f"❌ Supabase authentication error: {e}")
        
        # Step 2: Fallback to SQLite authentication
        if not user_manager or not user_session_manager:
            return jsonify({'error': 'Authentication not available'}), 500
        
        # Authenticate user with SQLite
        user_data = user_manager.authenticate_user(
            data['email'], 
            data['password']
        )
        
        if not user_data:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create user session
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        session_token = user_session_manager.create_session(
            user_id=user_data['id'],
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Get trial status
        trial_status = user_manager.check_trial_limit(user_data['id'])
        
        response_data = {
            'success': True,
            'message': 'Login successful (local database)',
            'token': session_token,
            'user': {
                'user_id': user_data['id'],
                'id': user_data['id'],
                'email': user_data['email'],
                'name': user_data['name'],
                'access_type': user_data['access_type'],
                'is_admin': False,
                'provider': 'sqlite',
                'needs_supabase_sync': True
            },
            'trial_status': trial_status
        }
        
        # Set session token in cookie
        response = make_response(jsonify(response_data))
        response.set_cookie('session_token', session_token, httponly=True, secure=True, samesite='Strict')
        
        logger.info(f"⚠️  User {data['email']} logged in via SQLite fallback")
        return response
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
        
        logger.info(f"User {data['email']} logged in successfully")
        return response
        
    except Exception as e:
        logger.error(f"User login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/session', methods=['GET'])
def validate_session():
    """Validate current session and return user data (handles both admin and user sessions)."""
    from middleware.auth import get_session_token
    
    try:
        session_token = get_session_token()
        
        if not session_token:
            return jsonify({'error': 'No authentication token provided'}), 401
        
        # Try admin session first
        if admin_user_manager:
            admin_data = admin_user_manager.validate_admin_session(session_token)
            if admin_data:
                response_data = {
                    'valid': True,
                    'user': {
                        'user_id': admin_data['id'],
                        'id': admin_data['id'],
                        'email': admin_data.get('email', admin_data['username']),
                        'name': admin_data.get('name', admin_data['username']),
                        'username': admin_data['username'],
                        'access_type': 'admin',
                        'is_admin': True
                    },
                    'trial_status': None  # Admins don't have trial limits
                }
                
                return jsonify(response_data)
        
        # Try user session
        if user_session_manager:
            user_data = user_session_manager.validate_session(session_token)
            if user_data:
                if not user_manager:
                    return jsonify({'error': 'User management not available'}), 500
                
                # Get updated trial status
                trial_status = user_manager.check_trial_limit(user_data['user_id'])
                
                response_data = {
                    'valid': True,
                    'user': {
                        'user_id': user_data['user_id'],
                        'id': user_data['user_id'],
                        'email': user_data['email'],
                        'name': user_data['name'],
                        'access_type': user_data['access_type'],
                        'is_admin': False
                    },
                    'trial_status': trial_status
                }
                
                return jsonify(response_data)
        
        # No valid session found
        return jsonify({'error': 'Invalid or expired session'}), 401
        
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout endpoint."""
    from middleware.auth import get_session_token
    
    try:
        session_token = get_session_token()
        
        if session_token and user_session_manager:
            success = user_session_manager.delete_session(session_token)
            
            if success:
                response = make_response(jsonify({'message': 'Logout successful'}))
                response.delete_cookie('session_token')
                return response
            else:
                return jsonify({'error': 'Session not found'}), 404
        else:
            return jsonify({'error': 'No active session'}), 400
            
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/admin-logout', methods=['POST'])
def admin_logout():
    """Admin logout endpoint."""
    from middleware.auth import get_session_token
    
    try:
        session_token = get_session_token()
        
        if session_token and admin_user_manager:
            # For admin logout, we need to delete from admin_sessions table
            # This would require adding a delete_admin_session method
            response = make_response(jsonify({'message': 'Admin logout successful'}))
            response.delete_cookie('session_token')
            return response
        else:
            return jsonify({'error': 'No active admin session'}), 400
            
    except Exception as e:
        logger.error(f"Admin logout error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """Get user profile information."""
    from middleware.auth import require_auth, get_current_user
    
    @require_auth
    def _get_profile():
        try:
            user = get_current_user()
            
            if not user_manager:
                return jsonify({'error': 'User management not available'}), 500
            
            # Get full user data
            user_data = user_manager.get_user_by_id(user['user_id'])
            
            if not user_data:
                return jsonify({'error': 'User not found'}), 404
            
            # Get trial status
            trial_status = user_manager.check_trial_limit(user['user_id'])
            
            response_data = {
                'user': {
                    'id': user_data['id'],
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'access_type': user_data['access_type'],
                    'created_at': user_data['created_at'],
                    'last_login': user_data['last_login']
                },
                'trial_status': trial_status
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Profile retrieval error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return _get_profile()

@auth_bp.route('/users', methods=['GET'])
def get_all_users():
    """Admin endpoint to get all users."""
    from middleware.auth import require_admin_auth
    
    @require_admin_auth
    def _get_all_users():
        try:
            if not user_manager:
                return jsonify({'error': 'User management not available'}), 500
            
            users = user_manager.get_all_users()
            
            response_data = {
                'users': users,
                'total_count': len(users)
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Get all users error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return _get_all_users()
