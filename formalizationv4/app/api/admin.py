"""
Admin Management API - Comprehensive admin interface endpoints.
Provides endpoints for user management, system configuration, and analytics.
"""
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import desc, and_, func, text, cast
from sqlalchemy.types import Integer, Float
from datetime import datetime, timedelta
import logging
from app import db
from app.models import User, Resume, Analysis, AnalysisQueue
from app.models.user import CreditTransaction
from app.models.admin import AdminUser, AdminAction, SystemConfiguration, AdminNotification
from app.models.queue import QueueStatus
from app.services.auth_manager import require_admin, get_current_user
from app.services.error_handler import ValidationError
# New imports for API management
from app.models.api_management import ApiKey, AccessLog, RateLimitRule, Webhook
from app.models.analytics import UsageInsight
import secrets
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')

# Standard response helpers
def _ok(data=None, status=200, **extra):
    payload = {'success': True}
    if isinstance(data, dict):
        payload.update(data)
    elif data is not None:
        payload['data'] = data
    if extra:
        payload.update(extra)
    return jsonify(payload), status


def _error(message: str, status: int = 400, code: str = 'bad_request', details=None):
    return jsonify({'success': False, 'error': {'message': message, 'code': code, 'details': details}}), status


def _paginate(items, page: int, per_page: int, total: int, **extra):
    resp = {
        'items': items,
        'page': page,
        'per_page': per_page,
        'total': total
    }
    if extra:
        resp.update(extra)
    return jsonify(resp), 200

# ============================================================================
# ADMIN HEALTH CHECK ENDPOINT
# ============================================================================

@admin_bp.route('/health', methods=['GET'])
@require_admin
def admin_health_check():
    """Admin-only health check with system statistics."""
    try:
        # Get comprehensive admin health data
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'admin_panel': 'active',
            'authenticated_user': {
                'id': str(get_current_user().id),
                'email': get_current_user().email,
                'is_admin': get_current_user().is_admin
            },
            'database': {
                'total_users': User.query.count(),
                'total_resumes': Resume.query.count(),
                'total_analyses': Analysis.query.count(),
                'queue_items': AnalysisQueue.query.count()
            },
            'recent_activity': {
                'users_today': User.query.filter(
                    User.created_at >= datetime.utcnow().date()
                ).count(),
                'analyses_today': Analysis.query.filter(
                    Analysis.created_at >= datetime.utcnow().date()
                ).count()
            }
        }
        
        return jsonify(health_data), 200
        
    except Exception as e:
        logger.error(f"Admin health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Admin health check failed',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@admin_bp.route('/auth-test', methods=['GET'])
@require_admin  
def admin_auth_test():
    """Test endpoint to verify authentication is working."""
    try:
        user = get_current_user()
        return jsonify({
            'success': True,
            'message': 'Authentication successful',
            'user': {
                'id': str(user.id),
                'email': user.email,
                'is_admin': user.is_admin
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Auth test failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@admin_bp.route('/users', methods=['GET'])
@require_admin
def get_all_users():
    """Get paginated list of all users with filtering and search."""
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Filtering parameters
        search = request.args.get('search', '').strip()
        is_admin = request.args.get('is_admin', type=bool)
        has_credits = request.args.get('has_credits', type=bool)
        is_active = request.args.get('is_active', type=bool)
        created_after = request.args.get('created_after', type=str)
        
        # Build query
        query = User.query
        
        # Search filter
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                db.or_(
                    User.email.ilike(search_filter),
                    User.first_name.ilike(search_filter),
                    User.last_name.ilike(search_filter)
                )
            )
        
        # Admin filter
        if is_admin is not None:
            query = query.filter(User.is_admin == is_admin)
        
        # Active status filter
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        else:
            # By default, only show active users unless explicitly requested
            show_inactive = request.args.get('show_inactive', 'false').lower() == 'true'
            if not show_inactive:
                query = query.filter(User.is_active == True)
        
        # Credits filter
        if has_credits is not None:
            if has_credits:
                query = query.filter(User.credits_balance > 0)
            else:
                query = query.filter(User.credits_balance <= 0)
        
        # Date filter
        if created_after:
            try:
                date_filter = datetime.fromisoformat(created_after.replace('Z', '+00:00'))
                query = query.filter(User.created_at >= date_filter)
            except ValueError:
                pass
        
        # Order by creation date (newest first)
        query = query.order_by(desc(User.created_at))
        
        # Paginate
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users = []
        for user in pagination.items:
            user_data = {
                'id': str(user.id),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_admin': user.is_admin,
                'is_active': user.is_active,
                'credits_balance': user.credits_balance,
                'total_resumes': user.resumes.count(),
                'total_analyses': sum(1 for resume in user.resumes for analysis in resume.analyses),
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None
            }
            
            # Add admin profile data if user is admin
            if user.is_admin and user.admin_profile:
                user_data['admin_profile'] = {
                    'role': user.admin_profile.role,
                    'access_level': user.admin_profile.access_level,
                    'is_active': user.admin_profile.is_active,
                    'last_activity': user.admin_profile.last_activity.isoformat() if user.admin_profile.last_activity else None
                }
            
            users.append(user_data)
        
        # Log admin action
        admin_user = get_current_user()
        if admin_user and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'view', 
                f'Viewed user list (page {page}, {len(users)} users)',
                'users'
            )
        
        meta = {
            'filters': {
                'search': search,
                'is_admin': is_admin,
                'is_active': is_active,
                'has_credits': has_credits,
                'created_after': created_after,
                'show_inactive': request.args.get('show_inactive', 'false').lower() == 'true'
            },
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
        return _paginate(users, pagination.page, pagination.per_page, pagination.total, meta=meta)
        
    except Exception as e:
        logger.error(f"Error getting user list: {str(e)}")
        return _error('Failed to retrieve user list', status=500, code='get_user_list_failed')

@admin_bp.route('/users/<user_id>', methods=['GET'])
@require_admin
def get_user_details(user_id):
    """Get detailed information for a specific user."""
    try:
        user = User.query.get_or_404(user_id)
        
        # Basic user information
        user_data = {
            'id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_admin': user.is_admin,
            'is_active': user.is_active,
            'credits_balance': user.credits_balance,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None
        }
        
        # Resume statistics
        user_data['resume_stats'] = {
            'total_resumes': user.resumes.count(),
            'recent_uploads': user.resumes.filter(
                Resume.created_at >= datetime.utcnow() - timedelta(days=30)
            ).count()
        }
        
        # Analysis statistics
        total_analyses = 0
        completed_analyses = 0
        for resume in user.resumes:
            total_analyses += resume.analyses.count()
            completed_analyses += resume.analyses.filter_by(status='completed').count()
        
        user_data['analysis_stats'] = {
            'total_analyses': total_analyses,
            'completed_analyses': completed_analyses,
            'pending_analyses': AnalysisQueue.query.filter_by(
                user_id=user.id, 
                status=QueueStatus.PENDING.value
            ).count(),
            'processing_analyses': AnalysisQueue.query.filter_by(
                user_id=user.id, 
                status=QueueStatus.PROCESSING.value
            ).count()
        }
        
        # Credit transaction history (last 10)
        recent_transactions = CreditTransaction.query.filter_by(
            user_id=user.id
        ).order_by(desc(CreditTransaction.created_at)).limit(10).all()
        
        user_data['recent_transactions'] = [
            {
                'id': str(transaction.id),
                'transaction_type': transaction.transaction_type,
                'amount': transaction.amount,
                'description': transaction.description,
                'balance_after': transaction.balance_after,
                'created_at': transaction.created_at.isoformat()
            }
            for transaction in recent_transactions
        ]
        
        # Admin profile if applicable
        if user.is_admin and user.admin_profile:
            admin_profile = user.admin_profile
            user_data['admin_profile'] = {
                'id': str(admin_profile.id),
                'role': admin_profile.role,
                'access_level': admin_profile.access_level,
                'permissions': admin_profile.permissions,
                'is_active': admin_profile.is_active,
                'last_login': admin_profile.last_login.isoformat() if admin_profile.last_login else None,
                'login_count': admin_profile.login_count,
                'failed_login_attempts': admin_profile.failed_login_attempts,
                'actions_performed': admin_profile.actions_performed,
                'created_at': admin_profile.created_at.isoformat()
            }
        
        # Log admin action
        admin_user = get_current_user()
        if admin_user and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'view', 
                f'Viewed detailed information for user {user.email}',
                'user',
                user.id
            )
        
        return jsonify(user_data)
        
    except Exception as e:
        logger.error(f"Error getting user details for {user_id}: {str(e)}")
        return _error('Failed to retrieve user details', status=500, code='get_user_details_failed')

@admin_bp.route('/users', methods=['POST'])
@require_admin
def create_user():
    """Create a new user account (admin only)."""
    try:
        data = request.get_json()
        
        if not data:
            return _error('Request body is required', status=400, code='validation_error')
        
        # Validate required fields
        required_fields = ['email', 'password']
        for field in required_fields:
            if not data.get(field):
                return _error(f'{field} is required', status=400, code='validation_error')
        
        email = data['email'].lower().strip()
        password = data['password']
        username = data.get('username', email.split('@')[0])
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        is_admin = data.get('is_admin', False)
        credits_balance = data.get('credits_balance', 10)
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return _error('User with this email already exists', status=400, code='user_exists')
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return _error('Invalid email format', status=400, code='validation_error')
        
        # Validate password strength
        from app.services.auth_manager import auth_manager
        password_errors = auth_manager.validate_password_strength(password)
        if password_errors:
            return _error(f"Password validation failed: {', '.join(password_errors)}", status=400, code='validation_error')
        
        # Validate credits balance
        if not isinstance(credits_balance, int) or credits_balance < 0:
            return _error('Credits balance must be a non-negative integer', status=400, code='validation_error')
        
        # Create new user
        user = User(
            email=email,
            username=username,
            password_hash=auth_manager.hash_password(password),
            first_name=first_name,
            last_name=last_name,
            is_admin=bool(is_admin),
            is_active=True,
            credits_balance=credits_balance
        )
        
        db.session.add(user)
        db.session.flush()  # Get user ID before creating admin profile
        
        # Create admin profile if user is admin
        if is_admin:
            admin_profile = AdminUser(
                user_id=user.id,
                role=data.get('admin_role', 'admin'),
                access_level=data.get('access_level', 50),
                created_by=get_current_user().admin_profile.id if get_current_user() and get_current_user().admin_profile else None
            )
            db.session.add(admin_profile)
        
        db.session.commit()
        
        # Log admin action
        admin_user = get_current_user()
        if admin_user and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'create',
                f'Created user {user.email} (admin: {is_admin})',
                'user',
                user.id,
                {'email': email, 'is_admin': is_admin, 'credits_balance': credits_balance}
            )
        
        # Prepare response data
        user_data = {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_admin': user.is_admin,
            'credits_balance': user.credits_balance,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat()
        }
        
        if user.admin_profile:
            user_data['admin_profile'] = {
                'role': user.admin_profile.role,
                'access_level': user.admin_profile.access_level,
                'is_active': user.admin_profile.is_active
            }
        
        return jsonify({
            'message': 'User created successfully',
            'user': user_data
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        db.session.rollback()
        return _error('Failed to create user', status=500, code='create_user_failed')

@admin_bp.route('/users/<user_id>', methods=['PUT'])
@require_admin
def update_user(user_id):
    """Update user information (admin only)."""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not data:
            return _error('Request body is required', status=400, code='validation_error')
        
        # Track changes for audit log
        changes = {}
        
        # Update basic fields
        if 'email' in data:
            new_email = data['email'].lower().strip()
            if new_email != user.email:
                # Check if new email already exists
                existing_user = User.query.filter(User.email == new_email, User.id != user.id).first()
                if existing_user:
                    return _error('Email already exists', status=400, code='email_exists')
                
                # Validate email format
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, new_email):
                    return _error('Invalid email format', status=400, code='validation_error')
                
                changes['email'] = {'old': user.email, 'new': new_email}
                user.email = new_email
        
        if 'username' in data:
            new_username = data['username'].strip()
            if new_username != user.username:
                changes['username'] = {'old': user.username, 'new': new_username}
                user.username = new_username
        
        if 'first_name' in data:
            new_first_name = data['first_name'].strip()
            if new_first_name != user.first_name:
                changes['first_name'] = {'old': user.first_name, 'new': new_first_name}
                user.first_name = new_first_name
        
        if 'last_name' in data:
            new_last_name = data['last_name'].strip()
            if new_last_name != user.last_name:
                changes['last_name'] = {'old': user.last_name, 'new': new_last_name}
                user.last_name = new_last_name
        
        if 'is_active' in data:
            new_is_active = bool(data['is_active'])
            if new_is_active != user.is_active:
                changes['is_active'] = {'old': user.is_active, 'new': new_is_active}
                user.is_active = new_is_active
        
        # Handle password change
        if 'password' in data and data['password']:
            from app.services.auth_manager import auth_manager
            new_password = data['password']
            
            # Validate password strength
            password_errors = auth_manager.validate_password_strength(new_password)
            if password_errors:
                return _error(f"Password validation failed: {', '.join(password_errors)}", status=400, code='validation_error')
            
            user.password_hash = auth_manager.hash_password(new_password)
            changes['password'] = {'changed': True}
        
        # Handle admin status change
        if 'is_admin' in data:
            new_is_admin = bool(data['is_admin'])
            if new_is_admin != user.is_admin:
                changes['is_admin'] = {'old': user.is_admin, 'new': new_is_admin}
                user.is_admin = new_is_admin
                
                if new_is_admin and not user.admin_profile:
                    # Create admin profile
                    admin_profile = AdminUser(
                        user_id=user.id,
                        role=data.get('admin_role', 'admin'),
                        access_level=data.get('access_level', 50),
                        created_by=get_current_user().admin_profile.id if get_current_user() and get_current_user().admin_profile else None
                    )
                    db.session.add(admin_profile)
                elif not new_is_admin and user.admin_profile:
                    # Deactivate admin profile
                    user.admin_profile.is_active = False
        
        # Update admin profile if user is admin and profile data provided
        if user.is_admin and user.admin_profile:
            if 'admin_role' in data:
                new_role = data['admin_role']
                if new_role != user.admin_profile.role:
                    changes['admin_role'] = {'old': user.admin_profile.role, 'new': new_role}
                    user.admin_profile.role = new_role
            
            if 'access_level' in data:
                new_access_level = int(data['access_level'])
                if new_access_level != user.admin_profile.access_level:
                    changes['access_level'] = {'old': user.admin_profile.access_level, 'new': new_access_level}
                    user.admin_profile.access_level = new_access_level
        
        db.session.commit()
        
        # Log admin action if changes were made
        if changes:
            admin_user = get_current_user()
            if admin_user and admin_user.admin_profile:
                admin_user.admin_profile.log_action(
                    'update',
                    f'Updated user {user.email}',
                    'user',
                    user.id,
                    {'changes': changes}
                )
        
        # Prepare response data
        user_data = {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_admin': user.is_admin,
            'credits_balance': user.credits_balance,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if user.admin_profile:
            user_data['admin_profile'] = {
                'role': user.admin_profile.role,
                'access_level': user.admin_profile.access_level,
                'is_active': user.admin_profile.is_active
            }
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user_data,
            'changes_made': len(changes) > 0
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        db.session.rollback()
        return _error('Failed to update user', status=500, code='update_user_failed')

@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    """Delete user account (admin only). Uses soft delete for safety."""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent self-deletion
        current_admin = get_current_user()
        if current_admin and str(current_admin.id) == str(user_id):
            return _error('Cannot delete your own account', status=400, code='self_deletion_forbidden')
        
        # Prevent deletion of the last admin
        if user.is_admin:
            admin_count = User.query.filter_by(is_admin=True, is_active=True).count()
            if admin_count <= 1:
                return _error('Cannot delete the last active admin user', status=400, code='last_admin_deletion_forbidden')
        
        # Check for hard delete vs soft delete
        hard_delete = request.args.get('hard_delete', 'false').lower() == 'true'
        
        if hard_delete:
            # Hard delete - remove from database completely
            # First, handle related records
            
            # Store user info for logging before deletion
            user_email = user.email
            user_was_admin = user.is_admin
            
            # Delete admin profile if exists
            if user.admin_profile:
                db.session.delete(user.admin_profile)
            
            # Delete credit transactions
            from app.models.user import CreditTransaction
            CreditTransaction.query.filter_by(user_id=user.id).delete()
            
            # Delete resumes and related analyses
            for resume in user.resumes:
                # Delete analyses first
                for analysis in resume.analyses:
                    db.session.delete(analysis)
                db.session.delete(resume)
            
            # Delete queue items
            AnalysisQueue.query.filter_by(user_id=user.id).delete()
            
            # Finally delete the user
            db.session.delete(user)
            db.session.commit()
            
            # Log admin action
            if current_admin and current_admin.admin_profile:
                current_admin.admin_profile.log_action(
                    'hard_delete',
                    f'Hard deleted user {user_email} (was admin: {user_was_admin})',
                    'user',
                    None,  # User ID no longer exists
                    {'email': user_email, 'was_admin': user_was_admin, 'deletion_type': 'hard'}
                )
            
            return jsonify({
                'message': 'User permanently deleted',
                'user_email': user_email,
                'deletion_type': 'hard'
            }), 200
            
        else:
            # Soft delete - deactivate user
            user.is_active = False
            
            # Also deactivate admin profile if exists
            if user.admin_profile:
                user.admin_profile.is_active = False
            
            db.session.commit()
            
            # Log admin action
            if current_admin and current_admin.admin_profile:
                current_admin.admin_profile.log_action(
                    'soft_delete',
                    f'Deactivated user {user.email} (admin: {user.is_admin})',
                    'user',
                    user.id,
                    {'email': user.email, 'is_admin': user.is_admin, 'deletion_type': 'soft'}
                )
            
            return jsonify({
                'message': 'User deactivated successfully',
                'user_id': str(user.id),
                'user_email': user.email,
                'deletion_type': 'soft',
                'note': 'User has been deactivated but data is preserved. Use hard_delete=true to permanently remove.'
            }), 200
        
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        db.session.rollback()
        return _error('Failed to delete user', status=500, code='delete_user_failed')

@admin_bp.route('/users/<user_id>/restore', methods=['POST'])
@require_admin
def restore_user(user_id):
    """Restore a soft-deleted user account (admin only)."""
    try:
        user = User.query.get_or_404(user_id)
        
        if user.is_active:
            return _error('User is already active', status=400, code='user_already_active')
        
        # Restore user
        user.is_active = True
        
        # Also restore admin profile if user is admin
        if user.is_admin and user.admin_profile:
            user.admin_profile.is_active = True
        
        db.session.commit()
        
        # Log admin action
        admin_user = get_current_user()
        if admin_user and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'restore',
                f'Restored user {user.email} (admin: {user.is_admin})',
                'user',
                user.id,
                {'email': user.email, 'is_admin': user.is_admin}
            )
        
        return jsonify({
            'message': 'User restored successfully',
            'user_id': str(user.id),
            'user_email': user.email,
            'is_admin': user.is_admin
        }), 200
        
    except Exception as e:
        logger.error(f"Error restoring user {user_id}: {str(e)}")
        db.session.rollback()
        return _error('Failed to restore user', status=500, code='restore_user_failed')

@admin_bp.route('/users/bulk-operations', methods=['POST'])
@require_admin
def bulk_user_operations():
    """Perform bulk operations on multiple users (admin only)."""
    try:
        data = request.get_json()
        
        if not data:
            return _error('Request body is required', status=400, code='validation_error')
        
        operation = data.get('operation')
        user_ids = data.get('user_ids', [])
        
        if not operation or not user_ids:
            return _error('Operation and user_ids are required', status=400, code='validation_error')
        
        if not isinstance(user_ids, list):
            return _error('user_ids must be a list', status=400, code='validation_error')
        
        # Validate operation
        valid_operations = ['activate', 'deactivate', 'delete', 'add_credits', 'remove_credits']
        if operation not in valid_operations:
            return _error(f'Invalid operation. Must be one of: {", ".join(valid_operations)}', 
                         status=400, code='validation_error')
        
        # Get users
        users = User.query.filter(User.id.in_(user_ids)).all()
        found_user_ids = [str(user.id) for user in users]
        missing_user_ids = [uid for uid in user_ids if uid not in found_user_ids]
        
        if missing_user_ids:
            return _error(f'Users not found: {", ".join(missing_user_ids)}', 
                         status=404, code='users_not_found')
        
        # Prevent operations on self
        current_admin = get_current_user()
        current_admin_id = str(current_admin.id) if current_admin else None
        if current_admin_id in user_ids:
            return _error('Cannot perform bulk operations on your own account', 
                         status=400, code='self_operation_forbidden')
        
        results = {'success': [], 'failed': [], 'skipped': []}
        
        for user in users:
            try:
                user_id = str(user.id)
                
                if operation == 'activate':
                    if user.is_active:
                        results['skipped'].append({'user_id': user_id, 'reason': 'already active'})
                    else:
                        user.is_active = True
                        if user.admin_profile:
                            user.admin_profile.is_active = True
                        results['success'].append({'user_id': user_id, 'action': 'activated'})
                
                elif operation == 'deactivate':
                    if not user.is_active:
                        results['skipped'].append({'user_id': user_id, 'reason': 'already inactive'})
                    elif user.is_admin:
                        # Check if this would leave no active admins
                        active_admins = User.query.filter_by(is_admin=True, is_active=True).count()
                        if active_admins <= 1:
                            results['failed'].append({'user_id': user_id, 'reason': 'cannot deactivate last admin'})
                            continue
                        
                        user.is_active = False
                        if user.admin_profile:
                            user.admin_profile.is_active = False
                        results['success'].append({'user_id': user_id, 'action': 'deactivated'})
                    else:
                        user.is_active = False
                        results['success'].append({'user_id': user_id, 'action': 'deactivated'})
                
                elif operation == 'delete':
                    # Only soft delete in bulk operations for safety
                    if not user.is_active:
                        results['skipped'].append({'user_id': user_id, 'reason': 'already inactive'})
                    elif user.is_admin:
                        # Check if this would leave no active admins
                        active_admins = User.query.filter_by(is_admin=True, is_active=True).count()
                        if active_admins <= 1:
                            results['failed'].append({'user_id': user_id, 'reason': 'cannot delete last admin'})
                            continue
                        
                        user.is_active = False
                        if user.admin_profile:
                            user.admin_profile.is_active = False
                        results['success'].append({'user_id': user_id, 'action': 'soft deleted'})
                    else:
                        user.is_active = False
                        results['success'].append({'user_id': user_id, 'action': 'soft deleted'})
                
                elif operation == 'add_credits':
                    credits = data.get('credits', 0)
                    if not isinstance(credits, int) or credits <= 0:
                        results['failed'].append({'user_id': user_id, 'reason': 'invalid credits amount'})
                        continue
                    
                    old_balance = user.credits_balance
                    user.credits_balance += credits
                    
                    # Create credit transaction
                    from app.models.user import CreditTransaction
                    transaction = CreditTransaction(
                        user_id=user.id,
                        transaction_type='credit',
                        amount=credits,
                        description=f'Bulk credit addition by admin',
                        balance_after=user.credits_balance
                    )
                    db.session.add(transaction)
                    
                    results['success'].append({
                        'user_id': user_id, 
                        'action': f'added {credits} credits',
                        'old_balance': old_balance,
                        'new_balance': user.credits_balance
                    })
                
                elif operation == 'remove_credits':
                    credits = data.get('credits', 0)
                    if not isinstance(credits, int) or credits <= 0:
                        results['failed'].append({'user_id': user_id, 'reason': 'invalid credits amount'})
                        continue
                    
                    if user.credits_balance < credits:
                        results['failed'].append({'user_id': user_id, 'reason': 'insufficient credits'})
                        continue
                    
                    old_balance = user.credits_balance
                    user.credits_balance -= credits
                    
                    # Create credit transaction
                    from app.models.user import CreditTransaction
                    transaction = CreditTransaction(
                        user_id=user.id,
                        transaction_type='debit',
                        amount=credits,
                        description=f'Bulk credit removal by admin',
                        balance_after=user.credits_balance
                    )
                    db.session.add(transaction)
                    
                    results['success'].append({
                        'user_id': user_id, 
                        'action': f'removed {credits} credits',
                        'old_balance': old_balance,
                        'new_balance': user.credits_balance
                    })
                
            except Exception as e:
                results['failed'].append({'user_id': user_id, 'reason': str(e)})
        
        db.session.commit()
        
        # Log admin action
        if current_admin and current_admin.admin_profile:
            current_admin.admin_profile.log_action(
                'bulk_operation',
                f'Performed bulk {operation} on {len(users)} users',
                'user',
                None,
                {
                    'operation': operation,
                    'user_count': len(users),
                    'results': results
                }
            )
        
        return jsonify({
            'message': f'Bulk {operation} operation completed',
            'operation': operation,
            'total_users': len(users),
            'results': results,
            'summary': {
                'successful': len(results['success']),
                'failed': len(results['failed']),
                'skipped': len(results['skipped'])
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in bulk user operations: {str(e)}")
        db.session.rollback()
        return _error('Failed to perform bulk operations', status=500, code='bulk_operations_failed')

@admin_bp.route('/users/<user_id>/credits', methods=['POST'])
@require_admin
def modify_user_credits(user_id):
    """Add or remove credits from a user's account."""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not data or 'amount' not in data:
            return _error('Amount is required', status=400, code='validation_error')
        
        amount = data['amount']
        description = data.get('description', 'Admin credit adjustment')
        
        if not isinstance(amount, int) or amount == 0:
            return _error('Amount must be a non-zero integer', status=400, code='validation_error')
        
        # Update user credits
        old_balance = user.credits_balance
        user.credits_balance += amount
        
        if user.credits_balance < 0:
            return _error('Cannot reduce credits below zero', status=400, code='credit_limit_exceeded')
        
        # Create credit transaction
        transaction = CreditTransaction(
            user_id=user.id,
            transaction_type='credit' if amount > 0 else 'debit',
            amount=abs(amount),
            description=description,
            balance_after=user.credits_balance
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        # Log admin action
        admin_user = get_current_user()
        if admin_user and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'credit_modification',
                f'Modified credits for {user.email}: {amount:+d} (balance: {old_balance} → {user.credits_balance})',
                'user',
                user.id,
                {'old_balance': old_balance, 'new_balance': user.credits_balance, 'amount': amount}
            )
        
        return jsonify({
            'message': f'Credits {"added" if amount > 0 else "removed"} successfully',
            'old_balance': old_balance,
            'new_balance': user.credits_balance,
            'amount_changed': amount,
            'transaction_id': str(transaction.id)
        })
        
    except Exception as e:
        logger.error(f"Error modifying credits for user {user_id}: {str(e)}")
        db.session.rollback()
        return _error('Failed to modify user credits', status=500, code='modify_user_credits_failed')

@admin_bp.route('/users/<user_id>/admin-status', methods=['POST'])
@require_admin
def toggle_user_admin_status(user_id):
    """Grant or revoke admin privileges for a user."""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        make_admin = data.get('make_admin', False)
        role = data.get('role', 'admin')
        access_level = data.get('access_level', 50)
        
        if make_admin and not user.is_admin:
            # Grant admin privileges
            user.is_admin = True
            
            # Create admin profile
            admin_profile = AdminUser(
                user_id=user.id,
                role=role,
                access_level=access_level,
                created_by=get_current_user().admin_profile.id if get_current_user() and get_current_user().admin_profile else None
            )
            db.session.add(admin_profile)
            
            action = f'Granted admin privileges (role: {role}, level: {access_level})'
            
        elif not make_admin and user.is_admin:
            # Revoke admin privileges
            user.is_admin = False
            
            # Deactivate admin profile
            if user.admin_profile:
                user.admin_profile.is_active = False
            
            action = 'Revoked admin privileges'
            
        else:
            return _error('No change in admin status required', status=400, code='no_status_change')
        
        db.session.commit()
        
        # Log admin action
        admin_user = get_current_user()
        if admin_user and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'admin_status_change',
                f'{action} for {user.email}',
                'user',
                user.id,
                {'make_admin': make_admin, 'role': role, 'access_level': access_level}
            )
        
        return jsonify({
            'message': f'User admin status updated successfully',
            'user_id': str(user.id),
            'is_admin': user.is_admin,
            'admin_profile': user.admin_profile.to_dict() if user.admin_profile else None
        })
        
    except Exception as e:
        logger.error(f"Error updating admin status for user {user_id}: {str(e)}")
        db.session.rollback()
        return _error('Failed to update admin status', status=500, code='toggle_user_admin_status_failed')

# ============================================================================
# SYSTEM CONFIGURATION ENDPOINTS
# ============================================================================

@admin_bp.route('/system/config', methods=['GET'])
@require_admin
def get_system_configuration():
    """Get all system configuration settings."""
    try:
        category = request.args.get('category')
        
        query = SystemConfiguration.query
        if category:
            query = query.filter_by(category=category)
        
        configs = query.order_by(SystemConfiguration.category, SystemConfiguration.key).all()
        
        # Group configurations by category
        config_data = {}
        for config in configs:
            if config.category not in config_data:
                config_data[config.category] = []
            
            config_data[config.category].append(config.to_dict(show_sensitive=False))
        
        # Log admin action
        admin_user = get_current_user()
        if admin_user and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'view',
                f'Viewed system configuration ({len(configs)} settings)',
                'system_config'
            )
        
        return jsonify({
            'configurations': config_data,
            'categories': list(config_data.keys()),
            'total_configs': len(configs)
        })
        
    except Exception as e:
        logger.error(f"Error getting system configuration: {str(e)}")
        return _error('Failed to retrieve system configuration', status=500, code='get_system_configuration_failed')

@admin_bp.route('/system/config', methods=['POST'])
@require_admin
def update_system_configuration():
    """Update or create system configuration setting."""
    try:
        data = request.get_json()
        
        if not data or 'key' not in data or 'value' not in data:
            return _error('Key and value are required', status=400, code='validation_error')
        
        key = data['key']
        value = data['value']
        description = data.get('description', '')
        category = data.get('category', 'general')
        is_sensitive = data.get('is_sensitive', False)
        requires_restart = data.get('requires_restart', False)
        
        # Find existing configuration or create new one
        config = SystemConfiguration.query.filter_by(key=key).first()
        
        if config:
            old_value = config.value
            config.value = value
            config.description = description
            config.category = category
            config.is_sensitive = is_sensitive
            config.requires_restart = requires_restart
            config.modified_by = get_current_user().admin_profile.id if get_current_user() and get_current_user().admin_profile else None
            config.updated_at = datetime.utcnow()
            action = 'updated'
        else:
            config = SystemConfiguration(
                key=key,
                value=value,
                description=description,
                category=category,
                is_sensitive=is_sensitive,
                requires_restart=requires_restart,
                modified_by=get_current_user().admin_profile.id if get_current_user() and get_current_user().admin_profile else None
            )
            db.session.add(config)
            old_value = None
            action = 'created'
        
        db.session.commit()
        
        # Log admin action
        admin_user = get_current_user()
        if admin_user and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'config_update',
                f'Configuration {key} {action}',
                'system_config',
                config.id,
                {'old_value': old_value, 'new_value': value, 'category': category}
            )
        
        return jsonify({
            'message': f'Configuration {action} successfully',
            'config': config.to_dict(show_sensitive=True),
            'requires_restart': config.requires_restart
        })
        
    except Exception as e:
        logger.error(f"Error updating system configuration: {str(e)}")
        db.session.rollback()
        return _error('Failed to update system configuration', status=500, code='update_system_configuration_failed')

# ============================================================================
# SYSTEM ANALYTICS ENDPOINTS
# ============================================================================

@admin_bp.route('/analytics/dashboard', methods=['GET'])
@require_admin
def get_admin_dashboard_analytics():
    """Get comprehensive analytics for admin dashboard."""
    try:
        # Time range parameters
        days = request.args.get('days', 7, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # User analytics
        total_users = User.query.count()
        new_users = User.query.filter(User.created_at >= start_date).count()
        admin_users = User.query.filter_by(is_admin=True).count()
        active_users = User.query.filter(
            User.last_login >= start_date
        ).count() if hasattr(User, 'last_login') else 0
        
        # Resume analytics
        total_resumes = Resume.query.count()
        new_resumes = Resume.query.filter(Resume.created_at >= start_date).count()
        
        # Analysis analytics
        total_analyses = Analysis.query.count()
        completed_analyses = Analysis.query.filter_by(status='completed').count()
        pending_analyses = AnalysisQueue.query.filter_by(status=QueueStatus.PENDING.value).count()
        processing_analyses = AnalysisQueue.query.filter_by(status=QueueStatus.PROCESSING.value).count()
        failed_analyses = AnalysisQueue.query.filter_by(status=QueueStatus.FAILED.value).count()
        
        # Queue performance
        avg_processing_time = db.session.query(
            func.avg(
                func.extract('epoch', AnalysisQueue.completed_at - AnalysisQueue.started_at)
            )
        ).filter(
            and_(
                AnalysisQueue.status == QueueStatus.COMPLETED.value,
                AnalysisQueue.completed_at.isnot(None),
                AnalysisQueue.started_at.isnot(None)
            )
        ).scalar() or 0
        
        # Credit analytics
        total_credits_issued = db.session.query(
            func.sum(CreditTransaction.amount)
        ).filter_by(transaction_type='credit').scalar() or 0
        
        total_credits_used = db.session.query(
            func.sum(CreditTransaction.amount)
        ).filter_by(transaction_type='debit').scalar() or 0
        
        # Recent activity
        recent_users = User.query.order_by(desc(User.created_at)).limit(5).all()
        recent_analyses = AnalysisQueue.query.filter_by(
            status=QueueStatus.COMPLETED.value
        ).order_by(desc(AnalysisQueue.completed_at)).limit(5).all()
        
        # System health
        from app.services.database_manager import DatabaseManager
        db_manager = DatabaseManager(current_app, db)
        db_health = db_manager.get_database_health() or {}
        system_health = {
            'database_status': db_health.get('status', 'unknown'),
            'queue_health': 'healthy' if pending_analyses < 100 and failed_analyses < 10 else 'warning',
            'processing_rate': f"{avg_processing_time:.1f}s" if avg_processing_time else "N/A"
        }
        
        # Daily analytics for the past week
        daily_stats = []
        for i in range(days):
            day_start = (datetime.utcnow() - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_stats = {
                'date': day_start.strftime('%Y-%m-%d'),
                'new_users': User.query.filter(
                    and_(User.created_at >= day_start, User.created_at < day_end)
                ).count(),
                'new_resumes': Resume.query.filter(
                    and_(Resume.created_at >= day_start, Resume.created_at < day_end)
                ).count(),
                'completed_analyses': AnalysisQueue.query.filter(
                    and_(
                        AnalysisQueue.status == QueueStatus.COMPLETED.value,
                        AnalysisQueue.completed_at >= day_start,
                        AnalysisQueue.completed_at < day_end
                    )
                ).count()
            }
            daily_stats.append(day_stats)
        
        # Log admin action
        admin_user = get_current_user()
        if admin_user and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'view',
                'Viewed admin dashboard analytics',
                'analytics'
            )
        
        return jsonify({
            'summary': {
                'total_users': total_users,
                'new_users': new_users,
                'admin_users': admin_users,
                'active_users': active_users,
                'total_resumes': total_resumes,
                'new_resumes': new_resumes,
                'total_analyses': total_analyses,
                'completed_analyses': completed_analyses,
                'pending_analyses': pending_analyses,
                'processing_analyses': processing_analyses,
                'failed_analyses': failed_analyses,
                'avg_processing_time': round(avg_processing_time, 2),
                'total_credits_issued': total_credits_issued,
                'total_credits_used': total_credits_used,
                'credits_remaining': total_credits_issued - total_credits_used
            },
            'recent_activity': {
                'recent_users': [
                    {
                        'id': str(user.id),
                        'email': user.email,
                        'name': f"{user.first_name} {user.last_name}",
                        'created_at': user.created_at.isoformat()
                    }
                    for user in recent_users
                ],
                'recent_analyses': [
                    {
                        'id': str(analysis.id),
                        'user_email': analysis.user.email if analysis.user else 'Unknown',
                        'status': analysis.status,
                        'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None
                    }
                    for analysis in recent_analyses
                ]
            },
            'daily_stats': daily_stats,
            'system_health': system_health,
            'period_days': days,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting admin dashboard analytics: {str(e)}")
        return _error('Failed to retrieve dashboard analytics', status=500, code='get_dashboard_analytics_failed')

# ============================================================================
# ADMIN ACTIONS & AUDIT LOG ENDPOINTS
# ============================================================================

@admin_bp.route('/audit-log', methods=['GET'])
@require_admin
def get_audit_log():
    """Get paginated audit log of admin actions."""
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        
        # Filtering parameters
        admin_user_id = request.args.get('admin_user_id')
        action_type = request.args.get('action_type')
        target_resource = request.args.get('target_resource')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query
        query = AdminAction.query
        
        if admin_user_id:
            query = query.filter_by(admin_user_id=admin_user_id)
        
        if action_type:
            query = query.filter_by(action_type=action_type)
        
        if target_resource:
            query = query.filter_by(target_resource=target_resource)
        
        if date_from:
            try:
                date_filter = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                query = query.filter(AdminAction.created_at >= date_filter)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_filter = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                query = query.filter(AdminAction.created_at <= date_filter)
            except ValueError:
                pass
        
        # Order by creation date (newest first)
        query = query.order_by(desc(AdminAction.created_at))
        
        # Paginate
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        actions = []
        for action in pagination.items:
            action_data = action.to_dict()
            
            # Add admin user info
            if action.admin_user:
                action_data['admin_user'] = {
                    'email': action.admin_user.user.email if action.admin_user.user else 'Unknown',
                    'role': action.admin_user.role
                }
            
            actions.append(action_data)
        
        return _paginate(actions, pagination.page, pagination.per_page, pagination.total)
        
    except Exception as e:
        logger.error(f"Error getting audit log: {str(e)}")
        return _error('Failed to retrieve audit log', status=500, code='get_audit_log_failed')

# ============================================================================
# ADMIN NOTIFICATIONS ENDPOINTS
# ============================================================================

@admin_bp.route('/notifications', methods=['GET'])
@require_admin
def get_admin_notifications():
    """Get admin notifications."""
    try:
        admin_user = get_current_user()
        if not admin_user or not admin_user.admin_profile:
            return _error('Admin profile required', status=403, code='admin_profile_required')
        
        # Get unread notifications first, then recent read ones
        unread_notifications = AdminNotification.query.filter_by(
            admin_user_id=admin_user.admin_profile.id,
            is_read=False,
            is_dismissed=False
        ).order_by(desc(AdminNotification.created_at)).all()
        
        read_notifications = AdminNotification.query.filter_by(
            admin_user_id=admin_user.admin_profile.id,
            is_read=True,
            is_dismissed=False
        ).order_by(desc(AdminNotification.created_at)).limit(20).all()
        
        all_notifications = unread_notifications + read_notifications
        
        notifications_data = [notification.to_dict() for notification in all_notifications]
        
        return jsonify({
            'notifications': notifications_data,
            'unread_count': len(unread_notifications),
            'total_count': len(all_notifications)
        })
        
    except Exception as e:
        logger.error(f"Error getting admin notifications: {str(e)}")
        return _error('Failed to retrieve notifications', status=500, code='get_notifications_failed')

@admin_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@require_admin
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    try:
        notification = AdminNotification.query.get_or_404(notification_id)
        
        # Verify notification belongs to current admin
        admin_user = get_current_user()
        if not admin_user or not admin_user.admin_profile or notification.admin_user_id != admin_user.admin_profile.id:
            return _error('Access denied', status=403, code='access_denied')
        
        notification.mark_as_read()
        db.session.commit()
        
        return jsonify({
            'message': 'Notification marked as read',
            'notification': notification.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        db.session.rollback()
        return _error('Failed to mark notification as read', status=500, code='mark_notification_read_failed')

# ============================================================================
# HR TEMPLATES AUTO-FIX ENDPOINTS
# ============================================================================

@admin_bp.route('/hr-templates/diagnose', methods=['GET'])
@require_admin
def diagnose_hr_templates():
    """Diagnose HR templates setup issues."""
    try:
        from app.services.hr_templates_autofix import HRTemplatesAutoFixService
        
        issues = HRTemplatesAutoFixService.detect_issues()
        
        return jsonify({
            'issues_detected': issues,
            'has_issues': any(issues.values()),
            'recommendations': _get_fix_recommendations(issues)
        })
        
    except Exception as e:
        logger.error(f"Error diagnosing HR templates: {str(e)}")
        return _error('Failed to diagnose HR templates', status=500, code='diagnose_hr_templates_failed')

@admin_bp.route('/hr-templates/auto-fix', methods=['POST'])
@require_admin
def auto_fix_hr_templates():
    """Automatically fix detected HR templates issues."""
    try:
        from app.services.hr_templates_autofix import HRTemplatesAutoFixService
        
        results = HRTemplatesAutoFixService.auto_fix_all_issues()
        
        # Log admin action
        admin_user = get_current_user()
        if admin_user and admin_user.admin_profile:
            action = AdminAction(
                admin_user_id=admin_user.admin_profile.id,
                action='hr_templates_auto_fix',
                target_type='system',
                details=results,
                ip_address=request.remote_addr
            )
            db.session.add(action)
            db.session.commit()
        
        status_code = 200 if results.get('overall_success') else 207  # 207 = Multi-Status
        
        return jsonify({
            'success': results.get('overall_success', False),
            'message': results.get('message', 'Auto-fix completed'),
            'results': results
        }), status_code
        
    except Exception as e:
        logger.error(f"Error auto-fixing HR templates: {str(e)}")
        return _error('Failed to auto-fix HR templates', status=500, code='auto_fix_hr_templates_failed')

def _get_fix_recommendations(issues):
    """Get recommendations for fixing detected issues."""
    recommendations = []
    
    if issues.get('table_missing'):
        recommendations.append({
            'issue': 'hr_templates table missing',
            'fix': 'Run database migrations',
            'command': 'flask db upgrade'
        })
    
    if issues.get('user_id_constraint'):
        recommendations.append({
            'issue': 'user_id column does not allow NULL values',
            'fix': 'Use auto-fix endpoint to update schema',
            'api': 'POST /api/v1/admin/hr-templates/auto-fix'
        })
    
    if issues.get('missing_system_templates'):
        recommendations.append({
            'issue': 'No system templates found',
            'fix': 'Use auto-fix endpoint to create default templates',
            'api': 'POST /api/v1/admin/hr-templates/auto-fix'
        })
    
    if issues.get('foreign_key_issues'):
        recommendations.append({
            'issue': 'Foreign key constraint issues',
            'fix': 'Check database schema and run migrations',
            'command': 'flask db upgrade'
        })
    
    return recommendations

# ============================================================================
# CREDIT MANAGEMENT ENDPOINTS
# ============================================================================

@admin_bp.route('/credit-transactions', methods=['GET'])
@require_admin
def get_credit_transactions():
    """Get paginated list of credit transactions."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        user_id = request.args.get('user_id')
        transaction_type = request.args.get('transaction_type')
        
        # Build query
        query = CreditTransaction.query
        
        # Apply filters
        if user_id:
            query = query.filter(CreditTransaction.user_id == user_id)
        if transaction_type:
            query = query.filter(CreditTransaction.transaction_type == transaction_type)
        
        # Order by creation time descending and paginate
        pagination = query.order_by(CreditTransaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format transactions data
        transactions_data = []
        for transaction in pagination.items:
            transaction_data = {
                'id': str(transaction.id),
                'user_id': str(transaction.user_id),
                'user_email': transaction.user.email if transaction.user else 'Unknown',
                'transaction_type': transaction.transaction_type,
                'amount': transaction.amount,
                'description': transaction.description,
                'balance_after': transaction.balance_after,
                'created_at': transaction.created_at.isoformat()
            }
            transactions_data.append(transaction_data)
        
        # Log admin action
        admin_user = get_current_user()
        if admin_user and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'view',
                'Viewed credit transactions',
                'credit_management'
            )
        
        return _paginate(transactions_data, pagination.page, pagination.per_page, pagination.total)
        
    except Exception as e:
        logger.error(f"Error getting credit transactions: {str(e)}")
        return _error('Failed to retrieve credit transactions', status=500, code='get_credit_transactions_failed')

@admin_bp.route('/analytics/credits', methods=['GET'])
@require_admin
def get_credit_analytics():
    """Get comprehensive credit system analytics."""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total credits issued and used
        total_credits_issued = db.session.query(
            func.sum(CreditTransaction.amount)
        ).filter(
            CreditTransaction.transaction_type == 'credit'
        ).scalar() or 0
        
        total_credits_used = db.session.query(
            func.sum(CreditTransaction.amount)
        ).filter(
            CreditTransaction.transaction_type == 'debit'
        ).scalar() or 0
        
        # Credits in period
        period_credits_issued = db.session.query(
            func.sum(CreditTransaction.amount)
        ).filter(
            and_(
                CreditTransaction.transaction_type == 'credit',
                CreditTransaction.created_at >= start_date
            )
        ).scalar() or 0
        
        period_credits_used = db.session.query(
            func.sum(CreditTransaction.amount)
        ).filter(
            and_(
                CreditTransaction.transaction_type == 'debit',
                CreditTransaction.created_at >= start_date
            )
        ).scalar() or 0
        
        # Daily credit usage trends
        daily_usage = db.session.query(
            func.date(CreditTransaction.created_at).label('date'),
            func.sum(func.case(
                [(CreditTransaction.transaction_type == 'credit', CreditTransaction.amount)], 
                else_=0
            )).label('credits_issued'),
            func.sum(func.case(
                [(CreditTransaction.transaction_type == 'debit', CreditTransaction.amount)], 
                else_=0
            )).label('credits_used')
        ).filter(
            CreditTransaction.created_at >= start_date
        ).group_by('date').order_by('date').all()
        
        # Top credit users
        top_users = db.session.query(
            CreditTransaction.user_id,
            User.email,
            func.sum(CreditTransaction.amount).label('total_credits_used')
        ).join(User).filter(
            and_(
                CreditTransaction.transaction_type == 'debit',
                CreditTransaction.created_at >= start_date
            )
        ).group_by(CreditTransaction.user_id, User.email).order_by(
            desc('total_credits_used')
        ).limit(10).all()
        
        # Credit distribution analysis
        user_credit_balances = db.session.query(
            User.credits_balance,
            func.count().label('user_count')
        ).group_by(User.credits_balance).order_by(User.credits_balance).all()
        
        # Calculate averages and statistics
        avg_credits_per_user = db.session.query(
            func.avg(User.credits_balance)
        ).scalar() or 0
        
        median_credits = db.session.query(
            func.percentile_cont(0.5).within_group(User.credits_balance)
        ).scalar() or 0
        
        # Users with zero credits
        users_with_zero_credits = User.query.filter(User.credits_balance <= 0).count()
        total_users = User.query.count()
        
        # Recent transaction activity
        recent_transactions = CreditTransaction.query.filter(
            CreditTransaction.created_at >= start_date
        ).order_by(desc(CreditTransaction.created_at)).limit(20).all()
        
        # Build response
        analytics_data = {
            'period_days': days,
            'summary': {
                'total_credits_issued': total_credits_issued,
                'total_credits_used': abs(total_credits_used),
                'credits_remaining': total_credits_issued + total_credits_used,  # debit is negative
                'period_credits_issued': period_credits_issued,
                'period_credits_used': abs(period_credits_used),
                'avg_credits_per_user': round(avg_credits_per_user, 2),
                'median_credits_per_user': round(median_credits, 2),
                'users_with_zero_credits': users_with_zero_credits,
                'zero_credits_percentage': round((users_with_zero_credits / total_users * 100), 2) if total_users > 0 else 0
            },
            'daily_trends': [
                {
                    'date': str(date),
                    'credits_issued': int(issued or 0),
                    'credits_used': abs(int(used or 0)),
                    'net_change': int((issued or 0) + (used or 0))
                }
                for date, issued, used in daily_usage
            ],
            'top_users': [
                {
                    'user_id': str(user_id),
                    'email': email,
                    'credits_used': abs(int(credits_used))
                }
                for user_id, email, credits_used in top_users
            ],
            'credit_distribution': [
                {
                    'balance': int(balance),
                    'user_count': int(count)
                }
                for balance, count in user_credit_balances
            ],
            'recent_transactions': [
                {
                    'id': str(txn.id),
                    'user_email': txn.user.email if txn.user else 'Unknown',
                    'type': txn.transaction_type,
                    'amount': txn.amount,
                    'description': txn.description,
                    'created_at': txn.created_at.isoformat()
                }
                for txn in recent_transactions
            ],
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Log admin action
        admin_user = get_current_user()
        if admin_user and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'view',
                'Viewed credit analytics',
                'credit_analytics'
            )
        
        return jsonify({
            'success': True,
            'analytics': analytics_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting credit analytics: {str(e)}")
        return _error('Failed to retrieve credit analytics', status=500, code='get_credit_analytics_failed')

# ============================================================================
# BACKUP MANAGEMENT ENDPOINTS
# ============================================================================

@admin_bp.route('/backups', methods=['GET'])
@require_admin
def get_backup_list():
    """Get list of available backups."""
    try:
        # This is a placeholder for backup functionality
        # In production, you would integrate with your backup system
        backups = [
            {
                'id': 'backup_001',
                'name': 'Daily Backup - ' + datetime.utcnow().strftime('%Y-%m-%d'),
                'type': 'automated',
                'size': '45.2 MB',
                'created_at': datetime.utcnow().isoformat(),
                'status': 'completed'
            }
        ]
        
        # Log admin action
        admin_user = get_current_user()
        if admin_user and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'view',
                'Viewed backup list',
                'backup_management'
            )
        
        return jsonify({
            'success': True,
            'backups': backups,
            'message': 'Backup management is in development. Integration with backup service pending.'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting backup list: {str(e)}")
        return _error('Failed to retrieve backup list', status=500, code='get_backup_list_failed')

@admin_bp.route('/backups/create', methods=['POST'])
@require_admin
def create_backup():
    """Create a new backup."""
    try:
        # Placeholder for backup creation
        backup_id = f"manual_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Emit initial backup progress (best-effort)
        try:
            if hasattr(current_app, 'websocket_service') and current_app.websocket_service:
                current_app.websocket_service.socketio.emit('backup_progress', {
                    'backup_id': backup_id,
                    'status': 'started',
                    'progress_pct': 0,
                    'timestamp': datetime.utcnow().isoformat()
                }, room='admin_dashboard')
        except Exception:
            pass

        # Log admin action
        admin_user = get_current_user()
        if admin_user and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'create',
                f'Initiated manual backup: {backup_id}',
                'backup_management'
            )

        return jsonify({
            'success': True,
            'backup_id': backup_id,
            'message': 'Backup creation initiated. This feature is in development.',
            'status': 'pending'
        }), 202

    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        return _error('Failed to create backup', status=500, code='create_backup_failed')

# Register error handlers
# ============================================================================
# MISSING ADMIN ENDPOINTS - Part 5: Feature Flags (New Functionality)
# ============================================================================

@admin_bp.route('/feature-flags', methods=['GET', 'POST', 'PUT'])
@require_admin
def manage_feature_flags():
    """Manage system feature flags."""
    try:
        from app.services.analytics_service import analytics_service
        import traceback
        
        if request.method == 'GET':
            # Get all feature flags
            feature_flags = {
                'ai_analysis': {
                    'enabled': True,
                    'description': 'AI-powered resume analysis',
                    'last_modified': datetime.utcnow().isoformat(),
                    'modified_by': 'system'
                },
                'websocket_connections': {
                    'enabled': True,
                    'description': 'Real-time websocket connections',
                    'last_modified': datetime.utcnow().isoformat(),
                    'modified_by': 'system'
                },
                'advanced_analytics': {
                    'enabled': True,
                    'description': 'Advanced analytics and reporting',
                    'last_modified': datetime.utcnow().isoformat(),
                    'modified_by': 'system'
                },
                'user_registration': {
                    'enabled': True,
                    'description': 'Allow new user registrations',
                    'last_modified': datetime.utcnow().isoformat(),
                    'modified_by': 'system'
                },
                'maintenance_mode': {
                    'enabled': False,
                    'description': 'System maintenance mode',
                    'last_modified': datetime.utcnow().isoformat(),
                    'modified_by': 'system'
                }
            }
            
            # Log feature flags access
            analytics_service.track_user_action(
                event_type='admin_action',
                event_category='feature_flags',
                event_action='view_feature_flags',
                user_id=str(get_current_user().id),
                metadata={'flags_count': len(feature_flags)}
            )
            
            return jsonify({
                'success': True,
                'feature_flags': feature_flags,
                'admin_context': {
                    'can_modify': True,
                    'viewing_admin': str(get_current_user().id),
                    'timestamp': datetime.utcnow().isoformat()
                }
            }), 200
            
        elif request.method in ['POST', 'PUT']:
            # Update feature flags (for future implementation)
            data = request.get_json()
            flag_name = data.get('flag_name')
            enabled = data.get('enabled', False)
            
            if not flag_name:
                return _error('Flag name is required', status=400, code='validation_error')
            
            # For now, just log the attempt since we don't have persistent storage
            analytics_service.track_user_action(
                event_type='admin_action',
                event_category='feature_flags',
                event_action='modify_feature_flag',
                user_id=str(get_current_user().id),
                metadata={
                    'flag_name': flag_name,
                    'enabled': enabled,
                    'action': 'update'
                }
            )
            
            admin_user = get_current_user()
            if admin_user and admin_user.admin_profile:
                admin_user.admin_profile.log_action(
                    'modify',
                    f'Updated feature flag: {flag_name} to {enabled}',
                    'feature_flags'
                )
            
            return jsonify({
                'success': True,
                'message': f'Feature flag {flag_name} updated (logged for future implementation)',
                'flag_name': flag_name,
                'enabled': enabled,
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        
    except Exception as e:
        import traceback
        logger.error(f"Error managing feature flags: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return _error('Failed to manage feature flags', status=500, code='manage_feature_flags_failed')

# ============================================================================
# MISSING ADMIN ENDPOINTS - Part 4: User Analytics
# ============================================================================

@admin_bp.route('/analytics/users', methods=['GET'])
@require_admin
def get_admin_user_analytics():
    """Get detailed user analytics for admin dashboard."""
    try:
        from app.services.analytics_service import analytics_service
        import traceback
        
        # Get request parameters
        timeframe = request.args.get('timeframe', '30d')
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        metric_type = request.args.get('metric_type', 'overview')
        
        # Get user analytics from the websocket endpoint equivalent
        user_analytics = analytics_service.get_user_analytics(
            timeframe=timeframe,
            include_inactive=include_inactive
        )
        
        # Enhanced admin analytics
        admin_user_analytics = {
            'user_analytics': user_analytics,
            'admin_enhancements': {
                'detailed_breakdown': {
                    'new_users_count': analytics_service.get_new_users_count(timeframe),
                    'active_users_count': analytics_service.get_active_users_count(timeframe),
                    'retention_rate': analytics_service.get_user_retention_rate(timeframe) if hasattr(analytics_service, 'get_user_retention_rate') else 'N/A'
                },
                'geographic_distribution': analytics_service.get_user_geographic_data() if hasattr(analytics_service, 'get_user_geographic_data') else {},
                'engagement_metrics': {
                    'avg_session_duration': analytics_service.get_avg_session_duration(timeframe) if hasattr(analytics_service, 'get_avg_session_duration') else 'N/A',
                    'page_views_per_user': analytics_service.get_avg_page_views_per_user(timeframe) if hasattr(analytics_service, 'get_avg_page_views_per_user') else 'N/A'
                }
            },
            'filters_applied': {
                'timeframe': timeframe,
                'include_inactive': include_inactive,
                'metric_type': metric_type
            },
            'admin_context': {
                'generated_by': str(get_current_user().id),
                'can_export_data': True,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        # Track admin analytics access
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='analytics',
            event_action='view_user_analytics',
            user_id=str(get_current_user().id),
            metadata={
                'timeframe': timeframe,
                'include_inactive': include_inactive,
                'metric_type': metric_type
            }
        )
        
        admin_user = get_current_user()
        if admin_user and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'view',
                f'Accessed user analytics (timeframe: {timeframe})',
                'user_analytics'
            )
        
        return jsonify({
            'success': True,
            'analytics': admin_user_analytics
        }), 200
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting admin user analytics: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return _error('Failed to retrieve user analytics', status=500, code='get_user_analytics_failed')

# ============================================================================
# MISSING ADMIN ENDPOINTS - Part 3: User Activity
# ============================================================================

@admin_bp.route('/activity', methods=['GET'])
@require_admin
def get_admin_activity():
    """Get admin-specific user activity monitoring."""
    try:
        from app.services.analytics_service import analytics_service
        import traceback
        
        # Get request parameters
        timeframe = request.args.get('timeframe', '24h')
        limit = min(int(request.args.get('limit', 50)), 500)  # Cap at 500
        user_filter = request.args.get('user_id')
        
        # Get user activity data
        activity_data = analytics_service.get_user_activity(
            timeframe=timeframe,
            limit=limit,
            user_filter=user_filter
        )
        
        # Enhance with admin-specific information
        admin_activity = {
            'activity_data': activity_data,
            'filters_applied': {
                'timeframe': timeframe,
                'limit': limit,
                'user_filter': user_filter
            },
            'admin_insights': {
                'total_active_users': len(set([act.get('user_id') for act in activity_data if act.get('user_id')])),
                'most_active_hours': analytics_service.get_peak_activity_hours() if hasattr(analytics_service, 'get_peak_activity_hours') else [],
                'activity_trends': analytics_service.get_activity_trends(timeframe) if hasattr(analytics_service, 'get_activity_trends') else {}
            },
            'admin_context': {
                'viewing_admin': str(get_current_user().id),
                'can_view_user_details': True,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        # Log admin monitoring action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='view_user_activity',
            user_id=str(get_current_user().id),
            metadata={
                'timeframe': timeframe,
                'activity_count': len(activity_data),
                'user_filter': user_filter
            }
        )
        
        admin_user = get_current_user()
        if admin_user and hasattr(admin_user, 'admin_profile') and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'view',
                f'Monitored user activity (timeframe: {timeframe})',
                'user_activity'
            )
        
        return jsonify({
            'success': True,
            'activity': admin_activity
        }), 200
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting admin activity: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return _error('Failed to retrieve user activity', status=500, code='get_user_activity_failed')

# ============================================================================
# MISSING ADMIN ENDPOINTS - Part 2: System Stats
# ============================================================================

@admin_bp.route('/stats', methods=['GET'])
@require_admin
def get_admin_stats():
    """Get admin-specific system statistics."""
    try:
        from app.services.analytics_service import analytics_service
        from app.api.websocket import get_current_connections
        import traceback
        
        # Get system stats
        basic_stats = analytics_service.get_dashboard_stats()
        
        # Get websocket connection stats
        ws_connections = len(get_current_connections()) if hasattr(get_current_connections, '__len__') else 0
        
        # Enhanced admin stats
        admin_stats = {
            'system_overview': basic_stats,
            'real_time_metrics': {
                'active_connections': ws_connections,
                'api_requests_last_hour': analytics_service.get_api_requests_count('1h'),
                'database_connections': analytics_service.get_db_pool_status() if hasattr(analytics_service, 'get_db_pool_status') else {'active': 'unknown'}
            },
            'admin_specific': {
                'user_id': str(get_current_user().id),
                'access_permissions': {
                    'can_modify_users': True,
                    'can_view_analytics': True,
                    'can_access_logs': True
                },
                'last_admin_login': get_current_user().last_login.isoformat() if get_current_user().last_login else None
            },
            'system_health': {
                'status': 'operational',
                'uptime': analytics_service.get_system_uptime() if hasattr(analytics_service, 'get_system_uptime') else 'unknown',
                'last_updated': datetime.utcnow().isoformat()
            }
        }
        
        # Track admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='dashboard',
            event_action='view_admin_stats',
            user_id=str(get_current_user().id),
            metadata={'stats_requested': True}
        )
        
        admin_user = get_current_user()
        if admin_user and hasattr(admin_user, 'admin_profile') and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'view',
                'Accessed admin system stats',
                'system_stats'
            )
        
        return jsonify({
            'success': True,
            'stats': admin_stats
        }), 200
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting admin stats: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return _error('Failed to retrieve system stats', status=500, code='get_admin_stats_failed')

# ============================================================================
# MISSING ADMIN ENDPOINTS - Part 1: Monitoring Metrics
# ============================================================================

@admin_bp.route('/monitoring/metrics', methods=['GET'])
@require_admin
def get_admin_monitoring_metrics():
    """Get admin-specific monitoring metrics dashboard."""
    try:
        # Import monitoring service
        from app.services.analytics_service import analytics_service
        
        # Get current system metrics
        metrics = analytics_service.collect_system_metrics()
        
        # Get admin-specific enhancements
        admin_metrics = {
            'system_metrics': metrics,
            'admin_context': {
                'user_id': str(get_current_user().id),
                'access_level': get_current_user().admin_profile.access_level if hasattr(get_current_user(), 'admin_profile') and get_current_user().admin_profile else 100,
                'can_view_analytics': True
            },
            'enhanced_data': {
                'critical_alerts': [],  # Will be populated if we have alert system
                'system_health_score': 'healthy' if metrics.get('cpu_usage', 0) < 80 and metrics.get('memory_usage', 0) < 85 else 'warning'
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Log admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='view_admin_monitoring_metrics',
            user_id=str(get_current_user().id),
            metadata={'metrics_requested': True}
        )
        
        admin_user = get_current_user()
        if admin_user and hasattr(admin_user, 'admin_profile') and admin_user.admin_profile:
            admin_user.admin_profile.log_action(
                'view',
                'Accessed admin monitoring metrics',
                'monitoring_metrics'
            )
        
        return jsonify({
            'success': True,
            'metrics': admin_metrics
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting admin monitoring metrics: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return _error('Failed to retrieve monitoring metrics', status=500, code='get_admin_monitoring_metrics_failed')

@admin_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({'error': str(e)}), 400

@admin_bp.errorhandler(404)
def handle_not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

@admin_bp.errorhandler(403)
def handle_forbidden(e):
    return jsonify({'error': 'Access denied'}), 403

# ============================================================================
# API KEY MANAGEMENT
# ============================================================================

@admin_bp.route('/api-keys', methods=['GET'])
@require_admin
def list_api_keys():
    """List API keys with pagination and filters."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')
        user_id = request.args.get('user_id')
        search = request.args.get('search', '').strip()

        query = ApiKey.query
        if status:
            query = query.filter(ApiKey.status == status)
        if user_id:
            query = query.filter(ApiKey.user_id == user_id)
        if search:
            query = query.filter(ApiKey.name.ilike(f"%{search}%"))

        query = query.order_by(desc(ApiKey.created_at))
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        items = [k.to_dict() for k in pagination.items]

        # Log admin action
        admin_user = get_current_user()
        if admin_user and getattr(admin_user, 'admin_profile', None):
            admin_user.admin_profile.log_action(
                'view', f'Viewed API keys (page {page}, {len(items)} items)', 'api_key'
            )

        meta = {
            'filters': {
                'status': status,
                'user_id': user_id,
                'search': search
            },
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
        return _paginate(items, pagination.page, pagination.per_page, pagination.total, meta=meta)
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        return _error('Failed to list API keys', status=500, code='list_api_keys_failed')


@admin_bp.route('/api-keys', methods=['POST'])
@require_admin
def create_api_key():
    """Create a new API key for a user. Returns the plain key once."""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        name = (data.get('name') or '').strip()
        permissions = data.get('permissions') or []
        rate_limit = data.get('rate_limit', 0)
        expires_at = data.get('expires_at')

        if not user_id or not name:
            return _error('user_id and name are required', status=400, code='validation_error')

        user = User.query.get(user_id)
        if not user:
            return _error('User not found', status=404, code='user_not_found')

        # Normalize permissions
        if not isinstance(permissions, list):
            return _error('permissions must be a list of strings', status=400, code='validation_error')
        permissions = [str(p) for p in permissions]

        # Parse expiry
        expires_dt = None
        if expires_at:
            try:
                if isinstance(expires_at, (int, float)):
                    # treat as epoch seconds
                    expires_dt = datetime.utcfromtimestamp(float(expires_at))
                else:
                    expires_dt = datetime.fromisoformat(str(expires_at).replace('Z', '+00:00'))
            except Exception:
                return _error('expires_at must be ISO8601 or epoch seconds', status=400, code='validation_error')

        # Generate secure key and hash
        plain_key = f"sk_{secrets.token_urlsafe(32)}"
        key_hash = ApiKey.hash_key(plain_key)

        record = ApiKey(
            user_id=user.id,
            name=name,
            key_hash=key_hash,
            permissions=permissions,
            rate_limit=int(rate_limit or 0),
            expires_at=expires_dt,
            status='active'
        )
        db.session.add(record)
        db.session.commit()

        # Log admin action
        admin_user = get_current_user()
        if admin_user and getattr(admin_user, 'admin_profile', None):
            admin_user.admin_profile.log_action(
                'create', f'Created API key "{name}" for {user.email}', 'api_key', record.id,
                { 'user_id': str(user.id), 'permissions': permissions, 'rate_limit': rate_limit }
            )

        return jsonify(record.to_dict(include_key=True, plain_key=plain_key)), 201
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        db.session.rollback()
        return _error('Failed to create API key', status=500, code='create_api_key_failed')


@admin_bp.route('/api-keys/<key_id>', methods=['PUT'])
@require_admin
def update_api_key(key_id):
    """Update API key metadata (name, permissions, rate_limit, status, expires_at)."""
    try:
        record = ApiKey.query.get_or_404(key_id)
        data = request.get_json() or {}

        if 'name' in data:
            record.name = (data.get('name') or '').strip() or record.name
        if 'permissions' in data:
            perms = data.get('permissions') or []
            if not isinstance(perms, list):
                return _error('permissions must be a list of strings', status=400, code='validation_error')
            record.permissions = [str(p) for p in perms]
        if 'rate_limit' in data:
            try:
                record.rate_limit = int(data.get('rate_limit'))
            except ValueError:
                return _error('rate_limit must be an integer', status=400, code='validation_error')
        if 'status' in data:
            status = str(data.get('status')).lower()
            if status not in ('active', 'revoked', 'expired'):
                return _error("status must be one of: active, revoked, expired", status=400, code='validation_error')
            record.status = status
        if 'expires_at' in data:
            expires_at = data.get('expires_at')
            if expires_at in (None, ''):
                record.expires_at = None
            else:
                try:
                    if isinstance(expires_at, (int, float)):
                        record.expires_at = datetime.utcfromtimestamp(float(expires_at))
                    else:
                        record.expires_at = datetime.fromisoformat(str(expires_at).replace('Z', '+00:00'))
                except Exception:
                    return _error('expires_at must be ISO8601 or epoch seconds', status=400, code='validation_error')

        db.session.commit()

        # Log admin action
        admin_user = get_current_user()
        if admin_user and getattr(admin_user, 'admin_profile', None):
            admin_user.admin_profile.log_action(
                'update', f'Updated API key "{record.name}"', 'api_key', record.id
            )

        return jsonify(record.to_dict()), 200
    except Exception as e:
        logger.error(f"Error updating API key {key_id}: {e}")
        db.session.rollback()
        return _error('Failed to update API key', status=500, code='update_api_key_failed')


@admin_bp.route('/api-keys/<key_id>/rotate', methods=['POST'])
@require_admin
def rotate_api_key(key_id):
    """Rotate an API key and return the new key once."""
    try:
        record = ApiKey.query.get_or_404(key_id)
        plain_key = f"sk_{secrets.token_urlsafe(32)}"
        record.key_hash = ApiKey.hash_key(plain_key)
        record.requests_today = 0
        record.last_used = None
        record.status = 'active'
        db.session.commit()

        # Log admin action
        admin_user = get_current_user()
        if admin_user and getattr(admin_user, 'admin_profile', None):
            admin_user.admin_profile.log_action(
                'rotate', f'Rotated API key "{record.name}"', 'api_key', record.id
            )

        return jsonify(record.to_dict(include_key=True, plain_key=plain_key)), 200
    except Exception as e:
        logger.error(f"Error rotating API key {key_id}: {e}")
        db.session.rollback()
        return _error('Failed to rotate API key', status=500, code='rotate_api_key_failed')


@admin_bp.route('/api-keys/<key_id>/revoke', methods=['POST'])
@require_admin
def revoke_api_key(key_id):
    """Revoke an API key."""
    try:
        record = ApiKey.query.get_or_404(key_id)
        if record.status != 'revoked':
            record.status = 'revoked'
            db.session.commit()

            # Log admin action
            admin_user = get_current_user()
            if admin_user and getattr(admin_user, 'admin_profile', None):
                admin_user.admin_profile.log_action(
                    'revoke', f'Revoked API key "{record.name}"', 'api_key', record.id
                )

        return _ok({'message': 'API key revoked', 'id': str(record.id), 'status': record.status})
    except Exception as e:
        logger.error(f"Error revoking API key {key_id}: {e}")
        db.session.rollback()
        return _error('Failed to revoke API key', status=500, code='revoke_api_key_failed')

# ============================================================================
# ACCESS LOGS (Admin Audit)
# ============================================================================

@admin_bp.route('/access-logs', methods=['GET'])
@require_admin
def get_access_logs():
    """Get access logs with filtering and pagination.
    Query params: user, action, success, from, to, page, per_page
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        user_q = (request.args.get('user') or '').strip()
        action = (request.args.get('action') or '').strip()
        success = request.args.get('success')
        start = request.args.get('from')
        end = request.args.get('to')

        query = AccessLog.query

        if user_q:
            like = f"%{user_q}%"
            query = query.filter(db.or_(AccessLog.user_email.ilike(like), AccessLog.user_name.ilike(like)))
        if action:
            query = query.filter(AccessLog.action == action)
        if success is not None and success != '':
            if success in ('true', '1', 'True'):
                query = query.filter(AccessLog.success.is_(True))
            elif success in ('false', '0', 'False'):
                query = query.filter(AccessLog.success.is_(False))
        if start:
            try:
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                query = query.filter(AccessLog.timestamp >= start_dt)
            except ValueError:
                pass
        if end:
            try:
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                query = query.filter(AccessLog.timestamp <= end_dt)
            except ValueError:
                pass

        query = query.order_by(desc(AccessLog.timestamp))
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = [row.to_dict() for row in pagination.items]

        # Log admin action
        admin_user = get_current_user()
        if admin_user and getattr(admin_user, 'admin_profile', None):
            admin_user.admin_profile.log_action('view', f'Viewed access logs (page {page}, {len(items)} items)', 'access_log')

        return _paginate(items, pagination.page, pagination.per_page, pagination.total)
    except Exception as e:
        logger.error(f"Error fetching access logs: {e}")
        return _error('Failed to fetch access logs', status=500, code='access_logs_failed')

# ============================================================================
# RATE LIMIT RULES
# ============================================================================

@admin_bp.route('/rate-limits', methods=['GET'])
@require_admin
def list_rate_limit_rules():
    try:
        rules = RateLimitRule.query.order_by(desc(RateLimitRule.updated_at), RateLimitRule.endpoint).all()
        return jsonify([r.to_dict() for r in rules]), 200
    except Exception as e:
        logger.error(f"Error listing rate limit rules: {e}")
        return _error('Failed to list rate limit rules', status=500, code='list_rate_limit_rules_failed')


@admin_bp.route('/rate-limits', methods=['PUT'])
@require_admin
def bulk_update_rate_limit_rules():
    """Bulk upsert rate limit rules. Payload: { rules: [ {id?, endpoint, method, per_minute, per_hour, burst, enabled} ] }"""
    try:
        data = request.get_json() or {}
        rules = data.get('rules')
        if not isinstance(rules, list):
            return _error('rules must be a list', status=400, code='validation_error')

        updated = []
        for payload in rules:
            if not isinstance(payload, dict):
                continue
            rid = payload.get('id')
            endpoint = (payload.get('endpoint') or '').strip()
            method = (payload.get('method') or '').upper()
            if not endpoint or not method:
                continue

            per_minute = int(payload.get('per_minute') or 0)
            per_hour = int(payload.get('per_hour') or 0)
            burst = int(payload.get('burst') or 0)
            enabled = bool(payload.get('enabled', True))

            record = None
            if rid:
                record = RateLimitRule.query.get(rid)
            if not record:
                record = RateLimitRule(endpoint=endpoint, method=method)
                db.session.add(record)

            record.endpoint = endpoint
            record.method = method
            record.per_minute = per_minute
            record.per_hour = per_hour
            record.burst = burst
            record.enabled = enabled
            updated.append(record)

        db.session.commit()

        # Log admin action
        admin_user = get_current_user()
        if admin_user and getattr(admin_user, 'admin_profile', None):
            admin_user.admin_profile.log_action('update', f'Bulk updated {len(updated)} rate limit rules', 'rate_limit_rule')

        return jsonify({'updated': [r.to_dict() for r in updated]}), 200
    except Exception as e:
        logger.error(f"Error updating rate limit rules: {e}")
        db.session.rollback()
        return _error('Failed to update rate limit rules', status=500, code='update_rate_limit_rules_failed')

# ============================================================================
# WEBHOOKS
# ============================================================================

@admin_bp.route('/webhooks', methods=['GET'])
@require_admin
def list_webhooks():
    try:
        hooks = Webhook.query.order_by(desc(Webhook.created_at)).all()
        return _ok({'items': [h.to_dict() for h in hooks], 'total': len(hooks)})
    except Exception as e:
        logger.error(f"Error listing webhooks: {e}")
        return _error('Failed to list webhooks', status=500, code='list_webhooks_failed')


@admin_bp.route('/webhooks', methods=['POST'])
@require_admin
def create_webhook():
    try:
        data = request.get_json() or {}
        url = (data.get('url') or '').strip()
        events = data.get('events') or []
        secret = (data.get('secret') or '').strip() or None
        status = (data.get('status') or 'active').strip()

        if not url:
            return _error('url is required', status=400, code='validation_error')
        if not isinstance(events, list):
            return _error('events must be a list of strings', status=400, code='validation_error')
        events = [str(e) for e in events]
        if status not in ('active', 'disabled'):
            return _error("status must be 'active' or 'disabled'", status=400, code='validation_error')

        hook = Webhook(url=url, events=events, secret=secret, status=status)
        db.session.add(hook)
        db.session.commit()

        # Log admin action
        admin_user = get_current_user()
        if admin_user and getattr(admin_user, 'admin_profile', None):
            admin_user.admin_profile.log_action('create', f'Created webhook {url}', 'webhook', hook.id)

        return jsonify(hook.to_dict()), 201
    except Exception as e:
        logger.error(f"Error creating webhook: {e}")
        db.session.rollback()
        return _error('Failed to create webhook', status=500, code='create_webhook_failed')


@admin_bp.route('/webhooks/<hook_id>', methods=['DELETE'])
@require_admin
def delete_webhook(hook_id):
    """Soft delete by disabling the webhook for safety."""
    try:
        hook = Webhook.query.get_or_404(hook_id)
        hook.status = 'disabled'
        db.session.commit()

        # Log admin action
        admin_user = get_current_user()
        if admin_user and getattr(admin_user, 'admin_profile', None):
            admin_user.admin_profile.log_action('delete', f'Disabled webhook {hook.url}', 'webhook', hook.id)

        return _ok({'message': 'Webhook disabled', 'id': str(hook.id)})
    except Exception as e:
        logger.error(f"Error deleting webhook {hook_id}: {e}")
        db.session.rollback()
        return _error('Failed to delete webhook', status=500, code='delete_webhook_failed')

# ============================================================================
# API USAGE ANALYTICS
# ============================================================================

@admin_bp.route('/api-usage/series', methods=['GET'])
@require_admin
def get_api_usage_series():
    """Time series of API usage with counts, errors, avg and p95 response time.
    Query params:
      - range: 24h|48h|7d|30d (default 7d)
      - method: optional HTTP method filter
      - path: optional substring match on path
    """
    try:
        range_q = (request.args.get('range') or '7d').lower()
        method_filter = (request.args.get('method') or '').upper().strip()
        path_filter = (request.args.get('path') or '').strip()

        # Determine window and granularity
        if range_q.endswith('h'):
            hours = int(range_q[:-1] or 24)
            start_time = datetime.utcnow() - timedelta(hours=hours)
            granularity = 'hour'
        else:
            days = int(range_q[:-1] or 7) if range_q.endswith('d') else int(range_q or 7)
            start_time = datetime.utcnow() - timedelta(days=days)
            granularity = 'day'

        bucket = func.date_trunc(granularity, UsageInsight.timestamp).label('bucket')
        dur_ms = cast(UsageInsight.duration_seconds * 1000.0, Float)
        status_code = cast(UsageInsight.event_metadata['status_code'].astext, Integer)
        method_col = func.coalesce(UsageInsight.event_metadata['method'].astext, '').label('method')
        path_col = func.coalesce(UsageInsight.event_metadata['path'].astext,
                                 UsageInsight.event_metadata['endpoint'].astext,
                                 '').label('path')

        q = db.session.query(
            bucket,
            func.count().label('count'),
            func.sum(func.case([(UsageInsight.success.is_(False), 1)], else_=0)).label('errors'),
            func.avg(dur_ms).label('avg_ms'),
            func.percentile_disc(0.95).within_group(dur_ms).label('p95_ms')
        ).filter(
            UsageInsight.event_type == 'api_call',
            UsageInsight.timestamp >= start_time
        )

        if method_filter:
            q = q.filter(method_col == method_filter)
        if path_filter:
            q = q.filter(path_col.ilike(f"%{path_filter}%"))

        q = q.group_by(bucket).order_by(bucket)
        rows = q.all()
        items = []
        for r in rows:
            ts = (r.bucket if hasattr(r, 'bucket') else r[0])
            count = int(getattr(r, 'count', 0) or 0)
            errors = int(getattr(r, 'errors', 0) or 0)
            avg_ms = float(getattr(r, 'avg_ms', 0) or 0)
            p95_ms = float(getattr(r, 'p95_ms', 0) or 0)
            items.append({
                'timestamp': ts.isoformat(),
                'time': ts.isoformat(),          # alias for frontend
                'count': count,
                'requests': count,               # alias for frontend
                'errors': errors,
                'avg_ms': avg_ms,
                'avg_response_ms': avg_ms,       # alias for frontend
                'p95_ms': p95_ms
            })

        return _ok({
            'items': items,
            'range': range_q,
            'granularity': granularity,
            'total': sum(item['count'] for item in items)
        })

    except Exception as e:
        logger.error(f"Error building API usage series: {e}")
        return _error('Failed to build API usage series', status=500, code='api_usage_series_failed')


@admin_bp.route('/api-usage/top-endpoints', methods=['GET'])
@require_admin
def get_api_usage_top_endpoints():
    """Top endpoints by request count with error rate and latency stats.
    Query params:
      - range: 24h|7d|30d (default 7d)
      - limit: max items (default 20)
    """
    try:
        range_q = (request.args.get('range') or '7d').lower()
        limit = min(request.args.get('limit', 20, type=int), 100)

        if range_q.endswith('h'):
            hours = int(range_q[:-1] or 24)
            start_time = datetime.utcnow() - timedelta(hours=hours)
        else:
            days = int(range_q[:-1] or 7) if range_q.endswith('d') else int(range_q or 7)
            start_time = datetime.utcnow() - timedelta(days=days)

        dur_ms = cast(UsageInsight.duration_seconds * 1000.0, Float)
        method_col = func.coalesce(UsageInsight.event_metadata['method'].astext, 'GET')
        path_col = func.coalesce(UsageInsight.event_metadata['path'].astext,
                                 UsageInsight.event_metadata['endpoint'].astext,
                                 'unknown')

        q = db.session.query(
            method_col.label('method'),
            path_col.label('path'),
            func.count().label('count'),
            func.sum(func.case([(UsageInsight.success.is_(False), 1)], else_=0)).label('errors'),
            func.avg(dur_ms).label('avg_ms'),
            func.percentile_disc(0.95).within_group(dur_ms).label('p95_ms'),
            func.max(UsageInsight.timestamp).label('last_ts')
        ).filter(
            UsageInsight.event_type == 'api_call',
            UsageInsight.timestamp >= start_time
        ).group_by(method_col, path_col).order_by(desc('count')).limit(limit)

        rows = q.all()
        items = []
        for r in rows:
            count = int(getattr(r, 'count', 0) or 0)
            errors = int(getattr(r, 'errors', 0) or 0)
            last_ts = getattr(r, 'last_ts', None)
            avg_ms = float(getattr(r, 'avg_ms', 0) or 0)
            items.append({
                'method': r.method,
                'path': r.path,
                'endpoint': r.path,                 # alias for frontend
                'count': count,
                'requests': count,                  # alias for frontend
                'errors': errors,
                'error_rate': round((errors / count * 100.0), 2) if count else 0.0,
                'avg_ms': avg_ms,
                'avg_response_ms': avg_ms,          # alias for frontend
                'p95_ms': float(getattr(r, 'p95_ms', 0) or 0),
                'last_accessed': last_ts.isoformat() if last_ts else None
            })

        return _ok({'items': items, 'range': range_q, 'total': len(items)})

    except Exception as e:
        logger.error(f"Error getting top endpoints: {e}")
        return _error('Failed to get top endpoints', status=500, code='get_top_endpoints_failed')

@admin_bp.route('/usage/overview', methods=['GET'])
@require_admin
def get_usage_overview():
    """Overview: { total_sessions, active_users, avg_session_minutes, total_page_views, bounce_rate, new_users, returning_users, peak_concurrent }"""
    try:
        range_q = (request.args.get('range') or '7d').lower()
        if range_q.endswith('h'):
            hours = int(range_q[:-1] or 24)
            start_time = datetime.utcnow() - timedelta(hours=hours)
        else:
            days = int(range_q[:-1] or 7) if range_q.endswith('d') else int(range_q or 7)
            start_time = datetime.utcnow() - timedelta(days=days)

        # Sessions and users
        total_sessions = db.session.query(func.count(func.distinct(UsageInsight.session_id))).filter(
            UsageInsight.session_id.isnot(None), UsageInsight.timestamp >= start_time
        ).scalar() or 0
        active_users = db.session.query(func.count(func.distinct(UsageInsight.user_id))).filter(
            UsageInsight.user_id.isnot(None), UsageInsight.timestamp >= start_time
        ).scalar() or 0

        # Avg session duration (minutes)
        session_sums = db.session.query(
            UsageInsight.session_id,
            func.sum(func.coalesce(UsageInsight.duration_seconds, 0)).label('dur')
        ).filter(
            UsageInsight.session_id.isnot(None), UsageInsight.timestamp >= start_time
        ).group_by(UsageInsight.session_id).subquery()
        avg_session_minutes = float((db.session.query(func.avg(session_sums.c.dur)).scalar() or 0) / 60.0)

        # Page views
        page_views = db.session.query(func.count()).filter(
            UsageInsight.timestamp >= start_time,
            func.coalesce(UsageInsight.event_action, '').ilike('%page_view%')
        ).scalar() or 0

        # Bounce rate: sessions with exactly 1 page_view
        pv_per_session = db.session.query(
            UsageInsight.session_id.label('sid'),
            func.count().label('pv')
        ).filter(
            UsageInsight.session_id.isnot(None),
            UsageInsight.timestamp >= start_time,
            func.coalesce(UsageInsight.event_action, '').ilike('%page_view%')
        ).group_by(UsageInsight.session_id).subquery()
        single_pv_sessions = db.session.query(func.count()).select_from(pv_per_session).filter(pv_per_session.c.pv == 1).scalar() or 0
        bounce_rate = round((single_pv_sessions / total_sessions * 100.0), 2) if total_sessions else 0.0

        # New and returning users
        new_users = User.query.filter(User.created_at >= start_time).count()
        returning_users = db.session.query(func.count(func.distinct(UsageInsight.user_id))).join(User, User.id == UsageInsight.user_id).filter(
            User.created_at < start_time,
            UsageInsight.timestamp >= start_time,
            UsageInsight.user_id.isnot(None)
        ).scalar() or 0

        # Peak concurrent sessions per hour
        hourly_sessions = db.session.query(
            func.date_trunc('hour', UsageInsight.timestamp).label('h'),
            func.count(func.distinct(UsageInsight.session_id)).label('sessions')
        ).filter(
            UsageInsight.session_id.isnot(None), UsageInsight.timestamp >= start_time
        ).group_by('h').all()
        peak_concurrent = max((int(row.sessions or 0) for row in hourly_sessions), default=0)

        return _ok({
            'total_sessions': int(total_sessions),
            'active_users': int(active_users),
            'avg_session_minutes': round(avg_session_minutes, 2),
            'total_page_views': int(page_views),
            'bounce_rate': bounce_rate,
            'new_users': int(new_users),
            'returning_users': int(returning_users),
            'peak_concurrent': int(peak_concurrent)
        })
    except Exception as e:
        logger.error(f"Error building usage overview: {e}")
        return _error('Failed to build usage overview', status=500, code='usage_overview_failed')


@admin_bp.route('/usage/hourly', methods=['GET'])
@require_admin
def get_usage_hourly():
    """Hourly series: [{ hour, sessions, users, page_views }]"""
    try:
        range_q = (request.args.get('range') or '24h').lower()
        if range_q.endswith('h'):
            hours = int(range_q[:-1] or 24)
            start_time = datetime.utcnow() - timedelta(hours=hours)
        else:
            days = int(range_q[:-1] or 1) if range_q.endswith('d') else int(range_q or 1)
            start_time = datetime.utcnow() - timedelta(days=days)

        hour_col = func.date_trunc('hour', UsageInsight.timestamp)
        rows = db.session.query(
            hour_col.label('h'),
            func.count(func.distinct(UsageInsight.session_id)).label('sessions'),
            func.count(func.distinct(UsageInsight.user_id)).label('users'),
            func.sum(func.case([(func.coalesce(UsageInsight.event_action, '').ilike('%page_view%'), 1)], else_=0)).label('page_views')
        ).filter(UsageInsight.timestamp >= start_time).group_by('h').order_by('h').all()

        items = [{
            'hour': (r.h if hasattr(r, 'h') else r[0]).isoformat(),
            'sessions': int(getattr(r, 'sessions', 0) or 0),
            'users': int(getattr(r, 'users', 0) or 0),
            'page_views': int(getattr(r, 'page_views', 0) or 0)
        } for r in rows]
        return _ok({'items': items, 'range': range_q, 'total': len(items)})
    except Exception as e:
        logger.error(f"Error building usage hourly: {e}")
        return _error('Failed to build usage hourly', status=500, code='usage_hourly_failed')


@admin_bp.route('/usage/weekly', methods=['GET'])
@require_admin
def get_usage_weekly():
    """Weekly daily series: [{ day, sessions, users }]. Returns last 7 full days including today."""
    try:
        # Define 7-day window ending today (UTC)
        today_utc = datetime.utcnow().date()
        start_date = today_utc - timedelta(days=6)
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(today_utc + timedelta(days=1), datetime.min.time())

        day_col = func.date(UsageInsight.timestamp)
        rows = db.session.query(
            day_col.label('d'),
            func.count(func.distinct(UsageInsight.session_id)).label('sessions'),
            func.count(func.distinct(UsageInsight.user_id)).label('users')
        ).filter(
            and_(UsageInsight.timestamp >= start_dt, UsageInsight.timestamp < end_dt)
        ).group_by('d').order_by('d').all()

        row_map = {str(getattr(r, 'd')): {
            'sessions': int(getattr(r, 'sessions', 0) or 0),
            'users': int(getattr(r, 'users', 0) or 0)
        } for r in rows}

        items = []
        for i in range(7):
            d = (start_date + timedelta(days=i)).isoformat()
            vals = row_map.get(d, {'sessions': 0, 'users': 0})
            items.append({'day': d, 'sessions': vals['sessions'], 'users': vals['users']})

        return _ok({'items': items, 'range': '7d', 'total': len(items)})
    except Exception as e:
        logger.error(f"Error building weekly usage series: {e}")
        return _error('Failed to build weekly usage', status=500, code='usage_weekly_failed')


@admin_bp.route('/usage/features', methods=['GET'])
@require_admin
def get_usage_features():
    """Features usage: [{ feature, category, sessions, unique_users, avg_duration_min, growth_pct }]"""
    try:
        range_q = (request.args.get('range') or '30d').lower()
        if range_q.endswith('h'):
            hours = int(range_q[:-1] or 24)
            start_time = datetime.utcnow() - timedelta(hours=hours)
            prev_start = start_time - timedelta(hours=hours)
        else:
            days = int(range_q[:-1] or 30) if range_q.endswith('d') else int(range_q or 30)
            start_time = datetime.utcnow() - timedelta(days=days)
            prev_start = start_time - timedelta(days=days)

        # Current period
        feature_rows = db.session.query(
            func.coalesce(UsageInsight.event_action, 'unknown').label('feature'),
            func.coalesce(UsageInsight.event_category, 'general').label('category'),
            func.count(func.distinct(UsageInsight.session_id)).label('sessions'),
            func.count(func.distinct(UsageInsight.user_id)).label('unique_users'),
            func.avg(func.coalesce(UsageInsight.duration_seconds, 0)).label('avg_dur')
        ).filter(UsageInsight.timestamp >= start_time).group_by('feature', 'category').order_by(desc('sessions')).all()

        # Previous period counts for growth
        prev_rows = db.session.query(
            func.coalesce(UsageInsight.event_action, 'unknown').label('feature'),
            func.count().label('count')
        ).filter(and_(UsageInsight.timestamp >= prev_start, UsageInsight.timestamp < start_time)).group_by('feature').all()
        prev_map = {r.feature: int(r.count or 0) for r in prev_rows}

        items = []
        for r in feature_rows:
            cur = int(getattr(r, 'sessions', 0) or 0)
            prev = prev_map.get(getattr(r, 'feature'), 0)
            growth_pct = 0.0
            if prev == 0:
                growth_pct = 100.0 if cur > 0 else 0.0
            else:
                growth_pct = round(((cur - prev) / prev) * 100.0, 2)
            items.append({
                'feature': getattr(r, 'feature'),
                'category': getattr(r, 'category'),
                'sessions': cur,
                'unique_users': int(getattr(r, 'unique_users', 0) or 0),
                'avg_duration_min': round(float(getattr(r, 'avg_dur', 0) or 0) / 60.0, 2),
                'growth_pct': growth_pct
            })
        return _ok({'items': items, 'range': range_q, 'total': len(items)})
    except Exception as e:
        logger.error(f"Error building features usage: {e}")
        return _error('Failed to build features usage', status=500, code='usage_features_failed')


@admin_bp.route('/usage/devices', methods=['GET'])
@require_admin
def get_usage_devices():
    """Devices breakdown: [{ device, sessions, users, percentage, avg_duration_min }]"""
    try:
        range_q = (request.args.get('range') or '30d').lower()
        if range_q.endswith('h'):
            hours = int(range_q[:-1] or 24)
            start_time = datetime.utcnow() - timedelta(hours=hours)
        else:
            days = int(range_q[:-1] or 30) if range_q.endswith('d') else int(range_q or 30)
            start_time = datetime.utcnow() - timedelta(days=days)

        # Simple device classifier
        def device_case(ua):
            ua_l = func.lower(func.coalesce(ua, ''))
            return func.case([
                (ua_l.ilike('%mobile%'), 'Mobile'),
                (ua_l.ilike('%iphone%'), 'Mobile'),
                (ua_l.ilike('%android%'), 'Mobile'),
                (ua_l.ilike('%ipad%'), 'Tablet'),
                (ua_l.ilike('%tablet%'), 'Tablet'),
                (ua_l.ilike('%windows%'), 'Desktop'),
                (ua_l.ilike('%macintosh%'), 'Desktop'),
                (ua_l.ilike('%linux%'), 'Desktop')
            ], else_='Desktop')

        ua_col = func.coalesce(UsageInsight.user_agent, '')
        rows = db.session.query(
            device_case(ua_col).label('device'),
            func.count(func.distinct(UsageInsight.session_id)).label('sessions'),
            func.count(func.distinct(UsageInsight.user_id)).label('users'),
            func.avg(func.coalesce(UsageInsight.duration_seconds, 0)).label('avg_dur')
        ).filter(UsageInsight.timestamp >= start_time).group_by('device').all()

        total_sessions = sum(int(getattr(r, 'sessions', 0) or 0) for r in rows) or 1
        items = []
        for r in rows:
            sessions = int(getattr(r, 'sessions', 0) or 0)
            items.append({
                'device': getattr(r, 'device'),
                'sessions': sessions,
                'users': int(getattr(r, 'users', 0) or 0),
                'percentage': round(sessions / total_sessions * 100.0, 2),
                'avg_duration_min': round(float(getattr(r, 'avg_dur', 0) or 0) / 60.0, 2)
            })
        return _ok({'items': items, 'range': range_q, 'total': len(items)})
    except Exception as e:
        logger.error(f"Error building devices usage: {e}")
        return _error('Failed to build devices usage', status=500, code='usage_devices_failed')


# ============================================================================
# API REQUEST LOGS (Admin Audit)
# ============================================================================

@admin_bp.route('/api-logs', methods=['GET'])
@require_admin
def get_api_request_logs():
    """Get API request logs with filtering and pagination.
    Query params: method, status, q (search), from, to, page, per_page
    Returns: { items, summary, page, per_page, total }
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        method_filter = (request.args.get('method') or '').upper().strip()
        status_filter = request.args.get('status', type=int)
        search_query = (request.args.get('q') or '').strip()
        start = request.args.get('from')
        end = request.args.get('to')

        # Build query from UsageInsight table filtering for API calls
        query = UsageInsight.query.filter(UsageInsight.event_type == 'api_call')

        # Apply filters
        if method_filter:
            query = query.filter(
                func.coalesce(UsageInsight.event_metadata['method'].astext, '').ilike(f'%{method_filter}%')
            )
        
        if status_filter:
            query = query.filter(
                cast(UsageInsight.event_metadata['status_code'].astext, Integer) == status_filter
            )
        
        if search_query:
            # Search in path/endpoint and user email
            search_like = f'%{search_query}%'
            query = query.outerjoin(User, User.id == UsageInsight.user_id).filter(
                db.or_(
                    func.coalesce(UsageInsight.event_metadata['path'].astext, '').ilike(search_like),
                    func.coalesce(UsageInsight.event_metadata['endpoint'].astext, '').ilike(search_like),
                    User.email.ilike(search_like)
                )
            )
        
        if start:
            try:
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                query = query.filter(UsageInsight.timestamp >= start_dt)
            except ValueError:
                pass
        
        if end:
            try:
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                query = query.filter(UsageInsight.timestamp <= end_dt)
            except ValueError:
                pass

        # Get summary data before pagination
        summary_query = query.with_entities(
            func.count().label('total'),
            func.sum(func.case([(UsageInsight.success.is_(False), 1)], else_=0)).label('errors'),
            func.avg(func.coalesce(UsageInsight.duration_seconds, 0) * 1000.0).label('avg_response_ms'),
            func.percentile_disc(0.95).within_group(
                func.coalesce(UsageInsight.duration_seconds, 0) * 1000.0
            ).label('p95_response_ms')
        )
        summary_result = summary_query.first()
        
        summary = {
            'total': int(summary_result.total or 0),
            'errors': int(summary_result.errors or 0),
            'avg_response_ms': round(float(summary_result.avg_response_ms or 0), 2),
            'p95_response_ms': round(float(summary_result.p95_response_ms or 0), 2)
        }

        # Order and paginate
        query = query.order_by(desc(UsageInsight.timestamp))
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # Format results
        items = []
        for log in pagination.items:
            metadata = log.event_metadata or {}
            status_code = None
            try:
                status_code = int(metadata.get('status_code', 0))
            except (ValueError, TypeError):
                pass

            # Get user email if available
            user_email = None
            if log.user_id and hasattr(log, 'user') and log.user:
                user_email = log.user.email
            elif log.user_id:
                # Fallback: query user separately if relationship not loaded
                user = User.query.get(log.user_id)
                user_email = user.email if user else None

            items.append({
                'id': str(log.id),
                'method': metadata.get('method', 'GET'),
                'path': metadata.get('path') or metadata.get('endpoint', 'unknown'),
                'status': status_code,
                'response_ms': round((log.duration_seconds or 0) * 1000, 2),
                'user_email': user_email,
                'ip': log.ip_address,
                'timestamp': log.timestamp.isoformat()
            })

        # Log admin action
        admin_user = get_current_user()
        if admin_user and getattr(admin_user, 'admin_profile', None):
            admin_user.admin_profile.log_action(
                'view', 
                f'Viewed API logs (page {page}, {len(items)} items, filters: method={method_filter}, status={status_filter})', 
                'api_log'
            )

        return jsonify({
            'items': items,
            'summary': summary,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total
        }), 200

    except Exception as e:
        logger.error(f"Error fetching API request logs: {e}")
        return _error('Failed to fetch API request logs', status=500, code='api_logs_failed')

# ============================================================================
# DATABASE TOOLS (Expanded)
# ============================================================================

@admin_bp.route('/db/connections', methods=['GET'])
@require_admin
def get_db_connections():
    """Database connections summary plus connection object compatible with UI."""
    try:
        parsed = urlparse(current_app.config.get('SQLALCHEMY_DATABASE_URI'))
        host = parsed.hostname or 'unknown'
        port = parsed.port or 5432
        database = (parsed.path or '/').lstrip('/') or 'unknown'
        name = f"Primary ({database})"

        # Ping DB and measure latency
        t0 = time.time()
        try:
            db.session.execute(text('SELECT 1'))
            db_ok = True
        except Exception:
            db_ok = False
        latency_ms = int((time.time() - t0) * 1000)

        # Pool stats (best-effort)
        pool = getattr(db.engine, 'pool', None)
        max_size = getattr(pool, 'size', lambda: None)()
        checked_out = getattr(pool, 'checkedout', lambda: None)()
        pool_info = {
            'active': int(checked_out) if checked_out is not None else None,
            'idle': None,
            'max': int(max_size) if max_size is not None else None
        }

        return _ok([{
            'id': 'primary',
            'name': name,
            'type': 'postgresql',
            'host': host,
            'port': int(port),
            'database': database,
            'status': 'up' if db_ok else 'down',
            'last_checked': datetime.utcnow().isoformat(),
            'response_ms': latency_ms,
            'pool': pool_info
        }])
    except Exception as e:
        logger.error(f"Error getting DB connections: {e}")
        return _error('Failed to get DB connections', status=500, code='db_connections_failed')


@admin_bp.route('/db/metrics', methods=['GET'])
@require_admin
def get_db_metrics():
    """Expanded PostgreSQL database metrics for admin UI."""
    try:
        # Sizes
        total_size_bytes = db.session.execute(text("SELECT pg_database_size(current_database())")).scalar() or 0
        table_count = db.session.execute(text("""
            SELECT count(*) FROM information_schema.tables WHERE table_schema='public'
        """)).scalar() or 0
        index_count = db.session.execute(text("""
            SELECT count(*) FROM pg_class WHERE relkind='i'
        """)).scalar() or 0
        connection_count = db.session.execute(text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")) .scalar() or 0
        active_queries = db.session.execute(text("""
            SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() AND state = 'active'
        """)).scalar() or 0
        # Cache hit ratio
        hit_row = db.session.execute(text("""
            SELECT blks_hit, blks_read FROM pg_stat_database WHERE datname = current_database()
        """)).fetchone()
        blks_hit = (hit_row[0] if hit_row else 0) or 0
        blks_read = (hit_row[1] if hit_row else 0) or 0
        cache_hit_ratio = round((blks_hit / (blks_hit + blks_read) * 100.0), 2) if (blks_hit + blks_read) > 0 else 100.0

        # These require extensions or historical stats; provide best-effort placeholders
        avg_query_ms = None
        qps = None

        return _ok({
            'total_size_gb': round(total_size_bytes / (1024**3), 3),
            'used_space_gb': None,
            'free_space_gb': None,
            'table_count': int(table_count),
            'index_count': int(index_count),
            'connection_count': int(connection_count),
            'active_queries': int(active_queries),
            'cache_hit_ratio': cache_hit_ratio,
            'avg_query_ms': avg_query_ms,
            'qps': qps
        })
    except Exception as e:
        logger.error(f"Error getting DB metrics: {e}")
        return _error('Failed to get DB metrics', status=500, code='db_metrics_failed')


@admin_bp.route('/db/queries/recent', methods=['GET'])
@require_admin
def get_db_recent_queries_alias():
    """Recent queries from pg_stat_activity (best-effort)."""
    try:
        limit = min(request.args.get('limit', 50, type=int), 200)
        rows = db.session.execute(text("""
            SELECT pid, datname, query, state, query_start
            FROM pg_stat_activity
            WHERE datname = current_database()
            ORDER BY query_start DESC NULLS LAST
            LIMIT :limit
        """), {'limit': limit}).fetchall()

        items = []
        now = datetime.utcnow()
        for r in rows:
            query_start = r.query_start or now
            duration_ms = int((now - query_start).total_seconds() * 1000)
            items.append({
                'id': str(r.pid),
                'query': r.query,
                'database': r.datname,
                'execution_ms': duration_ms,
                'rows': None,
                'timestamp': query_start.isoformat(),
                'status': r.state,
                'cpu_pct': None,
                'mem_mb': None
            })
        return _ok({'items': items, 'total': len(items)})
    except Exception as e:
        logger.error(f"Error getting recent DB queries: {e}")
        return _error('Failed to get recent queries', status=500, code='db_recent_queries_failed')


@admin_bp.route('/db/performance/series', methods=['GET'])
@require_admin
def get_db_performance_series():
    """Approximate DB performance using API usage as a proxy: [{ time, queries, response_ms }]."""
    try:
        range_q = (request.args.get('range') or '24h').lower()
        if range_q.endswith('h'):
            hours = int(range_q[:-1] or 24)
            start_time = datetime.utcnow() - timedelta(hours=hours)
            granularity = 'hour'
        else:
            days = int(range_q[:-1] or 7) if range_q.endswith('d') else int(range_q or 7)
            start_time = datetime.utcnow() - timedelta(days=days)
            granularity = 'day'

        bucket = func.date_trunc(granularity, UsageInsight.timestamp).label('bucket')
        dur_ms = cast(UsageInsight.duration_seconds * 1000.0, Float)
        q = db.session.query(
            bucket,
            func.count().label('count'),
            func.avg(dur_ms).label('avg_ms')
        ).filter(
            UsageInsight.event_type == 'api_call',
            UsageInsight.timestamp >= start_time
        ).group_by(bucket).order_by(bucket)
        rows = q.all()
        items = [{
            'time': (r.bucket if hasattr(r, 'bucket') else r[0]).isoformat(),
            'queries': int(getattr(r, 'count', 0) or 0),
            'response_ms': float(getattr(r, 'avg_ms', 0) or 0)
        } for r in rows]
        return _ok({'items': items, 'range': range_q, 'granularity': granularity, 'total': len(items)})
    except Exception as e:
        logger.error(f"Error building DB performance series: {e}")
        return _error('Failed to build DB performance series', status=500, code='db_performance_series_failed')


@admin_bp.route('/db/query', methods=['POST'])
@require_admin
def execute_readonly_query():
    """Execute a safe, read-only SQL query. Payload: { sql }
    Restrictions: must start with SELECT; single statement; limited result size.
    """
    try:
        data = request.get_json() or {}
        sql = (data.get('sql') or '').strip()
        if not sql:
            return _error('sql is required', status=400, code='validation_error')
        sql_lower = sql.lower().strip()
        if not sql_lower.startswith('select'):
            return _error('Only SELECT queries are allowed', status=400, code='forbidden_query')
        # rudimentary single-statement guard
        if ';' in sql[:-1]:
            return _error('Multiple statements are not allowed', status=400, code='validation_error')

        t0 = time.time()
        result = db.session.execute(text(sql))
        rows = result.fetchall()
        columns = list(result.keys())
        execution_ms = int((time.time() - t0) * 1000)

        # Cap rows returned to 1000 for safety
        max_rows = 1000
        rows = rows[:max_rows]
        payload_rows = [list(r) for r in rows]

        return _ok({
            'columns': columns,
            'rows': payload_rows,
            'row_count': len(payload_rows),
            'execution_ms': execution_ms
        })
    except Exception as e:
        logger.error(f"Error executing read-only query: {e}")
        return _error('Failed to execute query', status=500, code='db_query_failed')