"""
Authentication and user management routes - extracted from monolithic app.py
Handles: login, registration, profile management, session handling
"""

import os
import json
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Global dependencies (will be injected during initialization)
db_manager = None
storage_manager = None
auth_middleware = None
cache_manager = None
credit_manager = None
railway_db = None
email_automation = None

def init_auth_routes(database_manager, storage_mgr, auth_mid, cache_mgr=None, 
                    credit_mgr=None, railway_database=None, email_auto=None):
    """Initialize auth routes with dependencies"""
    global db_manager, storage_manager, auth_middleware, cache_manager
    global credit_manager, railway_db, email_automation
    
    db_manager = database_manager
    storage_manager = storage_mgr
    auth_middleware = auth_mid
    cache_manager = cache_mgr
    credit_manager = credit_mgr
    railway_db = railway_database
    email_automation = email_auto
    
    logger.info("✅ Auth routes initialized with all dependencies")

@auth_bp.route('/register', methods=['POST'])
def register_user():
    """Register new user with enhanced validation and trial credits"""
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        required_fields = ['email', 'password', 'full_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        full_name = data['full_name'].strip()
        
        # Enhanced validation
        if not is_valid_email(email):
            return jsonify({
                "success": False,
                "error": "Invalid email format"
            }), 400
        
        if len(password) < 8:
            return jsonify({
                "success": False,
                "error": "Password must be at least 8 characters long"
            }), 400
        
        if len(full_name) < 2:
            return jsonify({
                "success": False,
                "error": "Full name must be at least 2 characters long"
            }), 400
        
        # Check if user already exists
        if not railway_db:
            return jsonify({"error": "Database not available"}), 500
        
        existing_user = railway_db.execute_read(
            "SELECT user_id FROM users WHERE email = %s", (email,)
        )
        
        if existing_user:
            return jsonify({
                "success": False,
                "error": "User with this email already exists"
            }), 409
        
        # Hash password
        password_hash = hash_password(password)
        
        # Generate user ID
        import uuid
        user_id = str(uuid.uuid4())
        
        # Create user record
        user_data = {
            'user_id': user_id,
            'email': email,
            'password_hash': password_hash,
            'full_name': full_name,
            'is_premium': False,
            'trial_credits_used': 0,
            'created_at': datetime.utcnow(),
            'last_login': datetime.utcnow(),
            'is_active': True,
            'email_verified': False,
            'subscription_plan': 'trial',
            'total_resumes_uploaded': 0,
            'total_ai_requests': 0
        }
        
        # Insert user into database
        insert_query = """
            INSERT INTO users (
                user_id, email, password_hash, full_name, is_premium, 
                trial_credits_used, created_at, last_login, is_active,
                email_verified, subscription_plan, total_resumes_uploaded, total_ai_requests
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        insert_params = (
            user_data['user_id'], user_data['email'], user_data['password_hash'],
            user_data['full_name'], user_data['is_premium'], user_data['trial_credits_used'],
            user_data['created_at'], user_data['last_login'], user_data['is_active'],
            user_data['email_verified'], user_data['subscription_plan'],
            user_data['total_resumes_uploaded'], user_data['total_ai_requests']
        )
        
        result = railway_db.execute_write(insert_query, insert_params)
        
        if not result:
            return jsonify({
                "success": False,
                "error": "Failed to create user account"
            }), 500
        
        # Initialize credit system for new user
        if credit_manager:
            try:
                credit_manager.initialize_user_credits(user_id)
                logger.info(f"✅ Credits initialized for new user: {user_id}")
            except Exception as credit_error:
                logger.warning(f"Failed to initialize credits for user {user_id}: {credit_error}")
        
        # Create session
        session_token = create_user_session(user_data)
        
        # Log user activity
        log_user_activity(user_id, 'user_registered', {
            'email': email,
            'registration_method': 'standard'
        })
        
        # Send welcome email (if email automation is available)
        if email_automation:
            try:
                email_automation.send_welcome_email(email, full_name)
            except Exception as email_error:
                logger.warning(f"Failed to send welcome email: {email_error}")
        
        # Prepare response
        response_data = {
            "success": True,
            "message": "User registered successfully",
            "user": {
                "user_id": user_id,
                "email": email,
                "full_name": full_name,
                "is_premium": False,
                "subscription_plan": "trial"
            },
            "session_token": session_token,
            "trial_info": {
                "trial_credits": 10,
                "features_included": [
                    "Resume Upload & Analysis",
                    "Basic AI Scoring",
                    "Job Matching",
                    "Email Support"
                ]
            }
        }
        
        # Add credit status if available
        if credit_manager:
            try:
                credit_status = credit_manager.check_user_credits(user_id)
                response_data["credit_status"] = {
                    "trial_credits": credit_status.trial_credits,
                    "credits_remaining": credit_status.credits_remaining
                }
            except Exception:
                pass  # Non-breaking
        
        return jsonify(response_data), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({
            "success": False,
            "error": "Registration failed"
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login_user():
    """Authenticate user and create session"""
    try:
        data = request.get_json() or {}
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                "success": False,
                "error": "Email and password are required"
            }), 400
        
        if not railway_db:
            return jsonify({"error": "Database not available"}), 500
        
        # Get user from database
        user_record = railway_db.execute_read("""
            SELECT user_id, email, password_hash, full_name, is_premium, 
                   trial_credits_used, is_active, email_verified, subscription_plan,
                   last_login, created_at
            FROM users 
            WHERE email = %s
        """, (email,))
        
        if not user_record:
            return jsonify({
                "success": False,
                "error": "Invalid email or password"
            }), 401
        
        user = user_record[0]
        
        # Check if account is active
        if not user.get('is_active', True):
            return jsonify({
                "success": False,
                "error": "Account is deactivated. Please contact support."
            }), 403
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            # Log failed login attempt
            log_user_activity(user['user_id'], 'login_failed', {
                'email': email,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            })
            
            return jsonify({
                "success": False,
                "error": "Invalid email or password"
            }), 401
        
        # Update last login
        railway_db.execute_write(
            "UPDATE users SET last_login = %s WHERE user_id = %s",
            (datetime.utcnow(), user['user_id'])
        )
        
        # Create session
        session_token = create_user_session(user)
        
        # Log successful login
        log_user_activity(user['user_id'], 'login_successful', {
            'email': email,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        })
        
        # Prepare user data for response
        user_data = {
            "user_id": user['user_id'],
            "email": user['email'],
            "full_name": user['full_name'],
            "is_premium": user.get('is_premium', False),
            "subscription_plan": user.get('subscription_plan', 'trial'),
            "email_verified": user.get('email_verified', False),
            "member_since": user.get('created_at').isoformat() if user.get('created_at') else None
        }
        
        response_data = {
            "success": True,
            "message": "Login successful",
            "user": user_data,
            "session_token": session_token
        }
        
        # Add credit status if available
        if credit_manager:
            try:
                credit_status = credit_manager.check_user_credits(user['user_id'])
                response_data["credit_status"] = {
                    "trial_credits": credit_status.trial_credits,
                    "premium_credits": credit_status.premium_credits,
                    "credits_remaining": credit_status.credits_remaining,
                    "total_used": credit_status.total_used,
                    "processing_tier": credit_status.processing_tier.value if credit_status.processing_tier else 'trial'
                }
                
                # Add trial completion status
                if credit_status.credits_remaining <= 0 and not user.get('is_premium'):
                    response_data["trial_completed"] = True
                    response_data["monetization_prompt"] = {
                        "message": "Your trial credits have been exhausted. Upgrade to continue using advanced features.",
                        "upgrade_options": [
                            {
                                "plan": "Professional",
                                "price_monthly": 2500,
                                "credits_included": 100
                            }
                        ]
                    }
                    
            except Exception as credit_error:
                logger.warning(f"Failed to get credit status for user {user['user_id']}: {credit_error}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            "success": False,
            "error": "Login failed"
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout_user():
    """Logout user and invalidate session"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
        
        user = auth_middleware.get_current_user()
        if user:
            # Log logout activity
            log_user_activity(user['user_id'], 'logout', {
                'ip_address': request.remote_addr
            })
        
        # Clear session
        session.clear()
        
        return jsonify({
            "success": True,
            "message": "Logged out successfully"
        })
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({
            "success": False,
            "error": "Logout failed"
        }), 500

@auth_bp.route('/profile', methods=['GET'])
def get_user_profile():
    """Get current user profile"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
        
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = user['user_id']
        
        # Get detailed user profile
        if not railway_db:
            return jsonify({"error": "Database not available"}), 500
        
        profile_data = railway_db.execute_read("""
            SELECT user_id, email, full_name, is_premium, subscription_plan,
                   email_verified, created_at, last_login, 
                   total_resumes_uploaded, total_ai_requests
            FROM users 
            WHERE user_id = %s
        """, (user_id,))
        
        if not profile_data:
            return jsonify({"error": "User profile not found"}), 404
        
        profile = profile_data[0]
        
        # Get recent activity
        recent_activity = railway_db.execute_read("""
            SELECT action, details, created_at
            FROM user_activity_log 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 5
        """, (user_id,))
        
        # Get resume statistics
        resume_stats = railway_db.execute_read("""
            SELECT 
                COUNT(*) as total_resumes,
                COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as processed_resumes,
                AVG(overall_score) as average_score
            FROM resumes 
            WHERE user_id = %s
        """, (user_id,))
        
        response_data = {
            "success": True,
            "profile": profile,
            "recent_activity": recent_activity or [],
            "resume_statistics": resume_stats[0] if resume_stats else {}
        }
        
        # Add credit information if available
        if credit_manager:
            try:
                credit_status = credit_manager.check_user_credits(user_id)
                response_data["credit_status"] = {
                    "trial_credits": credit_status.trial_credits,
                    "premium_credits": credit_status.premium_credits,
                    "credits_remaining": credit_status.credits_remaining,
                    "total_used": credit_status.total_used,
                    "processing_tier": credit_status.processing_tier.value if credit_status.processing_tier else 'trial'
                }
            except Exception as credit_error:
                logger.warning(f"Failed to get credit status: {credit_error}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        return jsonify({"error": "Failed to get profile"}), 500

@auth_bp.route('/profile', methods=['PUT'])
def update_user_profile():
    """Update user profile"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
        
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json() or {}
        user_id = user['user_id']
        
        # Fields that can be updated
        updatable_fields = ['full_name', 'email']
        updates = {}
        
        for field in updatable_fields:
            if field in data and data[field] is not None:
                value = data[field].strip() if isinstance(data[field], str) else data[field]
                if value:  # Only update non-empty values
                    updates[field] = value
        
        if not updates:
            return jsonify({
                "success": False,
                "error": "No valid fields to update"
            }), 400
        
        # Validate email if being updated
        if 'email' in updates:
            new_email = updates['email'].lower()
            if not is_valid_email(new_email):
                return jsonify({
                    "success": False,
                    "error": "Invalid email format"
                }), 400
            
            # Check if email is already taken
            existing_user = railway_db.execute_read(
                "SELECT user_id FROM users WHERE email = %s AND user_id != %s",
                (new_email, user_id)
            )
            
            if existing_user:
                return jsonify({
                    "success": False,
                    "error": "Email is already taken"
                }), 409
            
            updates['email'] = new_email
            updates['email_verified'] = False  # Reset verification status
        
        # Build update query
        set_clauses = []
        params = []
        
        for field, value in updates.items():
            set_clauses.append(f"{field} = %s")
            params.append(value)
        
        set_clauses.append("updated_at = %s")
        params.append(datetime.utcnow())
        params.append(user_id)
        
        update_query = f"""
            UPDATE users 
            SET {', '.join(set_clauses)}
            WHERE user_id = %s
        """
        
        result = railway_db.execute_write(update_query, params)
        
        if result:
            # Log profile update
            log_user_activity(user_id, 'profile_updated', {
                'fields_updated': list(updates.keys())
            })
            
            return jsonify({
                "success": True,
                "message": "Profile updated successfully",
                "updated_fields": list(updates.keys())
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to update profile"
            }), 500
            
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        return jsonify({
            "success": False,
            "error": "Profile update failed"
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
        
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json() or {}
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({
                "success": False,
                "error": "Current password and new password are required"
            }), 400
        
        if len(new_password) < 8:
            return jsonify({
                "success": False,
                "error": "New password must be at least 8 characters long"
            }), 400
        
        user_id = user['user_id']
        
        # Get current password hash
        user_data = railway_db.execute_read(
            "SELECT password_hash FROM users WHERE user_id = %s", (user_id,)
        )
        
        if not user_data:
            return jsonify({"error": "User not found"}), 404
        
        # Verify current password
        if not verify_password(current_password, user_data[0]['password_hash']):
            return jsonify({
                "success": False,
                "error": "Current password is incorrect"
            }), 401
        
        # Hash new password
        new_password_hash = hash_password(new_password)
        
        # Update password
        result = railway_db.execute_write(
            "UPDATE users SET password_hash = %s, updated_at = %s WHERE user_id = %s",
            (new_password_hash, datetime.utcnow(), user_id)
        )
        
        if result:
            # Log password change
            log_user_activity(user_id, 'password_changed', {
                'ip_address': request.remote_addr
            })
            
            return jsonify({
                "success": True,
                "message": "Password changed successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to change password"
            }), 500
            
    except Exception as e:
        logger.error(f"Change password error: {e}")
        return jsonify({
            "success": False,
            "error": "Password change failed"
        }), 500

# Helper functions

def is_valid_email(email):
    """Validate email format"""
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def hash_password(password):
    """Hash password using bcrypt"""
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except ImportError:
        # Fallback to hashlib if bcrypt is not available
        import hashlib
        salt = secrets.token_hex(32)
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex() + salt

def verify_password(password, password_hash):
    """Verify password against hash"""
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except ImportError:
        # Fallback verification
        import hashlib
        if len(password_hash) > 64:  # Assuming salt is 32 bytes = 64 hex chars
            salt = password_hash[-64:]
            stored_hash = password_hash[:-64]
            return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex() == stored_hash
        return False

def create_user_session(user_data):
    """Create user session and return session token"""
    try:
        session_token = secrets.token_urlsafe(32)
        
        # Store session data
        session['user_id'] = user_data['user_id']
        session['email'] = user_data['email']
        session['is_premium'] = user_data.get('is_premium', False)
        session['session_token'] = session_token
        session['created_at'] = datetime.utcnow().isoformat()
        
        # Cache session if cache manager is available
        if cache_manager:
            cache_manager.set(
                f"session:{session_token}",
                {
                    'user_id': user_data['user_id'],
                    'email': user_data['email'],
                    'is_premium': user_data.get('is_premium', False),
                    'created_at': datetime.utcnow().isoformat()
                },
                ttl=86400  # 24 hours
            )
        
        return session_token
        
    except Exception as e:
        logger.error(f"Session creation error: {e}")
        return None

def log_user_activity(user_id, action, details=None):
    """Log user activity"""
    try:
        if railway_db:
            railway_db.execute_write("""
                INSERT INTO user_activity_log (user_id, action, details, created_at)
                VALUES (%s, %s, %s, %s)
            """, (user_id, action, json.dumps(details) if details else None, datetime.utcnow()))
    except Exception as e:
        logger.warning(f"Failed to log user activity: {e}")
