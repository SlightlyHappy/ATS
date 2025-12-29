"""
Batch API Processing Module
Implements Phase 1 optimization: Frontend Loading Optimization
Creates batch endpoints to reduce sequential API calls and improve dashboard performance.
"""
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from sqlalchemy import text, and_, func, desc
from typing import Dict, Any, List, Optional
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app import db, cache
from app.models import User, Resume, Analysis, AnalysisQueue
from app.models.user import CreditTransaction
from app.models.queue import QueueStatus
from app.services.auth_manager import require_admin, get_current_user
from app.services.error_handler import ApplicationError

logger = logging.getLogger(__name__)
batch_bp = Blueprint('batch', __name__, url_prefix='/api/v1/batch')

# =============================================================================
# BATCH DASHBOARD ENDPOINT - PHASE 1 OPTIMIZATION
# =============================================================================

@batch_bp.route('/admin/dashboard', methods=['GET'])
@cache.cached(timeout=300, key_prefix='batch_admin_dashboard')  # 5-minute cache
@require_admin
def get_dashboard_batch():
    """
    Optimized single endpoint for admin dashboard data.
    Replaces multiple sequential API calls with one batch request.
    Implements parallel data fetching and query optimization.
    """
    try:
        # Get request parameters
        timeframe = request.args.get('timeframe', '7d')
        include_trends = request.args.get('include_trends', 'true').lower() == 'true'
        include_activity = request.args.get('include_activity', 'true').lower() == 'true'
        
        # Parse timeframe
        if timeframe == '24h':
            start_date = datetime.utcnow() - timedelta(hours=24)
        elif timeframe == '7d':
            start_date = datetime.utcnow() - timedelta(days=7)
        elif timeframe == '30d':
            start_date = datetime.utcnow() - timedelta(days=30)
        else:
            start_date = datetime.utcnow() - timedelta(days=7)  # Default to 7 days
        
        # Use ThreadPoolExecutor for parallel data fetching
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all database queries in parallel
            future_stats = executor.submit(_get_dashboard_stats, start_date)
            future_queue = executor.submit(_get_queue_stats)
            future_credits = executor.submit(_get_credit_stats, start_date)
            future_performance = executor.submit(_get_performance_stats)
            
            # Conditionally fetch additional data
            future_trends = None
            future_activity = None
            if include_trends:
                future_trends = executor.submit(_get_trend_data, start_date)
            if include_activity:
                future_activity = executor.submit(_get_recent_activity)
            
            # Collect results
            dashboard_stats = future_stats.result()
            queue_stats = future_queue.result()
            credit_stats = future_credits.result()
            performance_stats = future_performance.result()
            
            trend_data = future_trends.result() if future_trends else None
            activity_data = future_activity.result() if future_activity else None
        
        # Compile response
        response_data = {
            'success': True,
            'data': {
                'summary': dashboard_stats,
                'queue_health': queue_stats,
                'credit_analytics': credit_stats,
                'performance': performance_stats,
                'metadata': {
                    'timeframe': timeframe,
                    'generated_at': datetime.utcnow().isoformat(),
                    'cache_status': 'fresh',
                    'response_time': 'optimized_batch'
                }
            },
            'cached': True,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Add optional data if requested
        if trend_data:
            response_data['data']['trends'] = trend_data
        if activity_data:
            response_data['data']['recent_activity'] = activity_data
        
        # Log batch request for monitoring
        logger.info(f"Batch dashboard request served for admin: {get_current_user().email}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error in batch dashboard endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load dashboard data',
            'message': str(e)
        }), 500


def _get_dashboard_stats(start_date: datetime) -> Dict[str, Any]:
    """Get core dashboard statistics with optimized query."""
    try:
        # Single optimized query for all user stats
        result = db.session.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM users WHERE created_at >= :start_date) as new_users,
                (SELECT COUNT(*) FROM users WHERE is_admin = true) as admin_users,
                (SELECT COUNT(*) FROM users WHERE last_login >= :start_date) as active_users,
                (SELECT COUNT(*) FROM resumes) as total_resumes,
                (SELECT COUNT(*) FROM resumes WHERE created_at >= :start_date) as new_resumes,
                (SELECT COUNT(*) FROM analyses) as total_analyses,
                (SELECT COUNT(*) FROM analyses WHERE status = 'completed') as completed_analyses,
                (SELECT AVG(processing_time) FROM analyses WHERE status = 'completed' AND processing_time IS NOT NULL) as avg_processing_time
        """), {'start_date': start_date}).fetchone()
        
        return dict(result._mapping) if result else {}
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        return {}


def _get_queue_stats() -> Dict[str, Any]:
    """Get queue health and status information."""
    try:
        result = db.session.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM analysis_queue WHERE status = 'pending') as pending_count,
                (SELECT COUNT(*) FROM analysis_queue WHERE status = 'processing') as processing_count,
                (SELECT COUNT(*) FROM analysis_queue WHERE status = 'failed') as failed_count,
                (SELECT COUNT(*) FROM analysis_queue WHERE status = 'completed') as completed_count,
                (SELECT AVG(EXTRACT(epoch FROM (completed_at - started_at))) 
                 FROM analysis_queue 
                 WHERE status = 'completed' AND completed_at IS NOT NULL AND started_at IS NOT NULL
                 AND completed_at >= NOW() - INTERVAL '24 hours') as avg_processing_time_24h
        """)).fetchone()
        
        stats = dict(result._mapping) if result else {}
        
        # Calculate queue health status
        pending = stats.get('pending_count', 0)
        failed = stats.get('failed_count', 0)
        processing_time = stats.get('avg_processing_time_24h', 0)
        
        if pending > 20 or failed > 5 or (processing_time and processing_time > 300):
            health_status = 'warning'
        elif pending > 50 or failed > 10 or (processing_time and processing_time > 600):
            health_status = 'critical'
        else:
            health_status = 'healthy'
        
        stats['health_status'] = health_status
        return stats
        
    except Exception as e:
        logger.error(f"Error getting queue stats: {str(e)}")
        return {'health_status': 'unknown'}


def _get_credit_stats(start_date: datetime) -> Dict[str, Any]:
    """Get credit system analytics."""
    try:
        result = db.session.execute(text("""
            SELECT 
                (SELECT SUM(amount) FROM credit_transactions WHERE transaction_type = 'credit') as total_credits_issued,
                (SELECT SUM(amount) FROM credit_transactions WHERE transaction_type = 'debit') as total_credits_used,
                (SELECT SUM(amount) FROM credit_transactions WHERE transaction_type = 'credit' AND created_at >= :start_date) as recent_credits_issued,
                (SELECT SUM(amount) FROM credit_transactions WHERE transaction_type = 'debit' AND created_at >= :start_date) as recent_credits_used,
                (SELECT AVG(credits_balance) FROM users) as avg_user_balance,
                (SELECT COUNT(*) FROM users WHERE credits_balance <= 5) as low_balance_users
        """), {'start_date': start_date}).fetchone()
        
        stats = dict(result._mapping) if result else {}
        
        # Calculate credit health metrics
        total_issued = stats.get('total_credits_issued', 0) or 0
        total_used = stats.get('total_credits_used', 0) or 0
        stats['credits_remaining'] = total_issued - total_used
        stats['utilization_rate'] = (total_used / total_issued * 100) if total_issued > 0 else 0
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting credit stats: {str(e)}")
        return {}


def _get_performance_stats() -> Dict[str, Any]:
    """Get system performance metrics."""
    try:
        # Get database connection pool status
        engine = db.engine
        pool = engine.pool
        
        performance_stats = {
            'database': {
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'pool_health': 'healthy' if pool.checkedin() > 0 else 'warning'
            },
            'cache': {
                'cache_type': current_app.config.get('CACHE_TYPE', 'simple'),
                'cache_enabled': bool(current_app.config.get('CACHE_DEFAULT_TIMEOUT', 0))
            },
            'api': {
                'optimization_level': 'batch_processing_enabled',
                'parallel_queries': True,
                'caching_enabled': True
            }
        }
        
        return performance_stats
        
    except Exception as e:
        logger.error(f"Error getting performance stats: {str(e)}")
        return {'status': 'unknown'}


def _get_trend_data(start_date: datetime) -> Dict[str, Any]:
    """Get trend data for charts and analytics."""
    try:
        # Get daily statistics for the requested period
        days_back = (datetime.utcnow() - start_date).days
        
        result = db.session.execute(text("""
            WITH date_series AS (
                SELECT generate_series(
                    CURRENT_DATE - INTERVAL '%s days',
                    CURRENT_DATE,
                    '1 day'::interval
                )::date as date
            ),
            daily_stats AS (
                SELECT 
                    d.date,
                    COALESCE(u.new_users, 0) as new_users,
                    COALESCE(r.new_resumes, 0) as new_resumes,
                    COALESCE(a.completed_analyses, 0) as completed_analyses
                FROM date_series d
                LEFT JOIN (
                    SELECT DATE(created_at) as date, COUNT(*) as new_users
                    FROM users 
                    WHERE created_at >= :start_date
                    GROUP BY DATE(created_at)
                ) u ON d.date = u.date
                LEFT JOIN (
                    SELECT DATE(created_at) as date, COUNT(*) as new_resumes
                    FROM resumes 
                    WHERE created_at >= :start_date
                    GROUP BY DATE(created_at)
                ) r ON d.date = r.date
                LEFT JOIN (
                    SELECT DATE(completed_at) as date, COUNT(*) as completed_analyses
                    FROM analysis_queue 
                    WHERE status = 'completed' AND completed_at >= :start_date
                    GROUP BY DATE(completed_at)
                ) a ON d.date = a.date
                ORDER BY d.date
            )
            SELECT * FROM daily_stats
        """ % days_back), {'start_date': start_date}).fetchall()
        
        trend_data = [
            {
                'date': row.date.strftime('%Y-%m-%d'),
                'new_users': row.new_users,
                'new_resumes': row.new_resumes,
                'completed_analyses': row.completed_analyses
            }
            for row in result
        ]
        
        return {'daily_trends': trend_data}
        
    except Exception as e:
        logger.error(f"Error getting trend data: {str(e)}")
        return {}


def _get_recent_activity() -> Dict[str, Any]:
    """Get recent user and system activity."""
    try:
        # Get recent users
        recent_users = db.session.query(User).order_by(desc(User.created_at)).limit(5).all()
        
        # Get recent completed analyses
        recent_analyses = db.session.query(AnalysisQueue).filter_by(
            status=QueueStatus.COMPLETED.value
        ).order_by(desc(AnalysisQueue.completed_at)).limit(5).all()
        
        activity_data = {
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
        }
        
        return activity_data
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {str(e)}")
        return {}


# =============================================================================
# BATCH USER DATA ENDPOINT
# =============================================================================

@batch_bp.route('/admin/users', methods=['GET'])
@cache.cached(timeout=300, key_prefix='batch_admin_users', query_string=True)
@require_admin
def get_users_batch():
    """
    Optimized batch endpoint for user data with pagination and filtering.
    Reduces database queries and improves admin user management performance.
    """
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)  # Optimized page size
        
        # Filtering parameters
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', 'all')  # all, active, inactive, admin
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build optimized query
        query = User.query
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                User.email.ilike(search_term) |
                User.first_name.ilike(search_term) |
                User.last_name.ilike(search_term)
            )
        
        if status_filter == 'active':
            query = query.filter(User.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(User.is_active == False)
        elif status_filter == 'admin':
            query = query.filter(User.is_admin == True)
        
        if date_from:
            query = query.filter(User.created_at >= datetime.fromisoformat(date_from))
        if date_to:
            query = query.filter(User.created_at <= datetime.fromisoformat(date_to))
        
        # Execute paginated query
        pagination = query.order_by(desc(User.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format user data
        users_data = []
        for user in pagination.items:
            user_data = {
                'id': str(user.id),
                'email': user.email,
                'name': f"{user.first_name} {user.last_name}",
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'credits_balance': user.credits_balance,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None
            }
            users_data.append(user_data)
        
        return jsonify({
            'success': True,
            'users': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            },
            'filters_applied': {
                'search': search,
                'status': status_filter,
                'date_from': date_from,
                'date_to': date_to
            },
            'metadata': {
                'cached': True,
                'optimized': True,
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in batch users endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load user data'
        }), 500


# =============================================================================
# BATCH ANALYTICS ENDPOINT
# =============================================================================

@batch_bp.route('/admin/analytics', methods=['GET'])
@cache.cached(timeout=600, key_prefix='batch_admin_analytics', query_string=True)  # 10-minute cache
@require_admin
def get_analytics_batch():
    """
    Comprehensive analytics endpoint that combines multiple analytics queries.
    Optimized for admin analytics dashboard performance.
    """
    try:
        timeframe = request.args.get('timeframe', '30d')
        include_detailed = request.args.get('detailed', 'false').lower() == 'true'
        
        # Parse timeframe
        if timeframe == '7d':
            start_date = datetime.utcnow() - timedelta(days=7)
        elif timeframe == '30d':
            start_date = datetime.utcnow() - timedelta(days=30)
        elif timeframe == '90d':
            start_date = datetime.utcnow() - timedelta(days=90)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        # Parallel analytics data fetching
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_user_analytics = executor.submit(_get_user_analytics, start_date)
            future_usage_analytics = executor.submit(_get_usage_analytics, start_date)
            future_performance_analytics = executor.submit(_get_performance_analytics)
            future_revenue_analytics = executor.submit(_get_revenue_analytics, start_date)
        
        # Collect results
        analytics_data = {
            'user_analytics': future_user_analytics.result(),
            'usage_analytics': future_usage_analytics.result(),
            'performance_analytics': future_performance_analytics.result(),
            'revenue_analytics': future_revenue_analytics.result(),
            'metadata': {
                'timeframe': timeframe,
                'generated_at': datetime.utcnow().isoformat(),
                'include_detailed': include_detailed,
                'cache_duration': 600
            }
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics_data,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in batch analytics endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load analytics data'
        }), 500


def _get_user_analytics(start_date: datetime) -> Dict[str, Any]:
    """Get user behavior and engagement analytics."""
    try:
        result = db.session.execute(text("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(CASE WHEN created_at >= :start_date THEN 1 END) as new_users,
                COUNT(CASE WHEN is_active = true THEN 1 END) as active_users,
                COUNT(CASE WHEN last_login >= :start_date THEN 1 END) as engaged_users,
                AVG(credits_balance) as avg_credits_balance,
                COUNT(CASE WHEN credits_balance > 0 THEN 1 END) as users_with_credits
        """), {'start_date': start_date}).fetchone()
        
        return dict(result._mapping) if result else {}
        
    except Exception as e:
        logger.error(f"Error getting user analytics: {str(e)}")
        return {}


def _get_usage_analytics(start_date: datetime) -> Dict[str, Any]:
    """Get system usage analytics."""
    try:
        result = db.session.execute(text("""
            SELECT 
                COUNT(*) as total_resumes,
                COUNT(CASE WHEN created_at >= :start_date THEN 1 END) as recent_resumes,
                (SELECT COUNT(*) FROM analyses WHERE status = 'completed') as completed_analyses,
                (SELECT COUNT(*) FROM analyses WHERE status = 'completed' AND created_at >= :start_date) as recent_analyses,
                (SELECT AVG(processing_time) FROM analyses WHERE status = 'completed' AND processing_time IS NOT NULL) as avg_processing_time
        """), {'start_date': start_date}).fetchone()
        
        return dict(result._mapping) if result else {}
        
    except Exception as e:
        logger.error(f"Error getting usage analytics: {str(e)}")
        return {}


def _get_performance_analytics() -> Dict[str, Any]:
    """Get system performance analytics."""
    try:
        # Get queue performance metrics
        queue_result = db.session.execute(text("""
            SELECT 
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_queue,
                COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_queue,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_queue,
                AVG(CASE WHEN status = 'completed' AND started_at IS NOT NULL AND completed_at IS NOT NULL 
                    THEN EXTRACT(epoch FROM (completed_at - started_at)) END) as avg_queue_time
            FROM analysis_queue
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)).fetchone()
        
        return dict(queue_result._mapping) if queue_result else {}
        
    except Exception as e:
        logger.error(f"Error getting performance analytics: {str(e)}")
        return {}


def _get_revenue_analytics(start_date: datetime) -> Dict[str, Any]:
    """Get revenue and credit analytics."""
    try:
        result = db.session.execute(text("""
            SELECT 
                SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE 0 END) as total_credits_purchased,
                SUM(CASE WHEN transaction_type = 'debit' THEN amount ELSE 0 END) as total_credits_consumed,
                SUM(CASE WHEN transaction_type = 'credit' AND created_at >= :start_date THEN amount ELSE 0 END) as recent_credits_purchased,
                SUM(CASE WHEN transaction_type = 'debit' AND created_at >= :start_date THEN amount ELSE 0 END) as recent_credits_consumed,
                COUNT(DISTINCT user_id) as paying_users
            FROM credit_transactions
        """), {'start_date': start_date}).fetchone()
        
        return dict(result._mapping) if result else {}
        
    except Exception as e:
        logger.error(f"Error getting revenue analytics: {str(e)}")
        return {}


# =============================================================================
# BATCH SYSTEM STATUS ENDPOINT
# =============================================================================

@batch_bp.route('/system/status', methods=['GET'])
@cache.cached(timeout=60, key_prefix='batch_system_status')  # 1-minute cache for real-time data
def get_system_status_batch():
    """
    Real-time system status endpoint for monitoring dashboard.
    Provides comprehensive system health in a single request.
    """
    try:
        # Get system metrics in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_db_status = executor.submit(_check_database_status)
            future_queue_status = executor.submit(_check_queue_status)
            future_cache_status = executor.submit(_check_cache_status)
        
        system_status = {
            'overall_status': 'healthy',
            'database': future_db_status.result(),
            'queue': future_queue_status.result(),
            'cache': future_cache_status.result(),
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': 'available',  # Could implement actual uptime tracking
            'version': '1.5-optimized'
        }
        
        # Determine overall status
        statuses = [
            system_status['database']['status'],
            system_status['queue']['status'],
            system_status['cache']['status']
        ]
        
        if 'critical' in statuses:
            system_status['overall_status'] = 'critical'
        elif 'warning' in statuses:
            system_status['overall_status'] = 'warning'
        else:
            system_status['overall_status'] = 'healthy'
        
        return jsonify({
            'success': True,
            'system_status': system_status
        }), 200
        
    except Exception as e:
        logger.error(f"Error in system status endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'system_status': {
                'overall_status': 'unknown',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 500


def _check_database_status() -> Dict[str, Any]:
    """Check database connectivity and pool status."""
    try:
        # Simple connectivity test
        db.session.execute(text('SELECT 1')).fetchone()
        
        # Get pool information
        engine = db.engine
        pool = engine.pool
        
        pool_stats = {
            'size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow()
        }
        
        # Determine status
        if pool_stats['checked_out'] / pool_stats['size'] > 0.8:
            status = 'warning'
        elif pool_stats['checked_out'] / pool_stats['size'] > 0.95:
            status = 'critical'
        else:
            status = 'healthy'
        
        return {
            'status': status,
            'connection': 'connected',
            'pool_stats': pool_stats
        }
        
    except Exception as e:
        return {
            'status': 'critical',
            'connection': 'failed',
            'error': str(e)
        }


def _check_queue_status() -> Dict[str, Any]:
    """Check queue system status."""
    try:
        result = db.session.execute(text("""
            SELECT 
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
            FROM analysis_queue
        """)).fetchone()
        
        stats = dict(result._mapping) if result else {}
        
        # Determine status
        pending = stats.get('pending', 0)
        failed = stats.get('failed', 0)
        
        if pending > 50 or failed > 10:
            status = 'critical'
        elif pending > 20 or failed > 5:
            status = 'warning'
        else:
            status = 'healthy'
        
        return {
            'status': status,
            'queue_stats': stats
        }
        
    except Exception as e:
        return {
            'status': 'critical',
            'error': str(e)
        }


def _check_cache_status() -> Dict[str, Any]:
    """Check cache system status."""
    try:
        cache_config = {
            'type': current_app.config.get('CACHE_TYPE', 'simple'),
            'timeout': current_app.config.get('CACHE_DEFAULT_TIMEOUT', 300)
        }
        
        # Simple cache test
        test_key = 'health_check_test'
        cache.set(test_key, 'test_value', timeout=60)
        retrieved = cache.get(test_key)
        cache.delete(test_key)
        
        if retrieved == 'test_value':
            status = 'healthy'
        else:
            status = 'warning'
        
        return {
            'status': status,
            'config': cache_config,
            'test_result': 'passed' if status == 'healthy' else 'failed'
        }
        
    except Exception as e:
        return {
            'status': 'critical',
            'error': str(e)
        }
