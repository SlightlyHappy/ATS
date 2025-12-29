"""
User Routes for HR ATS System
Implements native user endpoints to replace frontend fallback system
Provides secure, user-scoped access to dashboard, resumes, profile, and analytics
"""

import os
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import json
from functools import wraps
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# Create user blueprint
user_bp = Blueprint('user', __name__, url_prefix='/api/user')

# Global instances (initialized by main app)
db_manager = None
railway_db = None
auth_middleware = None
storage_manager = None
credit_manager = None

# Unified AI processor (replaces fragmented AI systems)
unified_ai_processor = None

def init_user_routes(database_manager, railway_database, auth_mid, storage_mgr, credit_mgr):
    """Initialize user routes with required dependencies."""
    global db_manager, railway_db, auth_middleware, storage_manager, credit_manager
    global unified_ai_processor
    
    db_manager = database_manager
    railway_db = railway_database
    auth_middleware = auth_mid
    storage_manager = storage_mgr
    credit_manager = credit_mgr
    
    # Initialize unified AI processor
    try:
        from utils.unified_ai_processor import get_unified_processor
        unified_ai_processor = get_unified_processor(railway_db, None)  # Cache manager can be added later
        logger.info("✅ Unified AI processing system initialized")
    except ImportError as e:
        logger.error(f"Failed to initialize unified AI processor: {e}")
        unified_ai_processor = None
    
    logger.info("User routes initialized successfully with unified AI processing")

def require_user_auth(f):
    """Decorator to require user authentication and set user context"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check for session token in cookies (primary method)
            session_token = request.cookies.get('user_session_token')
            
            if not session_token:
                # Fallback to Authorization header
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    session_token = auth_header.split(' ')[1]
            
            if not session_token:
                return jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                }), 401
            
            # Validate session using auth middleware
            if not auth_middleware or not hasattr(auth_middleware, 'user_session_manager'):
                return jsonify({
                    'success': False,
                    'error': 'Authentication service unavailable',
                    'code': 'AUTH_SERVICE_ERROR'
                }), 500
            
            user_session = auth_middleware.user_session_manager.validate_session(session_token)
            if not user_session:
                return jsonify({
                    'success': False,
                    'error': 'Invalid or expired session',
                    'code': 'INVALID_SESSION'
                }), 401
            
            # Ensure this is a regular user, not admin
            if user_session.get('access_type') == 'admin':
                return jsonify({
                    'success': False,
                    'error': 'Admin accounts must use admin endpoints',
                    'code': 'ADMIN_ACCOUNT_DETECTED'
                }), 403
            
            # Set user context for the request
            request.user = user_session
            g.current_user = user_session
            
            # Log user activity for security and analytics
            _log_user_activity(
                user_id=user_session['user_id'],
                action=f"{request.method} {request.endpoint}",
                category="api_access",
                details={
                    'endpoint': request.endpoint,
                    'method': request.method,
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')[:200],
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"User authentication error: {e}")
            return jsonify({
                'success': False,
                'error': 'Authentication failed',
                'code': 'AUTH_ERROR'
            }), 401
            
    return decorated_function

def _log_user_activity(user_id: str, action: str, category: str, details: Dict[str, Any], status: str = 'success'):
    """Log user activity for security and analytics tracking"""
    try:
        if not railway_db:
            return
        
        activity_data = {
            'user_id': user_id,
            'action': action,
            'category': category,
            'details': json.dumps(details),
            'metadata': json.dumps({
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')[:200],
                'timestamp': datetime.utcnow().isoformat()
            }),
            'status': status,
            'created_at': datetime.utcnow()
        }
        
        # Insert activity log into Railway PostgreSQL
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_activity_detailed 
                    (user_id, action, category, details, metadata, status, created_at)
                    VALUES (%(user_id)s, %(action)s, %(category)s, %(details)s, %(metadata)s, %(status)s, %(created_at)s)
                """, activity_data)
                conn.commit()
                
    except Exception as e:
        logger.error(f"Failed to log user activity: {e}")

def _get_standardized_response(success: bool, data: Any = None, message: str = None, error: str = None, code: str = None) -> Dict[str, Any]:
    """Generate standardized API response format"""
    response = {
        'success': success,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if success:
        if data is not None:
            response['data'] = data
        if message:
            response['message'] = message
    else:
        if error:
            response['error'] = error
        if code:
            response['code'] = code
    
    return response

@user_bp.route('/dashboard-stats', methods=['GET'])
@require_user_auth
def get_dashboard_stats():
    """Get user dashboard statistics with caching for performance"""
    try:
        user_id = request.user['user_id']
        
        # Query user-specific resume statistics from Railway PostgreSQL
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get resume statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_resumes,
                        COUNT(*) FILTER (WHERE processing_status = 'pending') as pending_analysis,
                        COUNT(*) FILTER (WHERE processing_status = 'processing') as processing_analysis,
                        COUNT(*) FILTER (WHERE processing_status = 'completed') as completed_analysis,
                        COUNT(*) FILTER (WHERE processing_status = 'failed') as failed_analysis,
                        AVG(CASE WHEN overall_score IS NOT NULL THEN overall_score ELSE NULL END) as average_score,
                        COUNT(*) FILTER (WHERE upload_date >= NOW() - INTERVAL '7 days') as recent_uploads,
                        COUNT(*) FILTER (WHERE upload_date >= NOW() - INTERVAL '30 days') as monthly_uploads
                    FROM resumes 
                    WHERE user_id = %s
                """, (user_id,))
                
                stats_row = cursor.fetchone()
                
                # Get recent activity
                cursor.execute("""
                    SELECT action, details, created_at, status
                    FROM user_activity_detailed 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT 10
                """, (user_id,))
                
                recent_activity = []
                for row in cursor.fetchall():
                    activity = {
                        'action': row[0],
                        'timestamp': row[2].isoformat() if row[2] else None,
                        'status': row[3],
                        'details': json.loads(row[1]) if row[1] else {}
                    }
                    recent_activity.append(activity)
                
                # Get score progression (last 30 days)
                cursor.execute("""
                    SELECT 
                        DATE(upload_date) as date,
                        AVG(overall_score) as avg_score,
                        COUNT(*) as resumes_count
                    FROM resumes 
                    WHERE user_id = %s 
                        AND upload_date >= NOW() - INTERVAL '30 days'
                        AND overall_score IS NOT NULL
                    GROUP BY DATE(upload_date)
                    ORDER BY date ASC
                """, (user_id,))
                
                score_progression = []
                for row in cursor.fetchall():
                    score_progression.append({
                        'date': row[0].isoformat() if row[0] else None,
                        'score': float(row[1]) if row[1] else 0,
                        'resumes_count': row[2]
                    })
                
                # Get processing performance metrics
                cursor.execute("""
                    SELECT 
                        AVG(ai_processing_time) as avg_processing_time_ms,
                        COUNT(*) FILTER (WHERE processing_status = 'completed') as success_count,
                        COUNT(*) as total_processed
                    FROM resumes 
                    WHERE user_id = %s 
                        AND ai_processing_time IS NOT NULL
                        AND upload_date >= NOW() - INTERVAL '30 days'
                """, (user_id,))
                
                perf_row = cursor.fetchone()
                avg_processing_time_ms = perf_row[0] if perf_row[0] else 0
                success_count = perf_row[1] if perf_row[1] else 0
                total_processed = perf_row[2] if perf_row[2] else 0
        
        # Get trial/credit information
        trial_info = {}
        if credit_manager:
            try:
                credit_data = credit_manager.get_user_credits(user_id)
                trial_info = {
                    'is_trial': credit_data.get('is_trial', True),
                    'credits_used': credit_data.get('used_credits', 0),
                    'credits_remaining': credit_data.get('remaining_credits', 0),
                    'resets_at': credit_data.get('resets_at'),
                    'plan_type': credit_data.get('plan_type', 'trial')
                }
            except Exception as e:
                logger.warning(f"Could not fetch credit info for user {user_id}: {e}")
                trial_info = {
                    'is_trial': True,
                    'credits_used': 0,
                    'credits_remaining': 50,
                    'plan_type': 'trial'
                }
        
        # Calculate score trend
        score_trend = "0%"
        if len(score_progression) >= 2:
            latest_score = score_progression[-1]['score']
            previous_score = score_progression[-2]['score']
            if previous_score > 0:
                trend_percent = ((latest_score - previous_score) / previous_score) * 100
                score_trend = f"{trend_percent:+.1f}%"
        
        # Format response data
        dashboard_data = {
            'stats': {
                'total_resumes': stats_row[0] or 0,
                'pending_analysis': stats_row[1] or 0,
                'processing_analysis': stats_row[2] or 0,
                'completed_analysis': stats_row[3] or 0,
                'failed_analysis': stats_row[4] or 0,
                'average_score': round(float(stats_row[5] or 0), 1),
                'recent_uploads': stats_row[6] or 0,
                'monthly_uploads': stats_row[7] or 0,
                'score_trend': score_trend
            },
            'recent_activity': recent_activity,
            'score_progression': score_progression,
            'trial_info': trial_info,
            'quick_stats': {
                'this_week_uploads': stats_row[6] or 0,
                'avg_processing_time': f"{round(avg_processing_time_ms / 1000 / 60, 1)} minutes" if avg_processing_time_ms > 0 else "N/A",
                'success_rate': f"{round((success_count / total_processed) * 100, 1)}%" if total_processed > 0 else "N/A"
            }
        }
        
        return jsonify(_get_standardized_response(
            success=True,
            data=dashboard_data,
            message="Dashboard statistics retrieved successfully"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats for user {request.user.get('user_id', 'unknown')}: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error="Failed to retrieve dashboard statistics",
            code="DASHBOARD_ERROR"
        )), 500

@user_bp.route('/my-resumes', methods=['GET'])
@require_user_auth
def get_my_resumes():
    """Get user's resumes with advanced filtering and pagination"""
    try:
        user_id = request.user['user_id']
        
        # Parse query parameters with validation
        page = max(1, int(request.args.get('page', 1)))
        limit = min(max(1, int(request.args.get('limit', 20))), 100)  # Limit between 1-100
        status = request.args.get('status')
        search = request.args.get('search', '').strip()
        sort_field = request.args.get('sort', 'upload_date')
        sort_order = request.args.get('order', 'desc').lower()
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        min_score = request.args.get('min_score', type=float)
        max_score = request.args.get('max_score', type=float)
        
        # Validate sort parameters
        allowed_sorts = ['upload_date', 'filename', 'overall_score', 'processing_status', 'candidate_name']
        if sort_field not in allowed_sorts:
            sort_field = 'upload_date'
        
        if sort_order not in ['asc', 'desc']:
            sort_order = 'desc'
        
        # Build dynamic query with proper security (user isolation)
        base_query = """
            SELECT 
                id, filename, file_path, candidate_name, upload_date,
                processing_status, overall_score, skills_extracted,
                file_size, created_at, updated_at
            FROM resumes 
            WHERE user_id = %s
        """
        
        params = [user_id]
        
        # Add filters
        if status and status in ['pending', 'processing', 'completed', 'failed']:
            base_query += " AND processing_status = %s"
            params.append(status)
        
        if search:
            base_query += " AND (filename ILIKE %s OR candidate_name ILIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        if date_from:
            try:
                datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                base_query += " AND upload_date >= %s"
                params.append(date_from)
            except ValueError:
                pass  # Ignore invalid date format
        
        if date_to:
            try:
                datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                base_query += " AND upload_date <= %s"
                params.append(date_to)
            except ValueError:
                pass  # Ignore invalid date format
        
        if min_score is not None and 0 <= min_score <= 100:
            base_query += " AND overall_score >= %s"
            params.append(min_score)
        
        if max_score is not None and 0 <= max_score <= 100:
            base_query += " AND overall_score <= %s"
            params.append(max_score)
        
        # Add sorting
        base_query += f" ORDER BY {sort_field} {sort_order.upper()}"
        
        # Add pagination
        offset = (page - 1) * limit
        base_query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        # Execute query
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(base_query, params)
                resumes_raw = cursor.fetchall()
                
                # Get total count for pagination (without LIMIT/OFFSET)
                count_query = """
                    SELECT COUNT(*) 
                    FROM resumes 
                    WHERE user_id = %s
                """
                count_params = [user_id]
                
                # Add same filters for count
                if status and status in ['pending', 'processing', 'completed', 'failed']:
                    count_query += " AND processing_status = %s"
                    count_params.append(status)
                
                if search:
                    count_query += " AND (filename ILIKE %s OR candidate_name ILIKE %s)"
                    count_params.extend([search_term, search_term])
                
                if date_from:
                    try:
                        datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                        count_query += " AND upload_date >= %s"
                        count_params.append(date_from)
                    except ValueError:
                        pass
                
                if date_to:
                    try:
                        datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                        count_query += " AND upload_date <= %s"
                        count_params.append(date_to)
                    except ValueError:
                        pass
                
                if min_score is not None:
                    count_query += " AND overall_score >= %s"
                    count_params.append(min_score)
                
                if max_score is not None:
                    count_query += " AND overall_score <= %s"
                    count_params.append(max_score)
                
                cursor.execute(count_query, count_params)
                total_count = cursor.fetchone()[0]
        
        # Format resumes with secure file URLs
        formatted_resumes = []
        for resume in resumes_raw:
            resume_data = {
                'id': resume[0],
                'filename': resume[1],
                'candidate_name': resume[3] or 'Unknown',
                'upload_date': resume[4].isoformat() if resume[4] else None,
                'processing_status': resume[5] or 'pending',
                'overall_score': float(resume[6]) if resume[6] is not None else None,
                'skills_extracted': json.loads(resume[7]) if resume[7] else [],
                'file_size': resume[8],
                'created_at': resume[9].isoformat() if resume[9] else None,
                'updated_at': resume[10].isoformat() if resume[10] else None
            }
            
            # Generate secure file URL if storage manager is available
            if storage_manager and resume[2]:  # file_path exists
                try:
                    secure_url = storage_manager.generate_secure_url(resume[2], expires_in=3600)  # 1 hour
                    resume_data['file_url'] = secure_url
                except Exception as e:
                    logger.warning(f"Could not generate secure URL for resume {resume[0]}: {e}")
                    resume_data['file_url'] = None
            
            formatted_resumes.append(resume_data)
        
        # Calculate pagination metadata
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        has_next = page < total_pages
        has_prev = page > 1
        
        response_data = {
            'resumes': formatted_resumes,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_count': total_count,
                'per_page': limit,
                'has_next': has_next,
                'has_prev': has_prev,
                'next_page': page + 1 if has_next else None,
                'prev_page': page - 1 if has_prev else None
            },
            'filters_applied': {
                'status': status,
                'search': search,
                'date_from': date_from,
                'date_to': date_to,
                'min_score': min_score,
                'max_score': max_score,
                'sort': f"{sort_field} {sort_order}"
            }
        }
        
        return jsonify(_get_standardized_response(
            success=True,
            data=response_data,
            message=f"Retrieved {len(formatted_resumes)} resumes"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching resumes for user {request.user.get('user_id', 'unknown')}: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error="Failed to retrieve resumes",
            code="RESUMES_FETCH_ERROR"
        )), 500

@user_bp.route('/profile', methods=['GET'])
@require_user_auth
def get_user_profile():
    """Get comprehensive user profile data"""
    try:
        user_id = request.user['user_id']
        
        # Get user profile from Railway PostgreSQL
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        id, email, full_name, phone, avatar_url, location_data,
                        professional_info, preferences, security_settings, timezone,
                        access_type, is_trial, created_at, last_login, login_count,
                        email_verified, phone_verified, last_active
                    FROM user_profiles 
                    WHERE id = %s
                """, (user_id,))
                
                user_row = cursor.fetchone()
                if not user_row:
                    return jsonify(_get_standardized_response(
                        success=False,
                        error="User profile not found",
                        code="PROFILE_NOT_FOUND"
                    )), 404
        
        # Get subscription information
        subscription_info = {}
        if credit_manager:
            try:
                credit_data = credit_manager.get_user_credits(user_id)
                subscription_info = {
                    'plan': credit_data.get('plan_type', 'trial'),
                    'status': 'active' if credit_data.get('remaining_credits', 0) > 0 else 'expired',
                    'credits_used': credit_data.get('used_credits', 0),
                    'credits_remaining': credit_data.get('remaining_credits', 0),
                    'resets_at': credit_data.get('resets_at'),
                    'is_trial': credit_data.get('is_trial', True)
                }
            except Exception as e:
                logger.warning(f"Could not fetch subscription info for user {user_id}: {e}")
        
        # Parse JSON fields safely
        def safe_json_parse(field, default=None):
            if field:
                try:
                    return json.loads(field) if isinstance(field, str) else field
                except (json.JSONDecodeError, TypeError):
                    return default
            return default
        
        location_data = safe_json_parse(user_row[5], {})
        professional_info = safe_json_parse(user_row[6], {})
        preferences = safe_json_parse(user_row[7], {})
        security_settings = safe_json_parse(user_row[8], {})
        
        # Format comprehensive profile response
        profile_data = {
            'user': {
                'id': user_row[0],
                'email': user_row[1],
                'name': user_row[2] or '',
                'phone': user_row[3] or '',
                'avatar_url': user_row[4] or '',
                'location': {
                    'city': location_data.get('city', ''),
                    'state': location_data.get('state', ''),
                    'country': location_data.get('country', ''),
                    'timezone': user_row[9] or 'UTC'
                },
                'professional_info': {
                    'title': professional_info.get('title', ''),
                    'company': professional_info.get('company', ''),
                    'industry': professional_info.get('industry', ''),
                    'experience_level': professional_info.get('experience_level', ''),
                    'current_salary_range': professional_info.get('current_salary_range', ''),
                    'target_salary_range': professional_info.get('target_salary_range', '')
                },
                'account_info': {
                    'access_type': user_row[10] or 'user',
                    'is_trial': user_row[11] if user_row[11] is not None else True,
                    'account_created': user_row[12].isoformat() if user_row[12] else None,
                    'last_login': user_row[13].isoformat() if user_row[13] else None,
                    'login_count': user_row[14] or 0,
                    'email_verified': user_row[15] if user_row[15] is not None else False,
                    'phone_verified': user_row[16] if user_row[16] is not None else False,
                    'last_active': user_row[17].isoformat() if user_row[17] else None,
                    'two_factor_enabled': security_settings.get('two_factor_enabled', False)
                }
            },
            'subscription': subscription_info,
            'preferences': {
                'notifications': preferences.get('notifications', {}),
                'privacy': preferences.get('privacy', {}),
                'dashboard': preferences.get('dashboard', {}),
                'resume_analysis': preferences.get('resume_analysis', {})
            },
            'security': {
                'password_last_changed': security_settings.get('password_last_changed'),
                'failed_login_attempts': security_settings.get('failed_login_attempts', 0),
                'account_locked': security_settings.get('account_locked', False),
                'suspicious_activity_detected': security_settings.get('suspicious_activity_detected', False)
            }
        }
        
        return jsonify(_get_standardized_response(
            success=True,
            data=profile_data,
            message="Profile retrieved successfully"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching profile for user {request.user.get('user_id', 'unknown')}: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error="Failed to retrieve user profile",
            code="PROFILE_ERROR"
        )), 500

@user_bp.route('/profile', methods=['PUT'])
@require_user_auth
def update_user_profile():
    """Update user profile with validation"""
    try:
        user_id = request.user['user_id']
        data = request.get_json()
        
        if not data:
            return jsonify(_get_standardized_response(
                success=False,
                error="No data provided for profile update",
                code="NO_DATA"
            )), 400
        
        # Validate and sanitize input data
        allowed_fields = {
            'name': 'full_name',
            'phone': 'phone', 
            'avatar_url': 'avatar_url',
            'location': 'location_data',
            'professional_info': 'professional_info',
            'preferences': 'preferences',
            'timezone': 'timezone'
        }
        
        update_fields = []
        update_values = []
        
        for field, db_column in allowed_fields.items():
            if field in data:
                if field in ['location', 'professional_info', 'preferences']:
                    # JSON fields - validate and convert
                    if isinstance(data[field], dict):
                        update_fields.append(f"{db_column} = %s")
                        update_values.append(json.dumps(data[field]))
                elif field == 'name':
                    # String field with length validation
                    name = str(data[field]).strip()[:100]  # Limit to 100 chars
                    if name:
                        update_fields.append(f"{db_column} = %s")
                        update_values.append(name)
                elif field == 'phone':
                    # Phone number validation (basic)
                    phone = str(data[field]).strip()[:20]  # Limit to 20 chars
                    update_fields.append(f"{db_column} = %s")
                    update_values.append(phone)
                elif field == 'avatar_url':
                    # URL validation (basic)
                    avatar_url = str(data[field]).strip()[:500]  # Limit to 500 chars
                    update_fields.append(f"{db_column} = %s")
                    update_values.append(avatar_url)
                elif field == 'timezone':
                    # Timezone validation (basic)
                    timezone = str(data[field]).strip()[:50]  # Limit to 50 chars
                    update_fields.append(f"{db_column} = %s")
                    update_values.append(timezone)
        
        if not update_fields:
            return jsonify(_get_standardized_response(
                success=False,
                error="No valid fields provided for update",
                code="NO_VALID_FIELDS"
            )), 400
        
        # Update profile in Railway PostgreSQL
        update_query = f"""
            UPDATE user_profiles 
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE id = %s
            RETURNING id
        """
        update_values.append(user_id)
        
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(update_query, update_values)
                result = cursor.fetchone()
                
                if not result:
                    conn.rollback()
                    return jsonify(_get_standardized_response(
                        success=False,
                        error="User profile not found",
                        code="PROFILE_NOT_FOUND"
                    )), 404
                
                conn.commit()
        
        # Log profile update activity
        _log_user_activity(
            user_id=user_id,
            action="profile_updated",
            category="account",
            details={
                'fields_updated': list(data.keys()),
                'update_timestamp': datetime.utcnow().isoformat()
            }
        )
        
        return jsonify(_get_standardized_response(
            success=True,
            message="Profile updated successfully",
            data={'updated_fields': list(data.keys())}
        ))
        
    except Exception as e:
        logger.error(f"Error updating profile for user {request.user.get('user_id', 'unknown')}: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error="Failed to update user profile",
            code="PROFILE_UPDATE_ERROR"
        )), 500

@user_bp.route('/upload-resume', methods=['POST'])
@require_user_auth
def upload_resume():
    """Upload resume with user quota enforcement and AI processing"""
    try:
        user_id = request.user['user_id']
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify(_get_standardized_response(
                success=False,
                error="No file uploaded",
                code="NO_FILE"
            )), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify(_get_standardized_response(
                success=False,
                error="No file selected",
                code="NO_FILE_SELECTED"
            )), 400
        
        # Validate file type and size
        allowed_extensions = {'.pdf', '.docx', '.doc'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify(_get_standardized_response(
                success=False,
                error="Only PDF, DOCX, and DOC files are allowed",
                code="INVALID_FILE_TYPE"
            )), 400
        
        # Check file size (10MB limit)
        file.seek(0, 2)  # Seek to end of file
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            return jsonify(_get_standardized_response(
                success=False,
                error="File size exceeds 10MB limit",
                code="FILE_TOO_LARGE"
            )), 400
        
        # Check user quota/credits
        if credit_manager:
            try:
                credit_check = credit_manager.check_user_credits(user_id, 'resume_upload')
                if not credit_check.get('allowed', False):
                    return jsonify(_get_standardized_response(
                        success=False,
                        error=credit_check.get('message', 'Insufficient credits'),
                        code="QUOTA_EXCEEDED"
                    )), 429
            except Exception as e:
                logger.warning(f"Credit check failed for user {user_id}: {e}")
                # Continue without credit check if service is unavailable
        
        # Get additional form data
        job_description = request.form.get('job_description', '').strip()
        tags = request.form.getlist('tags') or []
        is_primary = request.form.get('is_primary', 'false').lower() == 'true'
        privacy_level = request.form.get('privacy_level', 'private')
        
        # Validate privacy level
        if privacy_level not in ['private', 'public', 'shared']:
            privacy_level = 'private'
        
        # Save file using storage manager
        if not storage_manager:
            return jsonify(_get_standardized_response(
                success=False,
                error="File storage service unavailable",
                code="STORAGE_UNAVAILABLE"
            )), 500
        
        try:
            # Generate secure filename
            import uuid
            unique_id = str(uuid.uuid4())
            safe_filename = f"{unique_id}_{secure_filename(file.filename)}"
            
            # Save file and get file path
            file_path = storage_manager.save_uploaded_file(
                file=file,
                filename=safe_filename,
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"File upload failed for user {user_id}: {e}")
            return jsonify(_get_standardized_response(
                success=False,
                error="File upload failed",
                code="UPLOAD_FAILED"
            )), 500
        
        # Insert resume record into database
        try:
            with railway_db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Insert resume record
                    cursor.execute("""
                        INSERT INTO resumes (
                            id, user_id, filename, file_path, file_size,
                            processing_status, job_description, tags,
                            is_primary, privacy_level, upload_date, created_at
                        ) VALUES (
                            gen_random_uuid(), %s, %s, %s, %s,
                            'pending', %s, %s, %s, %s, NOW(), NOW()
                        ) RETURNING id, upload_date
                    """, (
                        user_id, file.filename, file_path, file_size,
                        job_description, json.dumps(tags), is_primary, privacy_level
                    ))
                    
                    resume_result = cursor.fetchone()
                    resume_id = resume_result[0]
                    upload_date = resume_result[1]
                    
                    conn.commit()
        
        except Exception as e:
            logger.error(f"Database insert failed for user {user_id}: {e}")
            # Try to clean up uploaded file
            try:
                storage_manager.delete_file(file_path)
            except:
                pass
            
            return jsonify(_get_standardized_response(
                success=False,
                error="Failed to save resume record",
                code="DATABASE_ERROR"
            )), 500
        
        # Update user credits if credit manager is available
        if credit_manager:
            try:
                credit_manager.deduct_user_credits(user_id, 'resume_upload', 1)
            except Exception as e:
                logger.warning(f"Credit deduction failed for user {user_id}: {e}")
        
        # AUTOMATIC AI PROCESSING - Process immediately on upload
        processing_status = "pending"
        processing_queued = False
        estimated_time = "Processing now..."
        analysis_results = None
        
        try:
            # Extract text from uploaded file for immediate processing
            if storage_manager:
                file_text = storage_manager.extract_text_from_file(file_path)
                if file_text and len(file_text.strip()) > 50:  # Ensure meaningful content
                    
                    # Process immediately with unified AI processor
                    if unified_ai_processor:
                        logger.info(f"🤖 Starting immediate AI analysis for resume {resume_id}")
                        
                        # Run AI analysis synchronously for immediate results
                        import asyncio
                        try:
                            # Create new event loop if none exists (for sync context)
                            try:
                                loop = asyncio.get_event_loop()
                            except RuntimeError:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                            
                            # Process resume with unified AI
                            ai_result = loop.run_until_complete(
                                unified_ai_processor.process_resume(
                                    resume_text=file_text,
                                    user_id=user_id,
                                    analysis_type="comprehensive"
                                )
                            )
                            
                            if ai_result.success and ai_result.data:
                                # Update database with analysis results immediately
                                analysis_data = ai_result.data
                                
                                with railway_db.get_connection() as conn:
                                    with conn.cursor() as cursor:
                                        cursor.execute("""
                                            UPDATE resumes SET 
                                            overall_score = %s, experience_score = %s, skills_score = %s, education_score = %s,
                                            candidate_name = %s, candidate_email = %s, candidate_phone = %s, summary = %s,
                                            key_skills = %s, experience_years = %s, education = %s, analysis_complete = true,
                                            processing_status = 'completed', ai_provider_used = %s, ai_model_used = %s,
                                            processing_completed_at = NOW(), extracted_text = %s, updated_at = NOW()
                                            WHERE id = %s AND user_id = %s
                                        """, (
                                            analysis_data.get('overall_score', 75),
                                            analysis_data.get('experience_score', 70),
                                            analysis_data.get('skills_score', 75),
                                            analysis_data.get('education_score', 70),
                                            analysis_data.get('candidate_info', {}).get('name', 'Unknown'),
                                            analysis_data.get('candidate_info', {}).get('email', ''),
                                            analysis_data.get('candidate_info', {}).get('phone', ''),
                                            analysis_data.get('summary', ''),
                                            json.dumps(analysis_data.get('key_skills', [])),
                                            analysis_data.get('experience_years', 0),
                                            json.dumps(analysis_data.get('education', [])),
                                            ai_result.provider_used.value if ai_result.provider_used else 'unified',
                                            ai_result.model_used or 'unknown',
                                            file_text[:50000],  # Store first 50k chars of extracted text
                                            resume_id,
                                            user_id
                                        ))
                                        conn.commit()
                                
                                processing_status = "completed"
                                estimated_time = "Analysis complete!"
                                analysis_results = {
                                    'overall_score': analysis_data.get('overall_score', 75),
                                    'experience_score': analysis_data.get('experience_score', 70),
                                    'skills_score': analysis_data.get('skills_score', 75),
                                    'education_score': analysis_data.get('education_score', 70),
                                    'candidate_name': analysis_data.get('candidate_info', {}).get('name', 'Unknown'),
                                    'key_skills': analysis_data.get('key_skills', [])[:10],  # First 10 skills
                                    'ai_provider': ai_result.provider_used.value if ai_result.provider_used else 'unified'
                                }
                                
                                logger.info(f"✅ Immediate AI analysis completed for resume {resume_id} - Score: {analysis_data.get('overall_score', 75)}")
                            else:
                                # AI processing failed, queue for retry
                                processing_queued = True
                                estimated_time = "Analysis failed, will retry automatically"
                                logger.warning(f"AI analysis failed for resume {resume_id}: {ai_result.error}")
                                
                        except Exception as ai_error:
                            logger.error(f"Immediate AI processing failed for resume {resume_id}: {ai_error}")
                            # Queue for background processing as fallback
                            processing_queued = True
                            estimated_time = "Processing queued due to system load"
                            
                            # Queue background processing as fallback
                            asyncio.create_task(_process_resume_with_unified_ai(
                                resume_id=str(resume_id),
                                resume_text=file_text,
                                filename=file.filename,
                                user_id=user_id
                            ))
                    else:
                        logger.warning("Unified AI processor not available - queueing for later")
                        processing_queued = True
                        estimated_time = "AI processor unavailable, will process when available"
                else:
                    logger.warning(f"Could not extract meaningful text from file {file.filename}")
                    processing_status = "failed"
                    estimated_time = "Text extraction failed"
                    
                    # Update status in database
                    with railway_db.get_connection() as conn:
                        with conn.cursor() as cursor:
                            cursor.execute("""
                                UPDATE resumes SET processing_status = 'failed', 
                                processing_error = 'Text extraction failed' WHERE id = %s
                            """, (resume_id,))
                            conn.commit()
            else:
                logger.warning("Storage manager not available for text extraction")
                processing_queued = True
                estimated_time = "Storage service issue, will retry"
                
        except Exception as e:
            logger.error(f"Automatic AI processing failed for resume {resume_id}: {e}")
            processing_queued = True
            estimated_time = "Processing error, queued for retry"
        
        # Log upload activity
        _log_user_activity(
            user_id=user_id,
            action="resume_uploaded",
            category="content",
            details={
                'resume_id': str(resume_id),
                'filename': file.filename,
                'file_size': file_size,
                'processing_queued': processing_queued,
                'tags': tags,
                'is_primary': is_primary
            }
        )
        
        # Get updated trial info for response
        trial_info = {}
        if credit_manager:
            try:
                credit_data = credit_manager.get_user_credits(user_id)
                trial_info = {
                    'is_trial': credit_data.get('is_trial', True),
                    'used': credit_data.get('used_credits', 0),
                    'remaining': credit_data.get('remaining_credits', 0),
                    'resets_at': credit_data.get('resets_at')
                }
            except:
                pass
        
        # Build response with analysis results if available
        response_data = {
            'resume': {
                'id': str(resume_id),
                'filename': file.filename,
                'file_size': file_size,
                'upload_date': upload_date.isoformat() if upload_date else None,
                'processing_status': processing_status,
                'tags': tags,
                'is_primary': is_primary,
                'privacy_level': privacy_level,
                'has_analysis': processing_status == 'completed'
            },
            'trial_info': trial_info,
            'processing_info': {
                'status': processing_status,
                'queued': processing_queued,
                'estimated_time': estimated_time,
                'message': "Analysis completed during upload!" if processing_status == 'completed' else 
                          "Analysis queued for processing" if processing_queued else "Ready for analysis",
                'ai_features': [
                    "✅ Content extraction and parsing",
                    "✅ Skills identification and scoring", 
                    "✅ ATS compatibility analysis",
                    "✅ Keyword optimization suggestions",
                    "✅ Experience timeline validation"
                ] if processing_status == 'completed' else [
                    "Content extraction and parsing",
                    "Skills identification and scoring", 
                    "ATS compatibility analysis",
                    "Keyword optimization suggestions",
                    "Experience timeline validation"
                ]
            }
        }
        
        # Add analysis results if available
        if analysis_results:
            response_data['analysis_preview'] = analysis_results
        
        success_message = (
            f"Resume uploaded and analyzed successfully! Overall score: {analysis_results.get('overall_score', 'N/A')}/100" 
            if analysis_results else 
            f"Resume uploaded successfully. AI analysis {estimated_time.lower()}"
        )
        
        return jsonify(_get_standardized_response(
            success=True,
            data=response_data,
            message=success_message
        ))
        
    except Exception as e:
        logger.error(f"Resume upload error for user {request.user.get('user_id', 'unknown')}: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error="Resume upload failed",
            code="UPLOAD_ERROR"
        )), 500

@user_bp.route('/activity-log', methods=['GET'])
@require_user_auth
def get_activity_log():
    """Get user activity log with filtering and pagination"""
    try:
        user_id = request.user['user_id']
        
        # Parse query parameters
        page = max(1, int(request.args.get('page', 1)))
        limit = min(max(1, int(request.args.get('limit', 50))), 200)  # Limit between 1-200
        action = request.args.get('action', '').strip()
        category = request.args.get('category', '').strip()
        status = request.args.get('status', '').strip()
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query with filters
        base_query = """
            SELECT action, category, details, metadata, status, created_at
            FROM user_activity_detailed 
            WHERE user_id = %s
        """
        params = [user_id]
        
        # Add filters
        if action:
            base_query += " AND action ILIKE %s"
            params.append(f"%{action}%")
        
        if category:
            base_query += " AND category = %s"
            params.append(category)
        
        if status and status in ['success', 'failed', 'warning']:
            base_query += " AND status = %s"
            params.append(status)
        
        if date_from:
            try:
                datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                base_query += " AND created_at >= %s"
                params.append(date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                base_query += " AND created_at <= %s"
                params.append(date_to)
            except ValueError:
                pass
        
        # Add ordering and pagination
        base_query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        offset = (page - 1) * limit
        params.extend([limit, offset])
        
        # Execute query
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(base_query, params)
                activities_raw = cursor.fetchall()
                
                # Get total count
                count_query = "SELECT COUNT(*) FROM user_activity_detailed WHERE user_id = %s"
                count_params = [user_id]
                
                # Add same filters for count
                if action:
                    count_query += " AND action ILIKE %s"
                    count_params.append(f"%{action}%")
                
                if category:
                    count_query += " AND category = %s"
                    count_params.append(category)
                
                if status and status in ['success', 'failed', 'warning']:
                    count_query += " AND status = %s"
                    count_params.append(status)
                
                if date_from:
                    try:
                        datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                        count_query += " AND created_at >= %s"
                        count_params.append(date_from)
                    except ValueError:
                        pass
                
                if date_to:
                    try:
                        datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                        count_query += " AND created_at <= %s"
                        count_params.append(date_to)
                    except ValueError:
                        pass
                
                cursor.execute(count_query, count_params)
                total_count = cursor.fetchone()[0]
        
        # Format activities
        formatted_activities = []
        for activity in activities_raw:
            activity_data = {
                'action': activity[0],
                'category': activity[1],
                'details': json.loads(activity[2]) if activity[2] else {},
                'metadata': json.loads(activity[3]) if activity[3] else {},
                'status': activity[4],
                'timestamp': activity[5].isoformat() if activity[5] else None
            }
            formatted_activities.append(activity_data)
        
        # Calculate pagination
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        response_data = {
            'activities': formatted_activities,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_count': total_count,
                'per_page': limit,
                'has_next': has_next,
                'has_prev': has_prev
            },
            'filters_applied': {
                'action': action,
                'category': category,
                'status': status,
                'date_from': date_from,
                'date_to': date_to
            },
            'categories': ['content', 'account', 'billing', 'security', 'api_access', 'system']
        }
        
        return jsonify(_get_standardized_response(
            success=True,
            data=response_data,
            message=f"Retrieved {len(formatted_activities)} activity records"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching activity log for user {request.user.get('user_id', 'unknown')}: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error="Failed to retrieve activity log",
            code="ACTIVITY_LOG_ERROR"
        )), 500

@user_bp.route('/usage-stats', methods=['GET'])
@require_user_auth
def get_usage_stats():
    """Get user usage statistics and analytics"""
    try:
        user_id = request.user['user_id']
        
        # Parse query parameters
        period = request.args.get('period', 'last_30_days')
        include_trends = request.args.get('include_trends', 'false').lower() == 'true'
        include_insights = request.args.get('include_insights', 'false').lower() == 'true'
        granularity = request.args.get('granularity', 'day')
        
        # Calculate date range based on period
        end_date = datetime.utcnow()
        
        if period == 'last_7_days':
            start_date = end_date - timedelta(days=7)
        elif period == 'last_30_days':
            start_date = end_date - timedelta(days=30)
        elif period == 'last_90_days':
            start_date = end_date - timedelta(days=90)
        elif period == 'this_month':
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == 'last_month':
            last_month = end_date.replace(day=1) - timedelta(days=1)
            start_date = last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = last_month.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == 'custom':
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')
            if date_from and date_to:
                try:
                    start_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                    end_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                except ValueError:
                    start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get usage statistics from database
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Basic stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_resumes,
                        COUNT(*) FILTER (WHERE processing_status = 'completed') as analyzed_resumes,
                        AVG(CASE WHEN overall_score IS NOT NULL THEN overall_score END) as avg_score,
                        COUNT(*) FILTER (WHERE upload_date >= %s) as period_uploads
                    FROM resumes 
                    WHERE user_id = %s AND upload_date <= %s
                """, (start_date, user_id, end_date))
                
                basic_stats = cursor.fetchone()
                
                # Daily/weekly breakdown based on granularity
                if granularity == 'day':
                    interval_trunc = 'day'
                elif granularity == 'week':
                    interval_trunc = 'week'
                elif granularity == 'month':
                    interval_trunc = 'month'
                else:
                    interval_trunc = 'day'
                
                cursor.execute(f"""
                    SELECT 
                        DATE_TRUNC(%s, upload_date) as period,
                        COUNT(*) as uploads,
                        COUNT(*) FILTER (WHERE processing_status = 'completed') as completed,
                        AVG(CASE WHEN overall_score IS NOT NULL THEN overall_score END) as avg_score
                    FROM resumes 
                    WHERE user_id = %s 
                        AND upload_date >= %s 
                        AND upload_date <= %s
                    GROUP BY DATE_TRUNC(%s, upload_date)
                    ORDER BY period ASC
                """, (interval_trunc, user_id, start_date, end_date, interval_trunc))
                
                time_series = []
                for row in cursor.fetchall():
                    time_series.append({
                        'period': row[0].isoformat() if row[0] else None,
                        'uploads': row[1] or 0,
                        'completed': row[2] or 0,
                        'avg_score': float(row[3]) if row[3] else 0
                    })
                
                # Activity breakdown
                cursor.execute("""
                    SELECT category, COUNT(*) as count
                    FROM user_activity_detailed 
                    WHERE user_id = %s 
                        AND created_at >= %s 
                        AND created_at <= %s
                    GROUP BY category
                    ORDER BY count DESC
                """, (user_id, start_date, end_date))
                
                activity_breakdown = {}
                for row in cursor.fetchall():
                    activity_breakdown[row[0]] = row[1]
        
        # Calculate trends if requested
        trends = {}
        if include_trends and len(time_series) >= 2:
            # Calculate upload trend
            recent_uploads = sum(item['uploads'] for item in time_series[-7:])  # Last 7 periods
            previous_uploads = sum(item['uploads'] for item in time_series[-14:-7])  # Previous 7 periods
            
            if previous_uploads > 0:
                upload_trend = ((recent_uploads - previous_uploads) / previous_uploads) * 100
            else:
                upload_trend = 100 if recent_uploads > 0 else 0
            
            # Calculate score trend
            recent_scores = [item['avg_score'] for item in time_series[-7:] if item['avg_score'] > 0]
            previous_scores = [item['avg_score'] for item in time_series[-14:-7] if item['avg_score'] > 0]
            
            score_trend = 0
            if recent_scores and previous_scores:
                avg_recent = sum(recent_scores) / len(recent_scores)
                avg_previous = sum(previous_scores) / len(previous_scores)
                if avg_previous > 0:
                    score_trend = ((avg_recent - avg_previous) / avg_previous) * 100
            
            trends = {
                'upload_trend': round(upload_trend, 1),
                'score_trend': round(score_trend, 1),
                'activity_trend': len(activity_breakdown)
            }
        
        # Generate insights if requested
        insights = []
        if include_insights:
            total_uploads = basic_stats[0] or 0
            avg_score = basic_stats[2] or 0
            
            if total_uploads > 10:
                insights.append({
                    'type': 'achievement',
                    'title': 'Resume Portfolio Building',
                    'message': f'Great progress! You have uploaded {total_uploads} resumes to build your portfolio.'
                })
            
            if avg_score > 85:
                insights.append({
                    'type': 'positive',
                    'title': 'High Quality Resumes',
                    'message': f'Your resumes have an excellent average score of {avg_score:.1f}!'
                })
            elif avg_score > 70:
                insights.append({
                    'type': 'neutral',
                    'title': 'Good Resume Quality',
                    'message': f'Your resumes have a good average score of {avg_score:.1f}. Consider optimizing for higher scores.'
                })
            elif total_uploads > 0:
                insights.append({
                    'type': 'improvement',
                    'title': 'Room for Improvement',
                    'message': 'Focus on keyword optimization and ATS compatibility to improve your resume scores.'
                })
            
            if trends.get('upload_trend', 0) > 20:
                insights.append({
                    'type': 'positive',
                    'title': 'Increased Activity',
                    'message': 'Your upload activity has increased significantly. Keep up the momentum!'
                })
        
        # Build response
        response_data = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'period_type': period,
                'granularity': granularity
            },
            'summary': {
                'total_resumes': basic_stats[0] or 0,
                'analyzed_resumes': basic_stats[1] or 0,
                'average_score': round(float(basic_stats[2] or 0), 1),
                'period_uploads': basic_stats[3] or 0,
                'completion_rate': round((basic_stats[1] / max(basic_stats[0], 1)) * 100, 1)
            },
            'time_series': time_series,
            'activity_breakdown': activity_breakdown
        }
        
        if include_trends:
            response_data['trends'] = trends
        
        if include_insights:
            response_data['insights'] = insights
        
        return jsonify(_get_standardized_response(
            success=True,
            data=response_data,
            message="Usage statistics retrieved successfully"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching usage stats for user {request.user.get('user_id', 'unknown')}: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error="Failed to retrieve usage statistics",
            code="USAGE_STATS_ERROR"
        )), 500

# Health check endpoint for user routes
@user_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for user routes"""
    return jsonify({
        'success': True,
        'service': 'user_routes',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'dependencies': {
            'railway_db': railway_db is not None,
            'auth_middleware': auth_middleware is not None,
            'storage_manager': storage_manager is not None,
            'credit_manager': credit_manager is not None
        }
    })

# ============================================================================
# SUBSCRIPTION MANAGEMENT ENDPOINTS
# ============================================================================

@user_bp.route('/subscription', methods=['GET'])
@require_user_auth
def get_user_subscription():
    """Get current user subscription status and details"""
    try:
        user_id = g.current_user['user_id']
        
        _log_user_activity(
            user_id=user_id,
            action='get_subscription',
            category='billing',
            details={'action': 'view_subscription_status'}
        )
        
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get current subscription
                cursor.execute("""
                    SELECT plan_id, plan_name, status, billing_cycle, amount, currency,
                           current_period_start, current_period_end, monthly_resume_limit,
                           created_at, updated_at
                    FROM user_subscriptions 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """, (user_id,))
                
                subscription = cursor.fetchone()
                
                if subscription:
                    subscription_data = {
                        'plan_id': subscription[0],
                        'plan_name': subscription[1],
                        'status': subscription[2],
                        'billing_cycle': subscription[3],
                        'amount': float(subscription[4]) if subscription[4] else 0,
                        'currency': subscription[5],
                        'current_period_start': subscription[6].isoformat() if subscription[6] else None,
                        'current_period_end': subscription[7].isoformat() if subscription[7] else None,
                        'monthly_resume_limit': subscription[8],
                        'created_at': subscription[9].isoformat() if subscription[9] else None,
                        'updated_at': subscription[10].isoformat() if subscription[10] else None
                    }
                    
                    # Calculate usage in current period
                    if subscription[6] and subscription[7]:
                        cursor.execute("""
                            SELECT COUNT(*) 
                            FROM resumes 
                            WHERE user_id = %s 
                            AND upload_date >= %s 
                            AND upload_date <= %s
                        """, (user_id, subscription[6], subscription[7]))
                        
                        current_usage = cursor.fetchone()[0]
                        subscription_data['current_usage'] = {
                            'resumes_uploaded': current_usage,
                            'remaining_resumes': max(0, subscription[8] - current_usage) if subscription[8] else 'unlimited'
                        }
                else:
                    # Create default trial subscription if none exists
                    cursor.execute("""
                        INSERT INTO user_subscriptions 
                        (user_id, plan_id, plan_name, status, billing_cycle, amount, currency, monthly_resume_limit)
                        VALUES (%s, 'trial', 'Trial Plan', 'active', 'monthly', 0, 'INR', 100)
                        RETURNING plan_id, plan_name, status, billing_cycle, amount, currency,
                                  current_period_start, current_period_end, monthly_resume_limit,
                                  created_at, updated_at
                    """, (user_id,))
                    
                    subscription = cursor.fetchone()
                    subscription_data = {
                        'plan_id': subscription[0],
                        'plan_name': subscription[1],
                        'status': subscription[2],
                        'billing_cycle': subscription[3],
                        'amount': float(subscription[4]) if subscription[4] else 0,
                        'currency': subscription[5],
                        'current_period_start': subscription[6].isoformat() if subscription[6] else None,
                        'current_period_end': subscription[7].isoformat() if subscription[7] else None,
                        'monthly_resume_limit': subscription[8],
                        'created_at': subscription[9].isoformat() if subscription[9] else None,
                        'updated_at': subscription[10].isoformat() if subscription[10] else None,
                        'current_usage': {
                            'resumes_uploaded': 0,
                            'remaining_resumes': subscription[8] if subscription[8] else 'unlimited'
                        }
                    }
                    
                    conn.commit()
                
                # Get billing history
                cursor.execute("""
                    SELECT po.razorpay_order_id, po.amount, po.currency, po.status, 
                           po.created_at, po.paid_at, po.description
                    FROM payment_orders po
                    WHERE po.user_id = %s
                    ORDER BY po.created_at DESC
                    LIMIT 10
                """, (user_id,))
                
                billing_history = []
                for order in cursor.fetchall():
                    billing_history.append({
                        'order_id': order[0],
                        'amount': order[1] / 100 if order[1] else 0,  # Convert paise to rupees
                        'currency': order[2],
                        'status': order[3],
                        'created_at': order[4].isoformat() if order[4] else None,
                        'paid_at': order[5].isoformat() if order[5] else None,
                        'description': order[6]
                    })
                
                subscription_data['billing_history'] = billing_history
                
                return jsonify(_get_standardized_response(
                    success=True,
                    data={'subscription': subscription_data},
                    message='Subscription details retrieved successfully'
                ))
                
    except Exception as e:
        logger.error(f"Error getting subscription for user {user_id}: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error='Failed to retrieve subscription information'
        )), 500

@user_bp.route('/subscription/change-plan', methods=['POST'])
@require_user_auth
def change_subscription_plan():
    """Change user's subscription plan"""
    try:
        user_id = g.current_user['user_id']
        data = request.get_json()
        
        if not data or 'new_plan' not in data:
            return jsonify(_get_standardized_response(
                success=False,
                error='new_plan is required'
            )), 400
        
        new_plan = data['new_plan']
        effective_date = data.get('effective_date', 'immediate')
        
        # Validate plan
        valid_plans = {
            'trial': {'name': 'Trial Plan', 'amount': 0, 'limit': 100},
            'basic': {'name': 'Basic Plan', 'amount': 999, 'limit': 500},
            'professional': {'name': 'Professional Plan', 'amount': 2999, 'limit': 2000},
            'enterprise': {'name': 'Enterprise Plan', 'amount': 9999, 'limit': None}
        }
        
        if new_plan not in valid_plans:
            return jsonify(_get_standardized_response(
                success=False,
                error='Invalid plan selected'
            )), 400
        
        plan_info = valid_plans[new_plan]
        
        _log_user_activity(
            user_id=user_id,
            action='change_subscription_plan',
            category='billing',
            details={
                'new_plan': new_plan,
                'effective_date': effective_date,
                'plan_amount': plan_info['amount']
            }
        )
        
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Update current subscription
                cursor.execute("""
                    UPDATE user_subscriptions 
                    SET plan_id = %s, plan_name = %s, amount = %s, monthly_resume_limit = %s,
                        updated_at = NOW()
                    WHERE user_id = %s
                """, (new_plan, plan_info['name'], plan_info['amount'], 
                     plan_info['limit'], user_id))
                
                if cursor.rowcount == 0:
                    # Create new subscription if none exists
                    cursor.execute("""
                        INSERT INTO user_subscriptions 
                        (user_id, plan_id, plan_name, amount, monthly_resume_limit)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_id, new_plan, plan_info['name'], 
                         plan_info['amount'], plan_info['limit']))
                
                conn.commit()
                
                return jsonify(_get_standardized_response(
                    success=True,
                    data={
                        'plan_id': new_plan,
                        'plan_name': plan_info['name'],
                        'effective_date': effective_date,
                        'amount': plan_info['amount'],
                        'monthly_limit': plan_info['limit']
                    },
                    message='Subscription plan updated successfully'
                ))
                
    except Exception as e:
        logger.error(f"Error changing subscription plan for user {user_id}: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error='Failed to change subscription plan'
        )), 500

@user_bp.route('/subscription/cancel', methods=['POST'])
@require_user_auth
def cancel_subscription():
    """Cancel user's subscription"""
    try:
        user_id = g.current_user['user_id']
        data = request.get_json() or {}
        
        cancellation_reason = data.get('cancellation_reason', 'User requested cancellation')
        effective_date = data.get('effective_date', 'end_of_billing_cycle')
        
        _log_user_activity(
            user_id=user_id,
            action='cancel_subscription',
            category='billing',
            details={
                'reason': cancellation_reason,
                'effective_date': effective_date
            }
        )
        
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Update subscription status
                if effective_date == 'immediate':
                    cursor.execute("""
                        UPDATE user_subscriptions 
                        SET status = 'cancelled', cancelled_at = NOW(), ends_at = NOW(),
                            updated_at = NOW()
                        WHERE user_id = %s AND status = 'active'
                    """, (user_id,))
                else:
                    cursor.execute("""
                        UPDATE user_subscriptions 
                        SET status = 'cancelled', cancelled_at = NOW(), 
                            ends_at = current_period_end, updated_at = NOW()
                        WHERE user_id = %s AND status = 'active'
                    """, (user_id,))
                
                if cursor.rowcount == 0:
                    return jsonify(_get_standardized_response(
                        success=False,
                        error='No active subscription found to cancel'
                    )), 404
                
                conn.commit()
                
                return jsonify(_get_standardized_response(
                    success=True,
                    data={
                        'cancellation_reason': cancellation_reason,
                        'effective_date': effective_date,
                        'cancelled_at': datetime.utcnow().isoformat()
                    },
                    message='Subscription cancelled successfully'
                ))
                
    except Exception as e:
        logger.error(f"Error cancelling subscription for user {user_id}: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error='Failed to cancel subscription'
        )), 500

async def _process_resume_with_unified_ai(resume_id: str, resume_text: str, filename: str, user_id: str):
    """Process resume using unified AI processor with user's configured model"""
    try:
        logger.info(f"🤖 Starting unified AI processing for resume {resume_id} (user: {user_id})")
        
        if not unified_ai_processor:
            logger.error("Unified AI processor not available")
            return
        
        # Process resume with user's configured AI provider
        start_time = datetime.utcnow()
        
        # Run AI analysis with user's preferred provider
        ai_result = await unified_ai_processor.process_resume(
            resume_text=resume_text,
            user_id=user_id,
            analysis_type="comprehensive"
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Prepare database record
        if ai_result.success and ai_result.data:
            database_record = {
                'overall_score': ai_result.data.get('overall_score', 75),
                'experience_score': ai_result.data.get('experience_score', 70),
                'skills_score': ai_result.data.get('skills_score', 75),
                'education_score': ai_result.data.get('education_score', 70),
                'candidate_name': ai_result.data.get('candidate_info', {}).get('name', 'Unknown'),
                'candidate_email': ai_result.data.get('candidate_info', {}).get('email', ''),
                'candidate_phone': ai_result.data.get('candidate_info', {}).get('phone', ''),
                'summary': ai_result.data.get('summary', ''),
                'key_skills': ai_result.data.get('key_skills', []),
                'experience_years': ai_result.data.get('experience_years', 0),
                'education': ai_result.data.get('education', []),
                'analysis_complete': True,
                'processing_status': 'completed',
                'ai_provider_used': ai_result.provider_used.value if ai_result.provider_used else 'unknown',
                'ai_model_used': ai_result.model_used,
                'ai_processing_time': int(processing_time),
                'processing_completed_at': datetime.utcnow().isoformat()
            }
        else:
            # Error case
            database_record = {
                'overall_score': 0,
                'processing_status': 'failed',
                'processing_error': ai_result.error,
                'ai_processing_time': int(processing_time),
                'processing_completed_at': datetime.utcnow().isoformat()
            }
        
        # Update database via Railway PostgreSQL
        try:
            with railway_db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE resumes SET 
                        overall_score = %s, experience_score = %s, skills_score = %s, education_score = %s,
                        candidate_name = %s, candidate_email = %s, candidate_phone = %s, summary = %s,
                        key_skills = %s, experience_years = %s, education = %s, analysis_complete = %s,
                        processing_status = %s, ai_provider_used = %s, ai_model_used = %s,
                        ai_processing_time = %s, processing_completed_at = %s, updated_at = NOW()
                        WHERE id = %s AND user_id = %s
                    """, (
                        database_record.get('overall_score'),
                        database_record.get('experience_score'),
                        database_record.get('skills_score'),
                        database_record.get('education_score'),
                        database_record.get('candidate_name'),
                        database_record.get('candidate_email'),
                        database_record.get('candidate_phone'),
                        database_record.get('summary'),
                        json.dumps(database_record.get('key_skills', [])),
                        database_record.get('experience_years'),
                        json.dumps(database_record.get('education', [])),
                        database_record.get('analysis_complete'),
                        database_record.get('processing_status'),
                        database_record.get('ai_provider_used'),
                        database_record.get('ai_model_used'),
                        database_record.get('ai_processing_time'),
                        database_record.get('processing_completed_at'),
                        resume_id,
                        user_id
                    ))
                    conn.commit()
                    
                    logger.info(f"✅ Database updated successfully for resume {resume_id} using {ai_result.provider_used.value if ai_result.provider_used else 'unknown'}")
        
        except Exception as db_error:
            logger.error(f"Database update error for resume {resume_id}: {db_error}")
        
        logger.info(f"✅ Unified AI processing completed for resume {resume_id} in {processing_time:.0f}ms")
        
    except Exception as e:
        logger.error(f"❌ Unified AI processing failed for resume {resume_id}: {e}")
        
        # Update status to failed
        try:
            with railway_db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE resumes SET processing_status = %s, processing_error = %s WHERE id = %s",
                        ('failed', str(e), resume_id)
                    )
                    conn.commit()
        except Exception:
            logger.error(f"Failed to update error status for resume {resume_id}")
