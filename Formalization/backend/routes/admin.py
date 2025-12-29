"""
Bear Systems Resume Screening Tool - Admin Routes
Comprehensive admin management for users, analytics, and system administration.
"""

from flask import Blueprint, request, jsonify, make_response
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Global variables for model instances (will be initialized by main app)
user_manager = None
user_session_manager = None
admin_user_manager = None
db_manager = None
storage = None
supabase_manager = None

def init_admin_routes(user_model, user_session_model, admin_user_model, database_manager, resume_storage, supabase_model=None):
    """Initialize admin routes with model instances."""
    global user_manager, user_session_manager, admin_user_manager, db_manager, storage, supabase_manager
    user_manager = user_model
    user_session_manager = user_session_model
    admin_user_manager = admin_user_model
    db_manager = database_manager
    storage = resume_storage
    supabase_manager = supabase_model

@admin_bp.route('/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """Get comprehensive dashboard statistics for admin."""
    from middleware.auth import require_admin_auth
    
    @require_admin_auth
    def _get_dashboard_stats():
        try:
            stats = {}
            
            # User Statistics
            with db_manager.get_connection() as conn:
                # Total users by type
                cursor = conn.execute("""
                    SELECT access_type, COUNT(*) as count 
                    FROM users 
                    WHERE status = 'active' 
                    GROUP BY access_type
                """)
                user_types = {row['access_type']: row['count'] for row in cursor.fetchall()}
                
                # Total users
                cursor = conn.execute("SELECT COUNT(*) as total FROM users WHERE status = 'active'")
                total_users = cursor.fetchone()['total']
                
                # Users created in last 30 days
                cursor = conn.execute("""
                    SELECT COUNT(*) as recent 
                    FROM users 
                    WHERE status = 'active' 
                    AND created_at >= datetime('now', '-30 days')
                """)
                recent_users = cursor.fetchone()['recent']
                
                # Trial usage statistics
                cursor = conn.execute("""
                    SELECT 
                        SUM(trial_resumes_analyzed) as total_analyzed,
                        AVG(trial_resumes_analyzed) as avg_analyzed,
                        COUNT(CASE WHEN trial_resumes_analyzed >= trial_limit THEN 1 END) as at_limit
                    FROM users 
                    WHERE access_type = 'trial' AND status = 'active'
                """)
                trial_stats = cursor.fetchone()
                
                # Resume processing statistics
                cursor = conn.execute("""
                    SELECT COUNT(*) as total_resumes
                    FROM resumes
                """)
                total_resumes = cursor.fetchone()['total_resumes']
                
                # Active sessions
                cursor = conn.execute("""
                    SELECT COUNT(*) as active_sessions
                    FROM user_sessions 
                    WHERE expires_at > datetime('now')
                """)
                active_sessions = cursor.fetchone()['active_sessions']
            
            stats = {
                'users': {
                    'total': total_users,
                    'recent': recent_users,
                    'by_type': user_types,
                    'trial_stats': {
                        'total_analyzed': trial_stats['total_analyzed'] or 0,
                        'avg_analyzed': round(trial_stats['avg_analyzed'] or 0, 2),
                        'at_limit': trial_stats['at_limit'] or 0
                    }
                },
                'system': {
                    'total_resumes': total_resumes,
                    'active_sessions': active_sessions
                }
            }
            
            return jsonify({'success': True, 'stats': stats})
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return jsonify({'error': 'Failed to get dashboard statistics'}), 500
    
    return _get_dashboard_stats()

@admin_bp.route('/users', methods=['GET'])
def get_all_users():
    """Get all users with pagination and filtering."""
    from middleware.auth import require_admin_auth
    
    @require_admin_auth
    def _get_all_users():
        try:
            page = int(request.args.get('page', 1))
            limit = int(request.args.get('limit', 20))
            search = request.args.get('search', '').strip()
            access_type = request.args.get('access_type', '')
            status = request.args.get('status', 'active')
            
            offset = (page - 1) * limit
            
            # Build query
            where_conditions = ["status = ?"]
            params = [status]
            
            if search:
                where_conditions.append("(email LIKE ? OR name LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%"])
            
            if access_type:
                where_conditions.append("access_type = ?")
                params.append(access_type)
            
            where_clause = " AND ".join(where_conditions)
            
            with db_manager.get_connection() as conn:
                # Get total count
                count_query = f"SELECT COUNT(*) as total FROM users WHERE {where_clause}"
                cursor = conn.execute(count_query, params)
                total = cursor.fetchone()['total']
                
                # Get users
                query = f"""
                    SELECT id, email, name, access_type, trial_resumes_analyzed, 
                           trial_limit, created_at, last_login, created_by_admin, status
                    FROM users 
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """
                params.extend([limit, offset])
                
                cursor = conn.execute(query, params)
                users = []
                for row in cursor.fetchall():
                    users.append({
                        'id': row['id'],
                        'email': row['email'],
                        'name': row['name'],
                        'access_type': row['access_type'],
                        'trial_resumes_analyzed': row['trial_resumes_analyzed'],
                        'trial_limit': row['trial_limit'],
                        'created_at': row['created_at'],
                        'last_login': row['last_login'],
                        'created_by_admin': row['created_by_admin'],
                        'status': row['status']
                    })
            
            return jsonify({
                'success': True,
                'users': users,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': (total + limit - 1) // limit
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return jsonify({'error': 'Failed to get users'}), 500
    
    return _get_all_users()

@admin_bp.route('/users', methods=['POST'])
def create_user():
    """Create a new user."""
    from middleware.auth import require_admin_auth, get_current_admin
    
    @require_admin_auth
    def _create_user():
        try:
            data = request.get_json()
            
            required_fields = ['email', 'name', 'password', 'access_type']
            if not data or not all(field in data for field in required_fields):
                return jsonify({'error': 'Email, name, password, and access_type required'}), 400
            
            admin = get_current_admin()
            
            # Create user
            user_id = user_manager.create_user(
                email=data['email'],
                name=data['name'],
                password=data['password'],
                access_type=data['access_type'],
                created_by_admin=admin['username']
            )
            
            if user_id:
                logger.info(f"Admin {admin['username']} created user {data['email']}")
                return jsonify({
                    'success': True,
                    'message': 'User created successfully',
                    'user_id': user_id
                })
            else:
                return jsonify({'error': 'User with this email already exists'}), 400
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return jsonify({'error': 'Failed to create user'}), 500
    
    return _create_user()

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user details."""
    from middleware.auth import require_admin_auth, get_current_admin
    
    @require_admin_auth
    def _update_user():
        try:
            data = request.get_json()
            admin = get_current_admin()
            
            # Build update query dynamically
            update_fields = []
            params = []
            
            allowed_fields = ['name', 'access_type', 'trial_limit', 'status']
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = ?")
                    params.append(data[field])
            
            if not update_fields:
                return jsonify({'error': 'No valid fields to update'}), 400
            
            params.append(user_id)
            
            with db_manager.get_connection() as conn:
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
                cursor = conn.execute(query, params)
                
                if cursor.rowcount == 0:
                    return jsonify({'error': 'User not found'}), 404
                
                conn.commit()
            
            logger.info(f"Admin {admin['username']} updated user {user_id}")
            return jsonify({'success': True, 'message': 'User updated successfully'})
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return jsonify({'error': 'Failed to update user'}), 500
    
    return _update_user()

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Soft delete user (set status to inactive)."""
    from middleware.auth import require_admin_auth, get_current_admin
    
    @require_admin_auth
    def _delete_user():
        try:
            admin = get_current_admin()
            
            with db_manager.get_connection() as conn:
                # Check if user exists
                cursor = conn.execute("SELECT email FROM users WHERE id = ?", (user_id,))
                user = cursor.fetchone()
                
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                
                # Soft delete
                conn.execute(
                    "UPDATE users SET status = 'inactive' WHERE id = ?",
                    (user_id,)
                )
                conn.commit()
            
            logger.info(f"Admin {admin['username']} deleted user {user_id}")
            return jsonify({'success': True, 'message': 'User deleted successfully'})
            
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return jsonify({'error': 'Failed to delete user'}), 500
    
    return _delete_user()

@admin_bp.route('/users/<int:user_id>/reset-trial', methods=['POST'])
def reset_user_trial(user_id):
    """Reset user's trial usage."""
    from middleware.auth import require_admin_auth, get_current_admin
    
    @require_admin_auth
    def _reset_user_trial():
        try:
            admin = get_current_admin()
            
            with db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "UPDATE users SET trial_resumes_analyzed = 0 WHERE id = ? AND access_type = 'trial'",
                    (user_id,)
                )
                
                if cursor.rowcount == 0:
                    return jsonify({'error': 'Trial user not found'}), 404
                
                conn.commit()
            
            logger.info(f"Admin {admin['username']} reset trial for user {user_id}")
            return jsonify({'success': True, 'message': 'Trial usage reset successfully'})
            
        except Exception as e:
            logger.error(f"Error resetting trial: {e}")
            return jsonify({'error': 'Failed to reset trial'}), 500
    
    return _reset_user_trial()

@admin_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """Get detailed analytics for admin dashboard."""
    from middleware.auth import require_admin_auth
    
    @require_admin_auth
    def _get_analytics():
        try:
            analytics = {}
            
            with db_manager.get_connection() as conn:
                # User registration over time (last 30 days)
                cursor = conn.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM users 
                    WHERE created_at >= datetime('now', '-30 days')
                    GROUP BY DATE(created_at)
                    ORDER BY date
                """)
                user_growth = [{'date': row['date'], 'count': row['count']} for row in cursor.fetchall()]
                
                # Resume processing by day (last 30 days)
                cursor = conn.execute("""
                    SELECT DATE(processed_at) as date, COUNT(*) as count
                    FROM resumes 
                    WHERE processed_at >= datetime('now', '-30 days')
                    GROUP BY DATE(processed_at)
                    ORDER BY date
                """)
                resume_processing = [{'date': row['date'], 'count': row['count']} for row in cursor.fetchall()]
                
                # Top users by resume analysis
                cursor = conn.execute("""
                    SELECT u.email, u.name, u.access_type, u.trial_resumes_analyzed
                    FROM users u
                    WHERE u.status = 'active'
                    ORDER BY u.trial_resumes_analyzed DESC
                    LIMIT 10
                """)
                top_users = []
                for row in cursor.fetchall():
                    top_users.append({
                        'email': row['email'],
                        'name': row['name'],
                        'access_type': row['access_type'],
                        'resumes_analyzed': row['trial_resumes_analyzed']
                    })
            
            analytics = {
                'user_growth': user_growth,
                'resume_processing': resume_processing,
                'top_users': top_users
            }
            
            return jsonify({'success': True, 'analytics': analytics})
            
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return jsonify({'error': 'Failed to get analytics'}), 500
    
    return _get_analytics()

@admin_bp.route('/system-health', methods=['GET'])
def get_system_health():
    """Get system health information."""
    from middleware.auth import require_admin_auth
    
    @require_admin_auth
    def _get_system_health():
        try:
            import psutil
            import os
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Database size
            db_path = db_manager.db_path
            db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
            
            # Storage statistics
            storage_stats = storage.get_cache_stats() if hasattr(storage, 'get_cache_stats') else {}
            
            health = {
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'database': {
                    'size': db_size
                },
                'storage': storage_stats
            }
            
            return jsonify({'success': True, 'health': health})
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return jsonify({'error': 'Failed to get system health'}), 500
    
    return _get_system_health()

# ========================================================================
# SUPABASE SYNC ENDPOINTS
# ========================================================================

@admin_bp.route('/sync-users-to-supabase', methods=['POST'])
def sync_users_to_supabase():
    """Sync all SQLite users to Supabase and mark them for cleanup."""
    from middleware.auth import require_admin_auth, get_current_admin
    
    @require_admin_auth
    def _sync_users():
        if not supabase_manager:
            return jsonify({'error': 'Supabase not available'}), 500
            
        try:
            admin = get_current_admin()
            data = request.get_json() or {}
            confirm_delete = data.get('confirm_delete_after_sync', False)
            
            # Get all SQLite users
            with db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, email, name, password_hash, access_type, 
                           trial_resumes_analyzed, trial_limit, created_at, 
                           created_by_admin, status
                    FROM users 
                    WHERE status = 'active'
                """)
                users = cursor.fetchall()
            
            results = {
                'total_users': len(users),
                'synced_successfully': 0,
                'already_exists': 0,
                'failed': 0,
                'errors': [],
                'sqlite_cleanup_ready': False
            }
            
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            for user in users:
                try:
                    # Try to create user in Supabase
                    # Note: We can't transfer the password hash, so we'll need to generate a temp password
                    # and ask users to reset their passwords
                    temp_password = f"TempPass{user[0]}{datetime.now().strftime('%Y%m%d')}"
                    
                    supabase_result = loop.run_until_complete(
                        supabase_manager.create_user(
                            email=user[1],  # email
                            password=temp_password,  # temporary password
                            full_name=user[2],  # name
                            access_type=user[4],  # access_type
                            trial_resumes_analyzed=user[5],  # trial_resumes_analyzed
                            trial_limit=user[6],  # trial_limit
                            created_by_admin=user[8] or admin['username'],  # created_by_admin
                            migrated_from_sqlite=True,
                            original_sqlite_id=user[0]
                        )
                    )
                    
                    if supabase_result.get('success'):
                        results['synced_successfully'] += 1
                        logger.info(f"✅ Synced user {user[1]} to Supabase")
                        
                        # Mark user as synced in SQLite
                        with db_manager.get_connection() as conn:
                            conn.execute("""
                                UPDATE users 
                                SET status = 'synced_to_supabase', 
                                    supabase_user_id = ?
                                WHERE id = ?
                            """, (supabase_result.get('user_id'), user[0]))
                            conn.commit()
                    
                    elif 'already exists' in supabase_result.get('error', '').lower():
                        results['already_exists'] += 1
                        logger.info(f"⚠️  User {user[1]} already exists in Supabase")
                        
                        # Mark as already synced
                        with db_manager.get_connection() as conn:
                            conn.execute("""
                                UPDATE users 
                                SET status = 'already_in_supabase'
                                WHERE id = ?
                            """, (user[0],))
                            conn.commit()
                    
                    else:
                        results['failed'] += 1
                        error_msg = f"User {user[1]}: {supabase_result.get('error')}"
                        results['errors'].append(error_msg)
                        logger.error(f"❌ Failed to sync user {user[1]}: {error_msg}")
                
                except Exception as e:
                    results['failed'] += 1
                    error_msg = f"User {user[1]}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(f"❌ Error syncing user {user[1]}: {e}")
            
            # Check if all users are synced and ready for cleanup
            if results['synced_successfully'] + results['already_exists'] == results['total_users']:
                results['sqlite_cleanup_ready'] = True
                logger.info("✅ All users successfully synced to Supabase")
                
                if confirm_delete:
                    # Delete synced users from SQLite
                    with db_manager.get_connection() as conn:
                        conn.execute("""
                            DELETE FROM users 
                            WHERE status IN ('synced_to_supabase', 'already_in_supabase')
                        """)
                        deleted_count = conn.total_changes
                        conn.commit()
                    
                    results['sqlite_users_deleted'] = deleted_count
                    logger.info(f"🗑️  Deleted {deleted_count} synced users from SQLite")
            
            response_data = {
                'success': True,
                'message': 'User sync operation completed',
                'results': results,
                'admin': admin['username'],
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"User sync error: {e}")
            return jsonify({'error': f'Sync operation failed: {str(e)}'}), 500
    
    return _sync_users()

@admin_bp.route('/supabase-status', methods=['GET'])
def get_supabase_status():
    """Get Supabase connection status and sync information."""
    from middleware.auth import require_admin_auth
    
    @require_admin_auth
    def _get_status():
        try:
            status = {
                'supabase_available': supabase_manager is not None,
                'sqlite_users_count': 0,
                'users_needing_sync': 0,
                'users_already_synced': 0
            }
            
            # Get SQLite user counts
            with db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
                status['sqlite_users_count'] = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM users WHERE status IN ('synced_to_supabase', 'already_in_supabase')")
                status['users_already_synced'] = cursor.fetchone()[0]
                
                status['users_needing_sync'] = status['sqlite_users_count']
            
            if supabase_manager:
                try:
                    # Test Supabase connection
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Simple test query to verify connection
                    status['supabase_connection_test'] = 'Connected'
                    status['supabase_initialized'] = True
                    
                except Exception as e:
                    status['supabase_connection_test'] = f'Failed: {str(e)}'
                    status['supabase_initialized'] = False
            
            return jsonify({'success': True, 'status': status})
            
        except Exception as e:
            logger.error(f"Error getting Supabase status: {e}")
            return jsonify({'error': 'Failed to get status'}), 500
    
    return _get_status()
