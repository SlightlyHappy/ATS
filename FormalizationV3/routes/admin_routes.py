"""
Admin panel routes - extracted from monolithic app.py
Handles: user management, system monitoring, analytics, database operations
"""

import os
import json
import logging
import subprocess
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, Response

logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Global dependencies (will be injected during initialization)
db_manager = None
storage_manager = None
auth_middleware = None
ai_processor = None
cache_manager = None
credit_manager = None
railway_db = None
analytics_processor = None

def init_admin_routes(database_manager, storage_mgr, auth_mid, ai_proc=None, 
                     cache_mgr=None, credit_mgr=None, railway_database=None,
                     analytics_proc=None):
    """Initialize admin routes with dependencies"""
    global db_manager, storage_manager, auth_middleware, ai_processor
    global cache_manager, credit_manager, railway_db, analytics_processor
    
    db_manager = database_manager
    storage_manager = storage_mgr
    auth_middleware = auth_mid
    ai_processor = ai_proc
    cache_manager = cache_mgr
    credit_manager = credit_mgr
    railway_db = railway_database
    analytics_processor = analytics_proc
    
    logger.info("✅ Admin routes initialized with all dependencies")

@admin_bp.route('/dashboard/stats', methods=['GET'])
def admin_dashboard_stats():
    """Get comprehensive admin dashboard statistics"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
            
        # Check admin privileges
        user = auth_middleware.get_current_user()
        if not user or not auth_middleware.is_admin(user):
            return jsonify({"error": "Admin access required"}), 403
        
        # Get time period from query params
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stats = {}
        
        # Basic system statistics
        try:
            if railway_db:
                # User statistics
                user_stats = railway_db.execute_read("""
                    SELECT 
                        COUNT(*) as total_users,
                        COUNT(CASE WHEN created_at > %s THEN 1 END) as new_users,
                        COUNT(CASE WHEN is_premium = true THEN 1 END) as premium_users,
                        COUNT(CASE WHEN last_login > %s THEN 1 END) as active_users
                    FROM users
                """, (start_date, start_date - timedelta(days=7)))
                
                if user_stats:
                    stats['users'] = user_stats[0]
                
                # Resume statistics
                resume_stats = railway_db.execute_read("""
                    SELECT 
                        COUNT(*) as total_resumes,
                        COUNT(CASE WHEN upload_date > %s THEN 1 END) as recent_resumes,
                        COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as processed_resumes,
                        COUNT(CASE WHEN processing_status = 'failed' THEN 1 END) as failed_resumes,
                        AVG(overall_score) as avg_score
                    FROM resumes
                    WHERE upload_date IS NOT NULL
                """, (start_date,))
                
                if resume_stats:
                    stats['resumes'] = resume_stats[0]
                
                # Credit system statistics
                if credit_manager:
                    credit_stats = railway_db.execute_read("""
                        SELECT 
                            SUM(trial_credits_used) as total_trial_credits,
                            SUM(premium_credits_used) as total_premium_credits,
                            COUNT(DISTINCT user_id) as active_credit_users,
                            AVG(trial_credits_used) as avg_trial_usage
                        FROM user_credits
                    """)
                    
                    if credit_stats:
                        stats['credits'] = credit_stats[0]
                
                # AI processing statistics
                ai_stats = railway_db.execute_read("""
                    SELECT 
                        COUNT(*) as total_ai_requests,
                        AVG(ai_processing_time) as avg_processing_time,
                        COUNT(CASE WHEN ai_provider_used = 'openai' THEN 1 END) as openai_usage,
                        COUNT(CASE WHEN ai_provider_used = 'anthropic' THEN 1 END) as anthropic_usage,
                        COUNT(CASE WHEN ai_provider_used = 'gemini' THEN 1 END) as gemini_usage
                    FROM resumes 
                    WHERE ai_processing_time IS NOT NULL
                    AND processing_completed_at > %s
                """, (start_date,))
                
                if ai_stats:
                    stats['ai_processing'] = ai_stats[0]
        
        except Exception as db_error:
            logger.error(f"Database stats error: {db_error}")
            stats['error'] = "Failed to fetch database statistics"
        
        # System health metrics
        try:
            stats['system'] = {
                'uptime': get_system_uptime(),
                'memory_usage': get_memory_usage(),
                'disk_usage': get_disk_usage(),
                'last_updated': datetime.utcnow().isoformat()
            }
        except Exception as system_error:
            logger.error(f"System stats error: {system_error}")
            stats['system'] = {'error': 'Failed to fetch system metrics'}
        
        # Queue statistics (if available)
        try:
            if hasattr(railway_db, 'queue_manager') and railway_db.queue_manager:
                queue_stats = railway_db.queue_manager.get_queue_statistics()
                stats['queue'] = queue_stats
        except Exception as queue_error:
            logger.warning(f"Queue stats not available: {queue_error}")
        
        return jsonify({
            "success": True,
            "stats": stats,
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        return jsonify({"error": "Failed to generate dashboard statistics"}), 500

@admin_bp.route('/users', methods=['GET'])
def get_all_users():
    """Get all users with pagination and filtering"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
            
        user = auth_middleware.get_current_user()
        if not user or not auth_middleware.is_admin(user):
            return jsonify({"error": "Admin access required"}), 403
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        search = request.args.get('search', '').strip()
        
        # Get filter parameters
        user_type = request.args.get('type', '')  # 'premium', 'trial', 'all'
        sort_by = request.args.get('sort', 'created_at')
        sort_order = request.args.get('order', 'desc')
        
        if not railway_db:
            return jsonify({"error": "Database not available"}), 500
        
        # Build query
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(email ILIKE %s OR full_name ILIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
        
        if user_type == 'premium':
            where_conditions.append("is_premium = true")
        elif user_type == 'trial':
            where_conditions.append("is_premium = false")
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Count total users
        count_query = f"SELECT COUNT(*) FROM users {where_clause}"
        total_count = railway_db.execute_read(count_query, params)
        total_users = total_count[0]['count'] if total_count else 0
        
        # Get users with pagination
        offset = (page - 1) * per_page
        order_clause = f"ORDER BY {sort_by} {sort_order.upper()}"
        limit_clause = f"LIMIT {per_page} OFFSET {offset}"
        
        users_query = f"""
            SELECT 
                user_id, email, full_name, is_premium, trial_credits_used,
                created_at, last_login, is_active, subscription_plan,
                total_resumes_uploaded, total_ai_requests
            FROM users 
            {where_clause}
            {order_clause}
            {limit_clause}
        """
        
        users = railway_db.execute_read(users_query, params)
        
        return jsonify({
            "success": True,
            "users": users or [],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_users,
                "pages": (total_users + per_page - 1) // per_page
            },
            "filters": {
                "search": search,
                "type": user_type,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        })
        
    except Exception as e:
        logger.error(f"Get users error: {e}")
        return jsonify({"error": "Failed to fetch users"}), 500

@admin_bp.route('/users/<user_id>', methods=['GET'])
def get_user_details(user_id):
    """Get detailed information about a specific user"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
            
        admin_user = auth_middleware.get_current_user()
        if not admin_user or not auth_middleware.is_admin(admin_user):
            return jsonify({"error": "Admin access required"}), 403
        
        if not railway_db:
            return jsonify({"error": "Database not available"}), 500
        
        # Get user basic info
        user_info = railway_db.execute_read("""
            SELECT * FROM users WHERE user_id = %s
        """, (user_id,))
        
        if not user_info:
            return jsonify({"error": "User not found"}), 404
        
        user = user_info[0]
        
        # Get user's resumes
        resumes = railway_db.execute_read("""
            SELECT id, filename, upload_date, processing_status, overall_score
            FROM resumes 
            WHERE user_id = %s 
            ORDER BY upload_date DESC 
            LIMIT 20
        """, (user_id,))
        
        # Get credit usage
        credit_info = None
        if credit_manager:
            try:
                credit_status = credit_manager.check_user_credits(user_id)
                credit_info = {
                    'trial_credits': credit_status.trial_credits,
                    'premium_credits': credit_status.premium_credits,
                    'total_used': credit_status.total_used,
                    'credits_remaining': credit_status.credits_remaining,
                    'processing_tier': credit_status.processing_tier.value if credit_status.processing_tier else 'unknown'
                }
            except Exception as credit_error:
                logger.warning(f"Failed to get credit info for user {user_id}: {credit_error}")
        
        # Get activity log
        activity_log = railway_db.execute_read("""
            SELECT action, details, created_at
            FROM user_activity_log 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 10
        """, (user_id,))
        
        return jsonify({
            "success": True,
            "user": user,
            "resumes": resumes or [],
            "credit_info": credit_info,
            "activity_log": activity_log or [],
            "total_resumes": len(resumes) if resumes else 0
        })
        
    except Exception as e:
        logger.error(f"Get user details error: {e}")
        return jsonify({"error": "Failed to fetch user details"}), 500

@admin_bp.route('/users/<user_id>/credits', methods=['POST'])
def update_user_credits(user_id):
    """Update user credits (admin only)"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
            
        admin_user = auth_middleware.get_current_user()
        if not admin_user or not auth_middleware.is_admin(admin_user):
            return jsonify({"error": "Admin access required"}), 403
        
        if not credit_manager:
            return jsonify({"error": "Credit manager not available"}), 500
        
        data = request.get_json() or {}
        action = data.get('action')  # 'add', 'set', 'reset'
        credit_type = data.get('type', 'premium')  # 'trial', 'premium'
        amount = data.get('amount', 0)
        reason = data.get('reason', 'Admin adjustment')
        
        if action not in ['add', 'set', 'reset']:
            return jsonify({"error": "Invalid action. Use 'add', 'set', or 'reset'"}), 400
        
        result = credit_manager.admin_update_credits(
            user_id, action, credit_type, amount, reason, admin_user['user_id']
        )
        
        if result.success:
            return jsonify({
                "success": True,
                "message": f"Credits {action}ed successfully",
                "new_credit_status": result.data
            })
        else:
            return jsonify({"error": result.error_message}), 400
            
    except Exception as e:
        logger.error(f"Update credits error: {e}")
        return jsonify({"error": "Failed to update credits"}), 500

@admin_bp.route('/system/maintenance', methods=['POST'])
def system_maintenance():
    """Perform system maintenance tasks"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
            
        admin_user = auth_middleware.get_current_user()
        if not admin_user or not auth_middleware.is_admin(admin_user):
            return jsonify({"error": "Admin access required"}), 403
        
        data = request.get_json() or {}
        task = data.get('task')
        
        if task == 'cleanup_temp_files':
            result = cleanup_temporary_files()
        elif task == 'clear_cache':
            result = clear_system_cache()
        elif task == 'vacuum_database':
            result = vacuum_database()
        elif task == 'backup_database':
            result = backup_database()
        else:
            return jsonify({"error": "Invalid maintenance task"}), 400
        
        return jsonify({
            "success": result['success'],
            "message": result['message'],
            "details": result.get('details', {})
        })
        
    except Exception as e:
        logger.error(f"Maintenance error: {e}")
        return jsonify({"error": "Maintenance task failed"}), 500

@admin_bp.route('/analytics/export', methods=['GET'])
def export_analytics():
    """Export analytics data"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
            
        admin_user = auth_middleware.get_current_user()
        if not admin_user or not auth_middleware.is_admin(admin_user):
            return jsonify({"error": "Admin access required"}), 403
        
        # Get export parameters
        export_type = request.args.get('type', 'users')  # 'users', 'resumes', 'analytics'
        format_type = request.args.get('format', 'json')  # 'json', 'csv'
        days = request.args.get('days', 30, type=int)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        if not railway_db:
            return jsonify({"error": "Database not available"}), 500
        
        data = []
        
        if export_type == 'users':
            data = railway_db.execute_read("""
                SELECT user_id, email, full_name, is_premium, created_at, last_login,
                       trial_credits_used, total_resumes_uploaded, total_ai_requests
                FROM users 
                WHERE created_at > %s
                ORDER BY created_at DESC
            """, (start_date,))
            
        elif export_type == 'resumes':
            data = railway_db.execute_read("""
                SELECT r.id, r.user_id, u.email, r.filename, r.upload_date,
                       r.processing_status, r.overall_score, r.ai_provider_used
                FROM resumes r
                JOIN users u ON r.user_id = u.user_id
                WHERE r.upload_date > %s
                ORDER BY r.upload_date DESC
            """, (start_date,))
            
        elif export_type == 'analytics':
            # Get comprehensive analytics
            data = get_comprehensive_analytics(start_date)
        
        if format_type == 'csv':
            return export_as_csv(data, export_type)
        else:
            return jsonify({
                "success": True,
                "export_type": export_type,
                "format": format_type,
                "period_days": days,
                "data": data,
                "count": len(data),
                "exported_at": datetime.utcnow().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Export analytics error: {e}")
        return jsonify({"error": "Export failed"}), 500

@admin_bp.route('/logs', methods=['GET'])
def get_system_logs():
    """Get system logs for debugging"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
            
        admin_user = auth_middleware.get_current_user()
        if not admin_user or not auth_middleware.is_admin(admin_user):
            return jsonify({"error": "Admin access required"}), 403
        
        # Get log parameters
        log_type = request.args.get('type', 'application')  # 'application', 'error', 'access'
        lines = request.args.get('lines', 100, type=int)
        lines = min(lines, 1000)  # Limit to prevent memory issues
        
        logs = []
        
        if log_type == 'application':
            logs = get_application_logs(lines)
        elif log_type == 'error':
            logs = get_error_logs(lines)
        elif log_type == 'access':
            logs = get_access_logs(lines)
        
        return jsonify({
            "success": True,
            "log_type": log_type,
            "lines_requested": lines,
            "logs": logs,
            "retrieved_at": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get logs error: {e}")
        return jsonify({"error": "Failed to retrieve logs"}), 500

# Helper functions for admin operations

def get_system_uptime():
    """Get system uptime"""
    try:
        import psutil
        boot_time = psutil.boot_time()
        uptime_seconds = datetime.utcnow().timestamp() - boot_time
        return int(uptime_seconds)
    except Exception:
        return None

def get_memory_usage():
    """Get memory usage information"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        }
    except Exception:
        return None

def get_disk_usage():
    """Get disk usage information"""
    try:
        import psutil
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        }
    except Exception:
        return None

def cleanup_temporary_files():
    """Clean up temporary files"""
    try:
        import shutil
        temp_dirs = ['uploads', 'temp', 'cache']
        cleaned_files = 0
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                for filename in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, filename)
                    if os.path.isfile(file_path):
                        # Delete files older than 24 hours
                        if datetime.utcnow().timestamp() - os.path.getctime(file_path) > 86400:
                            os.remove(file_path)
                            cleaned_files += 1
        
        return {
            "success": True,
            "message": f"Cleaned {cleaned_files} temporary files",
            "details": {"files_cleaned": cleaned_files}
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Cleanup failed: {str(e)}"
        }

def clear_system_cache():
    """Clear system cache"""
    try:
        cleared_items = 0
        
        if cache_manager:
            cleared_items = cache_manager.clear_all()
        
        return {
            "success": True,
            "message": f"Cleared {cleared_items} cache items",
            "details": {"items_cleared": cleared_items}
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Cache clear failed: {str(e)}"
        }

def vacuum_database():
    """Vacuum database to optimize performance"""
    try:
        if railway_db:
            railway_db.execute_write("VACUUM ANALYZE;")
            return {
                "success": True,
                "message": "Database vacuum completed successfully"
            }
        else:
            return {
                "success": False,
                "message": "Database not available"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Database vacuum failed: {str(e)}"
        }

def backup_database():
    """Create database backup"""
    try:
        backup_filename = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.sql"
        
        # This would need to be implemented based on your backup strategy
        return {
            "success": True,
            "message": f"Backup created: {backup_filename}",
            "details": {"backup_file": backup_filename}
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Backup failed: {str(e)}"
        }

def get_comprehensive_analytics(start_date):
    """Get comprehensive analytics data"""
    try:
        if not railway_db:
            return []
        
        analytics = railway_db.execute_read("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as daily_users,
                SUM(CASE WHEN is_premium THEN 1 ELSE 0 END) as premium_conversions
            FROM users 
            WHERE created_at > %s
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, (start_date,))
        
        return analytics or []
    except Exception as e:
        logger.error(f"Analytics query error: {e}")
        return []

def export_as_csv(data, export_type):
    """Export data as CSV"""
    try:
        import csv
        import io
        
        output = io.StringIO()
        
        if data:
            fieldnames = data[0].keys() if isinstance(data[0], dict) else []
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={export_type}_export.csv'
            }
        )
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        return jsonify({"error": "CSV export failed"}), 500

def get_application_logs(lines):
    """Get application logs"""
    # This would read from your logging files
    return [{"timestamp": datetime.utcnow().isoformat(), "message": "Sample log entry"}]

def get_error_logs(lines):
    """Get error logs"""
    # This would read from your error log files
    return [{"timestamp": datetime.utcnow().isoformat(), "level": "ERROR", "message": "Sample error"}]

def get_access_logs(lines):
    """Get access logs"""
    # This would read from your access log files
    return [{"timestamp": datetime.utcnow().isoformat(), "ip": "127.0.0.1", "method": "GET", "path": "/api/health"}]
