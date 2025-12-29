"""
WebSocket API endpoints for real-time features and live dashboard.
Provides REST endpoints that complement WebSocket functionality.
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from app import db
from app.models.user import User
from app.models.queue import AnalysisQueue, QueueStatus, BatchUpload
from app.models.analysis import Analysis
from app.models.resume import Resume
from app.models.admin import AdminUser
from app.models.api_management import AccessLog
from app.models.analytics import UsageInsight
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)

websocket_bp = Blueprint('websocket', __name__)

# Admin WebSocket namespace for real-time updates
admin_websocket_clients = set()

def emit_admin_event(event_type, data):
    """Emit events to admin WebSocket clients."""
    if hasattr(current_app, 'socketio'):
        current_app.socketio.emit(event_type, data, namespace='/admin')

def get_current_connections():
    """Get current WebSocket connections count."""
    try:
        if hasattr(current_app, 'socketio'):
            return len(admin_websocket_clients)
        return 0
    except Exception:
        return 0

# ============================================================================
# ADMIN WEBSOCKET EVENTS
# ============================================================================

def emit_health_update():
    """Emit real-time health update to admin clients."""
    try:
        from app.services.analytics_service import analytics_service
        
        # Get system metrics
        metrics = analytics_service.collect_system_metrics()
        
        # Calculate health status
        api_status = 'healthy' if metrics.get('cpu_usage', 0) < 80 else 'warning'
        database_status = 'healthy' if metrics.get('database', {}).get('active_connections', 0) > 0 else 'error'
        
        # Mock AI service and queue worker status (would be real in production)
        ai_service_status = 'healthy'
        queue_worker_status = 'healthy'
        
        # Calculate uptime percentage (mock - would be real monitoring)
        uptime_pct = 99.9
        
        health_data = {
            'api_status': api_status,
            'database_status': database_status,
            'ai_service_status': ai_service_status,
            'queue_worker_status': queue_worker_status,
            'response_ms': metrics.get('response_time_avg', 0),
            'uptime_pct': uptime_pct,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        emit_admin_event('health_update', health_data)
        
    except Exception as e:
        logger.error(f"Error emitting health update: {e}")

def emit_performance_metric(metric_type, value):
    """Emit real-time performance metric to admin clients."""
    try:
        metric_data = {
            'metric': metric_type,
            'time': datetime.utcnow().isoformat(),
            'value': value
        }
        
        emit_admin_event('performance_metric', metric_data)
        
    except Exception as e:
        logger.error(f"Error emitting performance metric: {e}")

def emit_alert_created(alert_id, severity, title):
    """Emit new alert notification to admin clients."""
    try:
        alert_data = {
            'id': alert_id,
            'severity': severity,
            'title': title,
            'created_at': datetime.utcnow().isoformat()
        }
        
        emit_admin_event('alert_created', alert_data)
        
    except Exception as e:
        logger.error(f"Error emitting alert: {e}")

def emit_access_log_created(access_log):
    """Emit new access log entry to admin clients."""
    try:
        if isinstance(access_log, AccessLog):
            log_data = access_log.to_dict()
        else:
            log_data = access_log
            
        emit_admin_event('access_log_created', log_data)
        
    except Exception as e:
        logger.error(f"Error emitting access log: {e}")

def emit_api_log_created(api_log):
    """Emit new API log entry to admin clients."""
    try:
        if isinstance(api_log, UsageInsight):
            metadata = api_log.event_metadata or {}
            log_data = {
                'id': str(api_log.id),
                'method': metadata.get('method', 'GET'),
                'path': metadata.get('path', 'unknown'),
                'status': metadata.get('status_code'),
                'response_ms': round((api_log.duration_seconds or 0) * 1000, 2),
                'user_email': api_log.user.email if api_log.user_id and hasattr(api_log, 'user') and api_log.user else None,
                'ip': api_log.ip_address,
                'timestamp': api_log.timestamp.isoformat()
            }
        else:
            log_data = api_log
            
        emit_admin_event('api_log_created', log_data)
        
    except Exception as e:
        logger.error(f"Error emitting API log: {e}")

def emit_backup_progress(backup_id, progress_pct, status):
    """Emit backup progress update to admin clients."""
    try:
        backup_data = {
            'backup_id': backup_id,
            'progress_pct': progress_pct,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        emit_admin_event('backup_progress', backup_data)
        
    except Exception as e:
        logger.error(f"Error emitting backup progress: {e}")

# ============================================================================
# REGULAR WEBSOCKET ENDPOINTS
# ============================================================================

@websocket_bp.route('/stats', methods=['GET'])
def get_system_stats():
    """Get real-time system statistics for dashboard."""
    try:
        # Queue statistics
        queue_stats = {
            'pending': AnalysisQueue.query.filter_by(status=QueueStatus.PENDING.value).count(),
            'processing': AnalysisQueue.query.filter_by(status=QueueStatus.PROCESSING.value).count(),
            'completed_today': AnalysisQueue.query.filter(
                and_(
                    AnalysisQueue.status == QueueStatus.COMPLETED.value,
                    AnalysisQueue.completed_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                )
            ).count(),
            'failed_today': AnalysisQueue.query.filter(
                and_(
                    AnalysisQueue.status == QueueStatus.FAILED.value,
                    AnalysisQueue.updated_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                )
            ).count()
        }
        
        # User statistics
        user_stats = {
            'total_users': User.query.count(),
            'active_today': User.query.filter(
                User.last_login >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count() if hasattr(User, 'last_login') else 0,
            'admin_users': User.query.filter_by(is_admin=True).count()
        }
        
        # Processing statistics
        processing_stats = {
            'total_resumes': Resume.query.count(),
            'total_analyses': Analysis.query.count(),
            'analyses_today': Analysis.query.filter(
                Analysis.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count(),
            'avg_processing_time': get_average_processing_time()
        }
        
        # WebSocket connection stats
        websocket_stats = {}
        if hasattr(current_app, 'websocket_service'):
            websocket_stats = current_app.websocket_service.get_connected_users_stats()
        
        return jsonify({
            'queue': queue_stats,
            'users': user_stats,
            'processing': processing_stats,
            'websocket': websocket_stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        return jsonify({'error': 'Failed to get system statistics'}), 500

def get_average_processing_time():
    """Calculate average processing time for completed analyses."""
    try:
        completed_items = AnalysisQueue.query.filter(
            and_(
                AnalysisQueue.status == QueueStatus.COMPLETED.value,
                AnalysisQueue.started_at.isnot(None),
                AnalysisQueue.completed_at.isnot(None),
                AnalysisQueue.completed_at >= datetime.utcnow() - timedelta(days=7)  # Last 7 days
            )
        ).all()
        
        if not completed_items:
            return 0
        
        total_time = sum([
            (item.completed_at - item.started_at).total_seconds()
            for item in completed_items
        ])
        
        return round(total_time / len(completed_items), 2)
        
    except Exception:
        return 0

@websocket_bp.route('/queue/live', methods=['GET'])
def get_live_queue_data():
    """Get live queue data for dashboard."""
    try:
        # Get pending queue items with user info
        pending_items = db.session.query(
            AnalysisQueue, User, Resume
        ).join(
            User, AnalysisQueue.user_id == User.id
        ).join(
            Resume, AnalysisQueue.resume_id == Resume.id
        ).filter(
            AnalysisQueue.status == QueueStatus.PENDING.value
        ).order_by(
            AnalysisQueue.priority.desc(),
            AnalysisQueue.created_at
        ).limit(20).all()
        
        # Get processing items
        processing_items = db.session.query(
            AnalysisQueue, User, Resume
        ).join(
            User, AnalysisQueue.user_id == User.id
        ).join(
            Resume, AnalysisQueue.resume_id == Resume.id
        ).filter(
            AnalysisQueue.status == QueueStatus.PROCESSING.value
        ).all()
        
        # Format data
        pending_data = []
        for queue_item, user, resume in pending_items:
            pending_data.append({
                'id': str(queue_item.id),
                'position': queue_item.queue_position,
                'user_email': user.email,
                'resume_filename': resume.original_filename,
                'priority': queue_item.priority,
                'created_at': queue_item.created_at.isoformat(),
                'estimated_completion': queue_item.estimated_completion_time.isoformat() if queue_item.estimated_completion_time else None
            })
        
        processing_data = []
        for queue_item, user, resume in processing_items:
            processing_data.append({
                'id': str(queue_item.id),
                'user_email': user.email,
                'resume_filename': resume.original_filename,
                'started_at': queue_item.started_at.isoformat() if queue_item.started_at else None,
                'processing_time': (datetime.utcnow() - queue_item.started_at).total_seconds() if queue_item.started_at else 0
            })
        
        return jsonify({
            'pending': pending_data,
            'processing': processing_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting live queue data: {str(e)}")
        return jsonify({'error': 'Failed to get live queue data'}), 500

@websocket_bp.route('/analytics/hourly', methods=['GET'])
def get_hourly_analytics():
    """Get hourly analytics for the last 24 hours."""
    try:
        hours = int(request.args.get('hours', 24))
        
        # Generate hourly buckets
        now = datetime.utcnow()
        hourly_data = []
        
        for i in range(hours):
            hour_start = now - timedelta(hours=i+1)
            hour_end = now - timedelta(hours=i)
            
            # Count completed analyses in this hour
            completed = AnalysisQueue.query.filter(
                and_(
                    AnalysisQueue.status == QueueStatus.COMPLETED.value,
                    AnalysisQueue.completed_at >= hour_start,
                    AnalysisQueue.completed_at < hour_end
                )
            ).count()
            
            # Count failed analyses in this hour
            failed = AnalysisQueue.query.filter(
                and_(
                    AnalysisQueue.status == QueueStatus.FAILED.value,
                    AnalysisQueue.updated_at >= hour_start,
                    AnalysisQueue.updated_at < hour_end
                )
            ).count()
            
            # Count new submissions in this hour
            submitted = AnalysisQueue.query.filter(
                and_(
                    AnalysisQueue.created_at >= hour_start,
                    AnalysisQueue.created_at < hour_end
                )
            ).count()
            
            hourly_data.append({
                'hour': hour_start.strftime('%Y-%m-%d %H:00'),
                'completed': completed,
                'failed': failed,
                'submitted': submitted
            })
        
        # Reverse to show oldest to newest
        hourly_data.reverse()
        
        return jsonify({
            'data': hourly_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting hourly analytics: {str(e)}")
        return jsonify({'error': 'Failed to get hourly analytics'}), 500

@websocket_bp.route('/analytics/users', methods=['GET'])
def get_user_analytics():
    """Get user analytics and activity."""
    try:
        # Top users by analysis count
        top_users = db.session.query(
            User.email,
            User.first_name,
            User.last_name,
            func.count(Analysis.id).label('analysis_count')
        ).join(
            Analysis, User.id == Analysis.user_id
        ).group_by(
            User.id, User.email, User.first_name, User.last_name
        ).order_by(
            func.count(Analysis.id).desc()
        ).limit(10).all()
        
        # Users with most credits used
        top_credit_users = db.session.query(
            User.email,
            User.first_name,
            User.last_name,
            User.total_credits_purchased,
            User.credits_balance
        ).filter(
            User.total_credits_purchased > 0
        ).order_by(
            User.total_credits_purchased.desc()
        ).limit(10).all()
        
        # Recent user registrations
        recent_users = User.query.order_by(
            User.created_at.desc()
        ).limit(5).all()
        
        return jsonify({
            'top_users': [
                {
                    'email': user.email,
                    'name': f"{user.first_name} {user.last_name}",
                    'analysis_count': user.analysis_count
                }
                for user in top_users
            ],
            'top_credit_users': [
                {
                    'email': user.email,
                    'name': f"{user.first_name} {user.last_name}",
                    'credits_purchased': user.total_credits_purchased,
                    'credits_balance': user.credits_balance
                }
                for user in top_credit_users
            ],
            'recent_users': [
                {
                    'email': user.email,
                    'name': f"{user.first_name} {user.last_name}",
                    'created_at': user.created_at.isoformat(),
                    'is_admin': user.is_admin
                }
                for user in recent_users
            ],
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting user analytics: {str(e)}")
        return jsonify({'error': 'Failed to get user analytics'}), 500

@websocket_bp.route('/system/health', methods=['GET'])
def get_system_health():
    """Get detailed system health information."""
    try:
        # Database health
        db_health = check_database_health()
        
        # Queue health
        queue_health = check_queue_health()
        
        # WebSocket health
        websocket_health = check_websocket_health()
        
        # Overall health status
        overall_status = 'healthy'
        if not db_health['healthy'] or not queue_health['healthy']:
            overall_status = 'unhealthy'
        elif not websocket_health['healthy']:
            overall_status = 'degraded'
        
        return jsonify({
            'status': overall_status,
            'database': db_health,
            'queue': queue_health,
            'websocket': websocket_health,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

def check_database_health():
    """Check database connectivity and performance."""
    try:
        # Simple query to test connectivity
        start_time = datetime.utcnow()
        User.query.count()
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            'healthy': True,
            'response_time_ms': round(response_time, 2),
            'status': 'connected'
        }
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'status': 'disconnected'
        }

def check_queue_health():
    """Check queue system health."""
    try:
        # Check for stuck processing items
        stuck_items = AnalysisQueue.query.filter(
            and_(
                AnalysisQueue.status == QueueStatus.PROCESSING.value,
                AnalysisQueue.started_at < datetime.utcnow() - timedelta(minutes=30)
            )
        ).count()
        
        # Check queue backlog
        pending_count = AnalysisQueue.query.filter_by(status=QueueStatus.PENDING.value).count()
        
        return {
            'healthy': stuck_items == 0,
            'stuck_items': stuck_items,
            'pending_count': pending_count,
            'warning': stuck_items > 0 or pending_count > 50
        }
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e)
        }

def check_websocket_health():
    """Check WebSocket system health."""
    try:
        if hasattr(current_app, 'websocket_service'):
            stats = current_app.websocket_service.get_connected_users_stats()
            return {
                'healthy': True,
                'connected_sessions': stats.get('total_sessions', 0),
                'user_sessions': stats.get('user_sessions', 0),
                'admin_sessions': stats.get('admin_sessions', 0)
            }
        else:
            return {
                'healthy': False,
                'error': 'WebSocket service not initialized'
            }
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e)
        }

@websocket_bp.route('/broadcast/test', methods=['POST'])
def test_broadcast():
    """Test endpoint for broadcasting messages (admin only)."""
    try:
        # In a real app, add admin authentication here
        data = request.get_json()
        message = data.get('message', 'Test broadcast message')
        alert_type = data.get('type', 'info')
        level = data.get('level', 'info')
        
        if hasattr(current_app, 'websocket_service'):
            current_app.websocket_service.notify_system_alert(alert_type, message, level)
            return jsonify({
                'status': 'success',
                'message': 'Broadcast sent',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'WebSocket service not available'}), 500
            
    except Exception as e:
        logger.error(f"Error sending test broadcast: {str(e)}")
        return jsonify({'error': 'Failed to send broadcast'}), 500

@websocket_bp.route('/dashboard/refresh', methods=['POST'])
def refresh_dashboard():
    """Trigger dashboard data refresh for all connected admin users."""
    try:
        if hasattr(current_app, 'websocket_service'):
            current_app.websocket_service.broadcast_dashboard_update()
            return jsonify({
                'status': 'success',
                'message': 'Dashboard refresh triggered',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'WebSocket service not available'}), 500
            
    except Exception as e:
        logger.error(f"Error refreshing dashboard: {str(e)}")
        return jsonify({'error': 'Failed to refresh dashboard'}), 500
