#!/usr/bin/env python3
"""
Performance Routes for HR ATS System
Provides API endpoints for performance monitoring and optimization
"""

from flask import Blueprint, request, jsonify, g
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from utils.performance_helpers import (
    performance_helper, get_performance_summary, PerformanceMetric
)
from utils.response_formatter import EnhancedResponseFormatter
from auth_middleware import require_admin, require_auth, get_current_user

logger = logging.getLogger(__name__)

# Global auth middleware instance (will be injected)
auth_middleware = None

# Create blueprint
performance_bp = Blueprint('performance', __name__, url_prefix='/api/v1/performance')

# Initialize response formatter
response_formatter = EnhancedResponseFormatter()

@performance_bp.route('/metrics', methods=['GET'])
@require_admin
def get_performance_metrics():
    """Get comprehensive performance metrics (admin only)"""
    try:
        summary = get_performance_summary()
        
        return response_formatter.success(
            data=summary,
            message="Performance metrics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return response_formatter.error(
            message="Failed to retrieve performance metrics",
            error_code="PERFORMANCE_METRICS_ERROR",
            details={'error': str(e)}
        ), 500

@performance_bp.route('/cache', methods=['GET'])
@require_admin
def get_cache_stats():
    """Get cache statistics (admin only)"""
    try:
        response_cache_stats = performance_helper.cache.get_stats()
        query_cache_stats = performance_helper.query_cache.get_stats()
        
        return response_formatter.success(
            data={
                'response_cache': response_cache_stats,
                'query_cache': query_cache_stats,
                'total_cache_entries': response_cache_stats['total_entries'] + query_cache_stats['total_entries'],
                'total_cache_size_mb': (response_cache_stats['total_size_bytes'] + query_cache_stats['total_size_bytes']) / (1024 * 1024),
                'timestamp': datetime.utcnow().isoformat()
            },
            message="Cache statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return response_formatter.error(
            message="Failed to retrieve cache statistics",
            error_code="CACHE_STATS_ERROR",
            details={'error': str(e)}
        ), 500

@performance_bp.route('/cache/clear', methods=['POST'])
@require_admin
def clear_cache():
    """Clear cache entries (admin only)"""
    try:
        data = request.get_json() or {}
        cache_type = data.get('cache_type', 'all')  # all, response, query
        pattern = data.get('pattern', '*')
        
        cleared_counts = {}
        
        if cache_type in ['all', 'response']:
            if pattern == '*':
                cleared_counts['response_cache'] = performance_helper.cache.clear()
            else:
                cleared_counts['response_cache'] = performance_helper.clear_cache_by_pattern(pattern)
        
        if cache_type in ['all', 'query']:
            if pattern == '*':
                cleared_counts['query_cache'] = performance_helper.query_cache.clear()
            else:
                # Pattern clearing for query cache
                cleared_counts['query_cache'] = 0  # Simplified for now
        
        total_cleared = sum(cleared_counts.values())
        
        return response_formatter.success(
            data={
                'cleared_counts': cleared_counts,
                'total_cleared': total_cleared,
                'cache_type': cache_type,
                'pattern': pattern
            },
            message=f"Cleared {total_cleared} cache entries"
        )
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return response_formatter.error(
            message="Failed to clear cache",
            error_code="CACHE_CLEAR_ERROR",
            details={'error': str(e)}
        ), 500

@performance_bp.route('/endpoints', methods=['GET'])
@require_admin
def get_endpoint_performance():
    """Get endpoint performance statistics (admin only)"""
    try:
        endpoint_filter = request.args.get('endpoint')
        sort_by = request.args.get('sort_by', 'average_response_time')
        limit = min(int(request.args.get('limit', 50)), 200)
        
        endpoint_stats = performance_helper.monitor.get_endpoint_stats(endpoint_filter)
        
        if endpoint_filter:
            # Return single endpoint stats
            return response_formatter.success(
                data={
                    'endpoint': endpoint_filter,
                    'stats': endpoint_stats
                },
                message="Endpoint statistics retrieved successfully"
            )
        else:
            # Return sorted list of endpoints
            sorted_endpoints = []
            for endpoint, stats in endpoint_stats.items():
                sorted_endpoints.append({
                    'endpoint': endpoint,
                    **stats
                })
            
            # Sort by specified field
            if sort_by in ['average_response_time', 'total_requests', 'error_count', 'cache_hit_rate']:
                sorted_endpoints.sort(
                    key=lambda x: x.get(sort_by, 0),
                    reverse=True
                )
            
            # Limit results
            sorted_endpoints = sorted_endpoints[:limit]
            
            return response_formatter.success(
                data={
                    'endpoints': sorted_endpoints,
                    'total_endpoints': len(endpoint_stats),
                    'sort_by': sort_by,
                    'limit': limit
                },
                message=f"Retrieved {len(sorted_endpoints)} endpoint statistics"
            )
        
    except Exception as e:
        logger.error(f"Error getting endpoint performance: {e}")
        return response_formatter.error(
            message="Failed to retrieve endpoint performance",
            error_code="ENDPOINT_PERFORMANCE_ERROR",
            details={'error': str(e)}
        ), 500

@performance_bp.route('/slow-requests', methods=['GET'])
@require_admin
def get_slow_requests():
    """Get slow requests above threshold (admin only)"""
    try:
        threshold_ms = float(request.args.get('threshold', 1000))
        limit = min(int(request.args.get('limit', 50)), 200)
        
        slow_requests = performance_helper.monitor.get_slow_requests(threshold_ms, limit)
        
        # Convert to serializable format
        slow_requests_data = []
        for metric in slow_requests:
            slow_requests_data.append({
                'endpoint': metric.endpoint,
                'method': metric.method,
                'response_time_ms': metric.response_time_ms,
                'status_code': metric.status_code,
                'timestamp': metric.timestamp.isoformat(),
                'user_id': metric.user_id,
                'request_size_bytes': metric.request_size_bytes,
                'response_size_bytes': metric.response_size_bytes,
                'cache_hit': metric.cache_hit,
                'error_message': metric.error_message
            })
        
        return response_formatter.success(
            data={
                'slow_requests': slow_requests_data,
                'threshold_ms': threshold_ms,
                'total_found': len(slow_requests_data)
            },
            message=f"Found {len(slow_requests_data)} slow requests"
        )
        
    except Exception as e:
        logger.error(f"Error getting slow requests: {e}")
        return response_formatter.error(
            message="Failed to retrieve slow requests",
            error_code="SLOW_REQUESTS_ERROR",
            details={'error': str(e)}
        ), 500

@performance_bp.route('/system', methods=['GET'])
@require_admin
def get_system_metrics():
    """Get system performance metrics (admin only)"""
    try:
        metrics = performance_helper.get_system_metrics()
        
        return response_formatter.success(
            data=metrics,
            message="System metrics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return response_formatter.error(
            message="Failed to retrieve system metrics",
            error_code="SYSTEM_METRICS_ERROR",
            details={'error': str(e)}
        ), 500

@performance_bp.route('/optimize', methods=['POST'])
@require_admin
def optimize_performance():
    """Run performance optimization (admin only)"""
    try:
        data = request.get_json() or {}
        optimization_type = data.get('type', 'cache')  # cache, database, memory
        
        optimization_results = {}
        
        if optimization_type in ['cache', 'all']:
            # Clear expired cache entries
            cache_cleared = performance_helper.cache.clear()
            query_cache_cleared = performance_helper.query_cache.clear()
            
            optimization_results['cache_optimization'] = {
                'response_cache_cleared': cache_cleared,
                'query_cache_cleared': query_cache_cleared,
                'total_cleared': cache_cleared + query_cache_cleared
            }
        
        if optimization_type in ['memory', 'all']:
            # Force garbage collection
            import gc
            collected = gc.collect()
            
            optimization_results['memory_optimization'] = {
                'garbage_collected': collected
            }
        
        if optimization_type in ['database', 'all']:
            # Database optimization would go here
            # For now, just clear query cache
            optimization_results['database_optimization'] = {
                'query_cache_cleared': performance_helper.query_cache.clear()
            }
        
        return response_formatter.success(
            data={
                'optimization_type': optimization_type,
                'results': optimization_results,
                'timestamp': datetime.utcnow().isoformat()
            },
            message="Performance optimization completed"
        )
        
    except Exception as e:
        logger.error(f"Error in performance optimization: {e}")
        return response_formatter.error(
            message="Failed to optimize performance",
            error_code="OPTIMIZATION_ERROR",
            details={'error': str(e)}
        ), 500

@performance_bp.route('/health', methods=['GET'])
@require_auth
def get_health_status():
    """Get application health status"""
    try:
        user = get_current_user()
        
        # Basic health checks
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': 0,  # Would be calculated from app start time
            'version': '1.0.0'  # Would come from config
        }
        
        # Add detailed metrics for admin users
        if user.get('is_admin'):
            system_metrics = performance_helper.get_system_metrics()
            cache_stats = performance_helper.cache.get_stats()
            
            # Determine health status based on metrics
            cpu_percent = system_metrics.get('system', {}).get('cpu_percent', 0)
            memory_percent = system_metrics.get('system', {}).get('memory_percent', 0)
            
            if cpu_percent > 90 or memory_percent > 90:
                health_status['status'] = 'critical'
            elif cpu_percent > 70 or memory_percent > 70:
                health_status['status'] = 'warning'
            
            health_status.update({
                'system_metrics': system_metrics,
                'cache_stats': cache_stats,
                'performance_summary': get_performance_summary()['summary']
            })
        
        return response_formatter.success(
            data=health_status,
            message="Health status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return response_formatter.error(
            message="Failed to retrieve health status",
            error_code="HEALTH_STATUS_ERROR",
            details={'error': str(e)}
        ), 500

@performance_bp.route('/warmup', methods=['POST'])
@require_admin
def warmup_cache():
    """Warm up cache with commonly accessed data (admin only)"""
    try:
        data = request.get_json() or {}
        cache_types = data.get('cache_types', ['resumes', 'users'])
        
        warmed_caches = []
        
        # Define cache warming functions
        def warm_resume_cache():
            # Cache recent resumes
            from railway_database import RailwayDatabase
            db = RailwayDatabase()
            recent_resumes = db.execute_read(
                "SELECT * FROM resumes ORDER BY upload_date DESC LIMIT 50"
            )
            for resume in recent_resumes:
                cache_key = f"resume:{resume['id']}"
                performance_helper.cache.set(cache_key, resume, ttl=600, tags=['resume'])
            return len(recent_resumes)
        
        def warm_user_cache():
            # Cache active users
            from railway_database import RailwayDatabase
            db = RailwayDatabase()
            active_users = db.execute_read(
                "SELECT id, email, first_name, last_name, role FROM users WHERE is_active = true LIMIT 100"
            )
            for user in active_users:
                cache_key = f"user:{user['id']}"
                performance_helper.cache.set(cache_key, user, ttl=300, tags=['user'])
            return len(active_users)
        
        # Warm up specified caches
        if 'resumes' in cache_types:
            try:
                count = warm_resume_cache()
                warmed_caches.append({'type': 'resumes', 'count': count})
            except Exception as e:
                logger.error(f"Error warming resume cache: {e}")
                warmed_caches.append({'type': 'resumes', 'error': str(e)})
        
        if 'users' in cache_types:
            try:
                count = warm_user_cache()
                warmed_caches.append({'type': 'users', 'count': count})
            except Exception as e:
                logger.error(f"Error warming user cache: {e}")
                warmed_caches.append({'type': 'users', 'error': str(e)})
        
        total_warmed = sum(cache.get('count', 0) for cache in warmed_caches)
        
        return response_formatter.success(
            data={
                'warmed_caches': warmed_caches,
                'total_entries_warmed': total_warmed,
                'cache_types': cache_types
            },
            message=f"Cache warmed with {total_warmed} entries"
        )
        
    except Exception as e:
        logger.error(f"Error warming cache: {e}")
        return response_formatter.error(
            message="Failed to warm cache",
            error_code="CACHE_WARMUP_ERROR",
            details={'error': str(e)}
        ), 500

@performance_bp.route('/preload', methods=['POST'])
@require_auth
def preload_user_data():
    """Preload user-specific data for faster access"""
    try:
        user = get_current_user()
        data = request.get_json() or {}
        preload_types = data.get('types', ['resumes', 'profile'])
        
        preloaded_data = {}
        
        if 'resumes' in preload_types:
            # Preload user's recent resumes
            try:
                from railway_database import RailwayDatabase
                db = RailwayDatabase()
                user_resumes = db.execute_read(
                    "SELECT * FROM resumes WHERE user_id = %s ORDER BY upload_date DESC LIMIT 20",
                    [user['id']]
                )
                
                # Cache each resume
                for resume in user_resumes:
                    cache_key = f"resume:{resume['id']}"
                    performance_helper.cache.set(cache_key, resume, ttl=300, tags=['resume', f"user:{user['id']}"])
                
                preloaded_data['resumes'] = {
                    'count': len(user_resumes),
                    'cached': True
                }
            except Exception as e:
                logger.error(f"Error preloading resumes: {e}")
                preloaded_data['resumes'] = {'error': str(e)}
        
        if 'profile' in preload_types:
            # Preload user profile data
            try:
                cache_key = f"user_profile:{user['id']}"
                performance_helper.cache.set(cache_key, user, ttl=600, tags=[f"user:{user['id']}"])
                preloaded_data['profile'] = {'cached': True}
            except Exception as e:
                logger.error(f"Error preloading profile: {e}")
                preloaded_data['profile'] = {'error': str(e)}
        
        return response_formatter.success(
            data={
                'preloaded_data': preloaded_data,
                'user_id': user['id'],
                'preload_types': preload_types
            },
            message="User data preloaded successfully"
        )
        
    except Exception as e:
        logger.error(f"Error preloading user data: {e}")
        return response_formatter.error(
            message="Failed to preload user data",
            error_code="PRELOAD_ERROR",
            details={'error': str(e)}
        ), 500

@performance_bp.route('/compression-test', methods=['POST'])
@require_auth
def test_compression():
    """Test response compression for optimization"""
    try:
        data = request.get_json() or {}
        test_data = data.get('test_data', {'message': 'test'})
        
        # Original size
        original_json = json.dumps(test_data, default=str)
        original_size = len(original_json.encode('utf-8'))
        
        # Compressed size
        compressed_data = performance_helper.compress_response(test_data)
        compressed_size = len(compressed_data.encode('utf-8'))
        
        # Compression ratio
        compression_ratio = (original_size - compressed_size) / original_size * 100 if original_size > 0 else 0
        
        # Test decompression
        try:
            decompressed_data = performance_helper.decompress_response(compressed_data)
            decompression_success = decompressed_data == test_data
        except Exception as e:
            decompression_success = False
            decompressed_data = None
        
        return response_formatter.success(
            data={
                'original_size_bytes': original_size,
                'compressed_size_bytes': compressed_size,
                'compression_ratio_percent': round(compression_ratio, 2),
                'compression_recommended': original_size > performance_helper.compression_threshold,
                'decompression_success': decompression_success,
                'compression_threshold': performance_helper.compression_threshold
            },
            message="Compression test completed"
        )
        
    except Exception as e:
        logger.error(f"Error testing compression: {e}")
        return response_formatter.error(
            message="Failed to test compression",
            error_code="COMPRESSION_TEST_ERROR",
            details={'error': str(e)}
        ), 500
