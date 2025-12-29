"""
Enhanced monitoring API endpoints for comprehensive system analytics.
Implements Priority 1.3: Enhanced Monitoring features and Performance Monitoring.
"""
from flask import Blueprint, jsonify, request, g, current_app
from datetime import datetime, timedelta
from typing import Dict, Any

from app.services.analytics_service import analytics_service
from app.services.auth_manager import require_admin, get_current_user
from app.services.error_handler import ApplicationError, ErrorCategory, ErrorSeverity
from app.models.analytics import PerformanceMetric, UsageInsight, ErrorTracking, SystemAlert
from app import db

# Create blueprint
monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/v1/monitoring')

# ========== Performance Monitoring Endpoints ==========

@monitoring_bp.route('/performance/current', methods=['GET'])
@require_admin
def get_current_performance():
    """Get current performance metrics from the performance monitoring service."""
    try:
        # Access the performance monitoring service
        performance_monitor = getattr(current_app, 'performance_monitor', None)
        
        if not performance_monitor:
            return jsonify({
                'error': 'Performance monitoring service not available',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Get current metrics
        current_metrics = performance_monitor.collect_current_metrics()
        
        return jsonify({
            'status': 'success',
            'data': current_metrics,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get performance metrics: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@monitoring_bp.route('/performance/summary', methods=['GET'])
@require_admin
def get_performance_summary():
    """Get performance summary and health status."""
    try:
        performance_monitor = getattr(current_app, 'performance_monitor', None)
        
        if not performance_monitor:
            return jsonify({
                'error': 'Performance monitoring service not available',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Get performance summary
        summary = performance_monitor.get_performance_summary()
        
        return jsonify({
            'status': 'success',
            'data': summary,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get performance summary: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@monitoring_bp.route('/performance/history', methods=['GET'])
@require_admin
def get_performance_history():
    """Get performance metrics history."""
    try:
        # Get hours parameter from query string
        hours = request.args.get('hours', 1, type=int)
        if hours > 24:
            hours = 24  # Limit to 24 hours max
        
        performance_monitor = getattr(current_app, 'performance_monitor', None)
        
        if not performance_monitor:
            return jsonify({
                'error': 'Performance monitoring service not available',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Get metrics history
        history = performance_monitor.get_metrics_history(hours=hours)
        
        return jsonify({
            'status': 'success',
            'data': history,
            'hours_requested': hours,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get performance history: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@monitoring_bp.route('/performance/alerts', methods=['GET'])
@require_admin
def get_performance_alerts():
    """Get current performance alerts."""
    try:
        # Get include_resolved parameter from query string
        include_resolved = request.args.get('include_resolved', False, type=bool)
        
        performance_monitor = getattr(current_app, 'performance_monitor', None)
        
        if not performance_monitor:
            return jsonify({
                'error': 'Performance monitoring service not available',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Get alerts
        alerts = performance_monitor.get_alerts(include_resolved=include_resolved)
        
        return jsonify({
            'status': 'success',
            'data': {
                'alerts': alerts,
                'total_count': len(alerts),
                'include_resolved': include_resolved
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get performance alerts: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@monitoring_bp.route('/cache/metrics', methods=['GET'])
@require_admin  
def get_cache_metrics():
    """Get enhanced cache service metrics."""
    try:
        enhanced_cache = getattr(current_app, 'enhanced_cache', None)
        
        if not enhanced_cache:
            return jsonify({
                'error': 'Enhanced cache service not available',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Get cache metrics
        if hasattr(enhanced_cache, 'get_metrics'):
            metrics = enhanced_cache.get_metrics()
        else:
            metrics = {
                'hit_rate': 0.0,
                'miss_rate': 0.0,
                'total_requests': 0,
                'cache_size': 0,
                'status': 'metrics_not_available'
            }
        
        return jsonify({
            'status': 'success',
            'data': metrics,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get cache metrics: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# ========== Enhanced Monitoring Endpoints ==========

@monitoring_bp.route('/status', methods=['GET'])
def get_monitoring_status():
    """Get basic monitoring status (public endpoint)."""
    try:
        # Get basic system status without requiring authentication
        performance_monitor = getattr(current_app, 'performance_monitor', None)
        enhanced_cache = getattr(current_app, 'enhanced_cache', None)
        
        status_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'monitoring': 'active',
                'analytics': 'active',
                'tracking': 'active',
                'performance_monitoring': 'active' if performance_monitor else 'unavailable',
                'enhanced_cache': 'active' if enhanced_cache else 'unavailable'
            },
            'uptime': 'available',
            'optimizations': {
                'performance_monitoring': bool(performance_monitor),
                'enhanced_caching': bool(enhanced_cache),
                'batch_processing': True  # Batch API is always available
            }
        }
        
        return jsonify(status_data), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Monitoring status unavailable',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@monitoring_bp.route('/health/comprehensive', methods=['GET'])
@require_admin
def get_comprehensive_health():
    """Get comprehensive system health report with real-time analysis."""
    try:
        # Get performance monitoring data if available
        performance_data = None
        performance_monitor = getattr(current_app, 'performance_monitor', None)
        
        if performance_monitor:
            performance_data = performance_monitor.get_performance_summary()
        
        # Get cache metrics if available
        cache_data = None
        enhanced_cache = getattr(current_app, 'enhanced_cache', None)
        
        if enhanced_cache and hasattr(enhanced_cache, 'get_metrics'):
            cache_data = enhanced_cache.get_metrics()
        
        # Get analytics health check
        health_report = analytics_service.perform_comprehensive_health_check()
        
        # Combine all health data
        comprehensive_health = {
            'overall_status': health_report.get('status', 'unknown'),
            'timestamp': datetime.utcnow().isoformat(),
            'analytics': health_report,
            'performance': performance_data,
            'cache': cache_data,
            'optimization_status': {
                'performance_monitoring_enabled': bool(performance_monitor),
                'enhanced_caching_enabled': bool(enhanced_cache),
                'batch_processing_enabled': True
            }
        }
        
        return jsonify({
            'status': 'success',
            'data': comprehensive_health,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
        # Track admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='comprehensive_health_check',
            user_id=str(get_current_user().id) if get_current_user() else None
        )
        
        return jsonify({
            'success': True,
            'health_report': health_report,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        analytics_service.track_error(e, endpoint='/monitoring/health/comprehensive', method='GET')
        return jsonify({
            'success': False,
            'error': 'Failed to get comprehensive health report'
        }), 500

@monitoring_bp.route('/dashboard/enhanced', methods=['GET'])
@require_admin
def get_enhanced_dashboard():
    """Get enhanced monitoring dashboard with all comprehensive metrics."""
    try:
        hours = request.args.get('hours', 24, type=int)
        dashboard_data = analytics_service.get_monitoring_dashboard_data(hours)
        
        # Track admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='view_enhanced_dashboard',
            user_id=str(get_current_user().id) if get_current_user() else None,
            metadata={'hours': hours}
        )
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        }), 200
        
    except Exception as e:
        analytics_service.track_error(e, endpoint='/monitoring/dashboard/enhanced', method='GET')
        return jsonify({
            'success': False,
            'error': 'Failed to get enhanced dashboard'
        }), 500

@monitoring_bp.route('/metrics', methods=['GET'])
def get_basic_metrics():
    """Get basic system metrics (public endpoint for health checks)."""
    try:
        # Collect basic system metrics without requiring admin access
        metrics = analytics_service.collect_system_metrics()
        
        # Return simplified metrics for external monitoring
        return jsonify({
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {
                'cpu_usage': metrics.get('cpu_usage', 0),
                'memory_usage': metrics.get('memory_usage', 0),
                'active_connections': metrics.get('database', {}).get('active_connections', 0),
                'response_time_avg': metrics.get('response_time_avg', 0),
                'status': 'healthy' if metrics.get('cpu_usage', 0) < 80 else 'warning'
            }
        }), 200
        
    except Exception as e:
        analytics_service.track_error(e, endpoint='/monitoring/metrics', method='GET')
        return jsonify({
            'success': False,
            'error': 'Failed to get metrics',
            'status': 'error'
        }), 500

@monitoring_bp.route('/metrics/real-time', methods=['GET'])
@require_admin
def get_real_time_metrics():
    """Get real-time system metrics with enhanced monitoring."""
    try:
        # Get fresh metrics
        metrics = analytics_service.collect_system_metrics()
        
        # Analyze for immediate alerts
        alerts = analytics_service._analyze_metrics_for_alerts(metrics)
        
        # Calculate health score
        health_score = analytics_service._calculate_health_score(metrics)
        
        # Get recommendations
        recommendations = analytics_service._generate_recommendations(metrics, alerts)
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'health_score': health_score,
            'alerts': alerts,
            'recommendations': recommendations,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        analytics_service.track_error(e, endpoint='/monitoring/metrics/real-time', method='GET')
        return jsonify({
            'success': False,
            'error': 'Failed to get real-time metrics'
        }), 500

# ========== Performance Analytics Endpoints ==========

@monitoring_bp.route('/performance/metrics', methods=['GET'])
@require_admin
def get_performance_metrics():
    """Get current system performance metrics."""
    try:
        # Collect current system metrics
        metrics = analytics_service.collect_system_metrics()
        
        # Track admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='view_performance_metrics',
            user_id=str(get_current_user().id) if get_current_user() else None
        )
        
        return jsonify({
            'success': True,
            'metrics': metrics
        }), 200
        
    except Exception as e:
        analytics_service.track_error(e, endpoint='/monitoring/performance/metrics', method='GET')
        return jsonify({
            'success': False,
            'error': 'Failed to get performance metrics'
        }), 500

@monitoring_bp.route('/performance/trends/<metric_type>', methods=['GET'])
@require_admin
def get_performance_trends(metric_type: str):
    """Get performance trends for a specific metric type."""
    try:
        hours = request.args.get('hours', 24, type=int)
        trends = analytics_service.get_performance_trends(metric_type, hours)
        
        # Track admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='view_performance_trends',
            user_id=str(get_current_user().id) if get_current_user() else None,
            metadata={'metric_type': metric_type, 'hours': hours}
        )
        
        return jsonify({
            'success': True,
            'metric_type': metric_type,
            'hours': hours,
            'trends': trends
        }), 200
        
    except Exception as e:
        analytics_service.track_error(e, endpoint=f'/monitoring/performance/trends/{metric_type}', method='GET')
        return jsonify({
            'success': False,
            'error': 'Failed to get performance trends'
        }), 500

@monitoring_bp.route('/performance/dashboard', methods=['GET'])
@require_admin
def get_performance_dashboard():
    """Get comprehensive performance dashboard data."""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        # Get current metrics
        current_metrics = analytics_service.collect_system_metrics()
        
        # Get trends for key metrics
        cpu_trends = analytics_service.get_performance_trends('cpu', hours)
        memory_trends = analytics_service.get_performance_trends('memory', hours)
        database_trends = analytics_service.get_performance_trends('database', hours)
        queue_trends = analytics_service.get_performance_trends('queue', hours)
        
        # Get recent performance alerts
        recent_alerts = SystemAlert.query.filter(
            SystemAlert.alert_type == 'performance',
            SystemAlert.triggered_at >= datetime.utcnow() - timedelta(hours=hours)
        ).order_by(SystemAlert.triggered_at.desc()).limit(10).all()
        
        dashboard_data = {
            'current_metrics': current_metrics,
            'trends': {
                'cpu': cpu_trends,
                'memory': memory_trends,
                'database': database_trends,
                'queue': queue_trends
            },
            'recent_alerts': [alert.to_dict() for alert in recent_alerts],
            'period_hours': hours,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Track admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='view_performance_dashboard',
            user_id=str(get_current_user().id) if get_current_user() else None
        )
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        }), 200
        
    except Exception as e:
        analytics_service.track_error(e, endpoint='/monitoring/performance/dashboard', method='GET')
        return jsonify({
            'success': False,
            'error': 'Failed to get performance dashboard'
        }), 500

# ========== Usage Insights Endpoints ==========

@monitoring_bp.route('/usage/insights', methods=['GET'])
@require_admin
def get_usage_insights():
    """Get comprehensive user behavior insights."""
    try:
        days = request.args.get('days', 30, type=int)
        insights = analytics_service.get_user_behavior_insights(days)
        
        # Track admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='view_usage_insights',
            user_id=str(get_current_user().id) if get_current_user() else None,
            metadata={'days': days}
        )
        
        return jsonify({
            'success': True,
            'insights': insights
        }), 200
        
    except Exception as e:
        analytics_service.track_error(e, endpoint='/monitoring/usage/insights', method='GET')
        return jsonify({
            'success': False,
            'error': 'Failed to get usage insights'
        }), 500

@monitoring_bp.route('/usage/activity', methods=['GET'])
@require_admin
def get_user_activity():
    """Get recent user activity data."""
    try:
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        activities = UsageInsight.query.filter(
            UsageInsight.timestamp >= start_time
        ).order_by(UsageInsight.timestamp.desc()).limit(limit).all()
        
        # Track admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='view_user_activity',
            user_id=str(get_current_user().id) if get_current_user() else None
        )
        
        return jsonify({
            'success': True,
            'activities': [activity.to_dict() for activity in activities],
            'period_hours': hours,
            'total_activities': len(activities)
        }), 200
        
    except Exception as e:
        analytics_service.track_error(e, endpoint='/monitoring/usage/activity', method='GET')
        return jsonify({
            'success': False,
            'error': 'Failed to get user activity'
        }), 500

@monitoring_bp.route('/usage/patterns', methods=['GET'])
@require_admin
def get_usage_patterns():
    """Get detailed usage patterns and analytics."""
    try:
        days = request.args.get('days', 7, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Activity by time of day
        from sqlalchemy import func
        hourly_activity = db.session.query(
            func.extract('hour', UsageInsight.timestamp).label('hour'),
            func.count().label('count')
        ).filter(
            UsageInsight.timestamp >= start_date
        ).group_by('hour').all()
        
        # Activity by day of week
        daily_activity = db.session.query(
            func.extract('dow', UsageInsight.timestamp).label('day_of_week'),
            func.count().label('count')
        ).filter(
            UsageInsight.timestamp >= start_date
        ).group_by('day_of_week').all()
        
        # Most active users
        top_users = db.session.query(
            UsageInsight.user_id,
            func.count().label('activity_count')
        ).filter(
            UsageInsight.timestamp >= start_date,
            UsageInsight.user_id.isnot(None)
        ).group_by(UsageInsight.user_id).order_by(func.count().desc()).limit(10).all()
        
        # Popular actions
        popular_actions = db.session.query(
            UsageInsight.event_action,
            func.count().label('count')
        ).filter(
            UsageInsight.timestamp >= start_date
        ).group_by(UsageInsight.event_action).order_by(func.count().desc()).limit(10).all()
        
        patterns_data = {
            'hourly_activity': [{'hour': int(hour), 'count': count} for hour, count in hourly_activity],
            'daily_activity': [{'day_of_week': int(dow), 'count': count} for dow, count in daily_activity],
            'top_users': [{'user_id': str(user_id), 'activity_count': count} for user_id, count in top_users],
            'popular_actions': [{'action': action, 'count': count} for action, count in popular_actions],
            'period_days': days,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Track admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='view_usage_patterns',
            user_id=str(get_current_user().id) if get_current_user() else None
        )
        
        return jsonify({
            'success': True,
            'patterns': patterns_data
        }), 200
        
    except Exception as e:
        analytics_service.track_error(e, endpoint='/monitoring/usage/patterns', method='GET')
        return jsonify({
            'success': False,
            'error': 'Failed to get usage patterns'
        }), 500

# ========== Error Tracking Endpoints ==========

@monitoring_bp.route('/errors/dashboard', methods=['GET'])
@require_admin
def get_error_dashboard():
    """Get comprehensive error tracking dashboard."""
    try:
        days = request.args.get('days', 7, type=int)
        dashboard_data = analytics_service.get_error_dashboard(days)
        
        # Track admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='view_error_dashboard',
            user_id=str(get_current_user().id) if get_current_user() else None
        )
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        }), 200
        
    except Exception as e:
        analytics_service.track_error(e, endpoint='/monitoring/errors/dashboard', method='GET')
        return jsonify({
            'success': False,
            'error': 'Failed to get error dashboard'
        }), 500

@monitoring_bp.route('/errors/list', methods=['GET'])
@require_admin
def get_error_list():
    """Get paginated list of errors with filtering."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        severity = request.args.get('severity')
        category = request.args.get('category')
        status = request.args.get('status')
        
        query = ErrorTracking.query
        
        # Apply filters
        if severity:
            query = query.filter(ErrorTracking.severity == severity)
        if category:
            query = query.filter(ErrorTracking.category == category)
        if status:
            query = query.filter(ErrorTracking.status == status)
        
        # Order by last seen descending
        query = query.order_by(ErrorTracking.last_seen.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Track admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='view_error_list',
            user_id=str(get_current_user().id) if get_current_user() else None
        )
        
        return jsonify({
            'success': True,
            'errors': [error.to_dict() for error in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        }), 200
        
    except Exception as e:
        analytics_service.track_error(e, endpoint='/monitoring/errors/list', method='GET')
        return jsonify({
            'success': False,
            'error': 'Failed to get error list'
        }), 500

@monitoring_bp.route('/errors/<error_id>/resolve', methods=['POST'])
@require_admin
def resolve_error(error_id: str):
    """Mark an error as resolved."""
    try:
        error_tracking = ErrorTracking.query.get(error_id)
        if not error_tracking:
            return jsonify({
                'success': False,
                'error': 'Error not found'
            }), 404
        
        data = request.get_json() or {}
        resolution_notes = data.get('resolution_notes', '')
        
        error_tracking.status = 'resolved'
        error_tracking.resolved_at = datetime.utcnow()
        error_tracking.resolved_by = get_current_user().admin_profile.id
        error_tracking.resolution_notes = resolution_notes
        
        db.session.commit()
        
        # Track admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='resolve_error',
            user_id=str(get_current_user().id),
            resource_type='error',
            resource_id=error_id
        )
        
        return jsonify({
            'success': True,
            'message': 'Error marked as resolved'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        analytics_service.track_error(e, endpoint=f'/monitoring/errors/{error_id}/resolve', method='POST')
        return jsonify({
            'success': False,
            'error': 'Failed to resolve error'
        }), 500

# ========== System Alerts Endpoints ==========

@monitoring_bp.route('/alerts', methods=['GET'])
@require_admin
def get_system_alerts():
    """Get system alerts with filtering."""
    try:
        status = request.args.get('status', 'active')
        alert_type = request.args.get('alert_type')
        alert_level = request.args.get('alert_level')
        limit = request.args.get('limit', 50, type=int)
        
        query = SystemAlert.query
        
        # Apply filters
        if status:
            query = query.filter(SystemAlert.status == status)
        if alert_type:
            query = query.filter(SystemAlert.alert_type == alert_type)
        if alert_level:
            query = query.filter(SystemAlert.alert_level == alert_level)
        
        # Order by trigger time descending
        alerts = query.order_by(SystemAlert.triggered_at.desc()).limit(limit).all()
        
        # Track admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='view_system_alerts',
            user_id=str(get_current_user().id) if get_current_user() else None
        )
        
        return jsonify({
            'success': True,
            'alerts': [alert.to_dict() for alert in alerts],
            'filters': {
                'status': status,
                'alert_type': alert_type,
                'alert_level': alert_level,
                'limit': limit
            }
        }), 200
        
    except Exception as e:
        analytics_service.track_error(e, endpoint='/monitoring/alerts', method='GET')
        return jsonify({
            'success': False,
            'error': 'Failed to get system alerts'
        }), 500

@monitoring_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
@require_admin
def acknowledge_alert(alert_id: str):
    """Acknowledge a system alert."""
    try:
        admin_user = get_current_user()
        success = analytics_service.acknowledge_alert(alert_id, str(admin_user.admin_profile.id))
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Alert not found or already acknowledged'
            }), 404
        
        # Track admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='acknowledge_alert',
            user_id=str(admin_user.id),
            resource_type='alert',
            resource_id=alert_id
        )
        
        return jsonify({
            'success': True,
            'message': 'Alert acknowledged'
        }), 200
        
    except Exception as e:
        analytics_service.track_error(e, endpoint=f'/monitoring/alerts/{alert_id}/acknowledge', method='POST')
        return jsonify({
            'success': False,
            'error': 'Failed to acknowledge alert'
        }), 500

# ========== Comprehensive Monitoring Dashboard ==========

@monitoring_bp.route('/dashboard', methods=['GET'])
@require_admin
def get_monitoring_dashboard():
    """Get comprehensive monitoring dashboard with all key metrics."""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        # Performance metrics
        performance_metrics = analytics_service.collect_system_metrics()
        
        # Usage insights (shorter period for dashboard)
        usage_insights = analytics_service.get_user_behavior_insights(days=7)
        
        # Error dashboard
        error_dashboard = analytics_service.get_error_dashboard(days=7)
        
        # Active alerts (use SystemAlert model to avoid missing service method)
        active_alerts = [
            alert.to_dict() for alert in SystemAlert.query
                .filter_by(status='active')
                .order_by(SystemAlert.triggered_at.desc())
                .limit(50)
                .all()
        ]
        
        # Recent performance trends
        cpu_trends = analytics_service.get_performance_trends('cpu', hours)
        memory_trends = analytics_service.get_performance_trends('memory', hours)
        
        dashboard_data = {
            'performance': performance_metrics,
            'usage_insights': usage_insights,
            'error_tracking': error_dashboard,
            'active_alerts': active_alerts,
            'performance_trends': {
                'cpu': cpu_trends[-20:] if cpu_trends else [],  # Last 20 data points
                'memory': memory_trends[-20:] if memory_trends else []
            },
            'summary': {
                'total_alerts': len(active_alerts),
                'critical_alerts': len([a for a in active_alerts if a.get('alert_level') == 'critical']),
                'system_health': 'healthy' if len(active_alerts) == 0 else 'warning',
                'error_rate': error_dashboard.get('summary', {}).get('total_errors', 0) if isinstance(error_dashboard, dict) else 0
            },
            'generated_at': datetime.utcnow().isoformat(),
            'period_hours': hours
        }
        
        # Track admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='view_monitoring_dashboard',
            user_id=str(get_current_user().id) if get_current_user() else None
        )
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        }), 200
        
    except Exception as e:
        analytics_service.track_error(e, endpoint='/monitoring/dashboard', method='GET')
        return jsonify({
            'success': False,
            'error': 'Failed to get monitoring dashboard'
        }), 500

# ========== Data Export Endpoints ==========

@monitoring_bp.route('/export/metrics', methods=['GET'])
@require_admin
def export_metrics():
    """Export performance metrics as CSV."""
    try:
        days = request.args.get('days', 7, type=int)
        metric_type = request.args.get('metric_type')
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = PerformanceMetric.query.filter(
            PerformanceMetric.timestamp >= start_date
        )
        
        if metric_type:
            query = query.filter(PerformanceMetric.metric_type == metric_type)
        
        metrics = query.order_by(PerformanceMetric.timestamp).all()
        
        # Generate CSV content
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'timestamp', 'metric_type', 'metric_name', 'category',
            'value', 'unit', 'status', 'threshold_warning', 'threshold_critical'
        ])
        
        # Write data
        for metric in metrics:
            writer.writerow([
                metric.timestamp.isoformat(),
                metric.metric_type,
                metric.metric_name,
                metric.category,
                metric.value,
                metric.unit or '',
                metric.status,
                metric.threshold_warning or '',
                metric.threshold_critical or ''
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        # Track admin action
        analytics_service.track_user_action(
            event_type='admin_action',
            event_category='monitoring',
            event_action='export_metrics',
            user_id=str(get_current_user().id) if get_current_user() else None,
            metadata={'days': days, 'metric_type': metric_type}
        )
        
        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=metrics_{days}days.csv'}
        )
        
    except Exception as e:
        analytics_service.track_error(e, endpoint='/monitoring/export/metrics', method='GET')
        return jsonify({
            'success': False,
            'error': 'Failed to export metrics'
        }), 500

# ========== Health Check for Monitoring System ==========

@monitoring_bp.route('/health', methods=['GET'])
def monitoring_health():
    """Health check for monitoring system itself."""
    try:
        # Check if we can record a metric
        test_metric = analytics_service.record_performance_metric(
            'test', 'health_check', 'monitoring', 1.0, 'test'
        )
        
        # Check if we can track an action
        analytics_service.track_user_action(
            'health_check', 'monitoring', 'system_health_check'
        )
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'message': 'Monitoring system is operational',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503
