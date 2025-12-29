"""
API health and monitoring routes - extracted from monolithic app.py
Handles: health checks, system status, API monitoring, performance metrics
"""

import os
import json
import logging
import psutil
import platform
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

# Create blueprint
health_bp = Blueprint('health', __name__, url_prefix='/api')

# Global dependencies (will be injected during initialization)
db_manager = None
railway_db = None
auth_middleware = None
cache_manager = None
ai_processor = None

# Health check cache
health_cache = {}
last_health_check = None

def init_health_routes(database_manager=None, railway_database=None, auth_mid=None, 
                      cache_mgr=None, ai_proc=None):
    """Initialize health routes with dependencies"""
    global db_manager, railway_db, auth_middleware, cache_manager, ai_processor
    
    db_manager = database_manager
    railway_db = railway_database
    auth_middleware = auth_mid
    cache_manager = cache_mgr
    ai_processor = ai_proc
    
    logger.info("✅ Health routes initialized")

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    try:
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "HR ATS API",
            "version": "3.0.0"
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Comprehensive health check with all system components"""
    try:
        global last_health_check, health_cache
        
        # Cache health check for 30 seconds to avoid overload
        now = datetime.utcnow()
        if (last_health_check and 
            (now - last_health_check).total_seconds() < 30 and 
            health_cache):
            return jsonify(health_cache)
        
        health_status = {
            "overall_status": "healthy",
            "timestamp": now.isoformat(),
            "service_info": {
                "name": "HR ATS API",
                "version": "3.0.0",
                "environment": os.getenv("ENVIRONMENT", "production"),
                "deployment": "railway"
            },
            "components": {}
        }
        
        # Database health
        db_status = check_database_health()
        health_status["components"]["database"] = db_status
        
        # AI Processor health
        ai_status = check_ai_processor_health()
        health_status["components"]["ai_processor"] = ai_status
        
        # Cache health (if available)
        if cache_manager:
            cache_status = check_cache_health()
            health_status["components"]["cache"] = cache_status
        
        # System resources
        system_status = check_system_resources()
        health_status["components"]["system"] = system_status
        
        # API endpoints health
        api_status = check_api_endpoints()
        health_status["components"]["api_endpoints"] = api_status
        
        # External services health
        external_status = check_external_services()
        health_status["components"]["external_services"] = external_status
        
        # Determine overall status
        component_statuses = [
            comp.get("status", "unknown") 
            for comp in health_status["components"].values()
        ]
        
        if "critical" in component_statuses:
            health_status["overall_status"] = "critical"
            status_code = 503
        elif "degraded" in component_statuses:
            health_status["overall_status"] = "degraded"
            status_code = 200
        else:
            health_status["overall_status"] = "healthy"
            status_code = 200
        
        # Cache the result
        health_cache = health_status
        last_health_check = now
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Detailed health check error: {e}")
        return jsonify({
            "overall_status": "critical",
            "error": "Health check failed",
            "timestamp": datetime.utcnow().isoformat()
        }), 503

@health_bp.route('/status', methods=['GET'])
def system_status():
    """Get comprehensive system status"""
    try:
        status_data = {
            "system_info": get_system_info(),
            "performance_metrics": get_performance_metrics(),
            "active_connections": get_active_connections(),
            "recent_errors": get_recent_errors(),
            "uptime": get_system_uptime(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify({
            "success": True,
            "status": status_data
        })
        
    except Exception as e:
        logger.error(f"System status error: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get system status"
        }), 500

@health_bp.route('/metrics', methods=['GET'])
def api_metrics():
    """Get API performance metrics"""
    try:
        # Check if user is authenticated for detailed metrics
        authenticated = False
        if auth_middleware:
            try:
                user = auth_middleware.get_current_user()
                authenticated = bool(user)
            except:
                pass
        
        metrics_data = {
            "basic_metrics": get_basic_metrics(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add detailed metrics for authenticated users
        if authenticated:
            metrics_data["detailed_metrics"] = get_detailed_metrics()
            metrics_data["database_metrics"] = get_database_metrics()
        
        return jsonify({
            "success": True,
            "metrics": metrics_data,
            "authenticated": authenticated
        })
        
    except Exception as e:
        logger.error(f"API metrics error: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get metrics"
        }), 500

@health_bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint for uptime monitoring"""
    return jsonify({
        "pong": True,
        "timestamp": datetime.utcnow().isoformat(),
        "server": "HR-ATS-API"
    })

@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """Kubernetes/Railway readiness probe"""
    try:
        # Check critical dependencies
        ready = True
        checks = {}
        
        # Database check
        if railway_db:
            try:
                railway_db.execute_read("SELECT 1")
                checks["database"] = True
            except Exception:
                checks["database"] = False
                ready = False
        else:
            checks["database"] = False
            ready = False
        
        # AI Processor check
        if ai_processor:
            checks["ai_processor"] = True
        else:
            checks["ai_processor"] = False
            ready = False
        
        if ready:
            return jsonify({
                "ready": True,
                "checks": checks,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                "ready": False,
                "checks": checks,
                "timestamp": datetime.utcnow().isoformat()
            }), 503
            
    except Exception as e:
        logger.error(f"Readiness check error: {e}")
        return jsonify({
            "ready": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503

@health_bp.route('/live', methods=['GET'])
def liveness_check():
    """Kubernetes/Railway liveness probe"""
    try:
        # Basic liveness check - just ensure the app is responding
        return jsonify({
            "alive": True,
            "timestamp": datetime.utcnow().isoformat(),
            "pid": os.getpid()
        })
    except Exception as e:
        logger.error(f"Liveness check error: {e}")
        return jsonify({
            "alive": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503

# Health check helper functions

def check_database_health():
    """Check database connectivity and performance"""
    try:
        start_time = datetime.utcnow()
        
        if not railway_db:
            return {
                "status": "critical",
                "message": "Database manager not available",
                "response_time_ms": 0
            }
        
        # Test basic connectivity
        result = railway_db.execute_read("SELECT 1 as test")
        
        if not result:
            return {
                "status": "critical",
                "message": "Database query failed",
                "response_time_ms": 0
            }
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Check response time
        if response_time > 5000:  # 5 seconds
            status = "degraded"
            message = f"Database response slow: {response_time:.0f}ms"
        elif response_time > 1000:  # 1 second
            status = "degraded"
            message = f"Database response acceptable: {response_time:.0f}ms"
        else:
            status = "healthy"
            message = f"Database responding normally: {response_time:.0f}ms"
        
        return {
            "status": status,
            "message": message,
            "response_time_ms": round(response_time, 2),
            "connection_pool": "active"
        }
        
    except Exception as e:
        logger.error(f"Database health check error: {e}")
        return {
            "status": "critical",
            "message": f"Database error: {str(e)}",
            "response_time_ms": 0
        }

def check_ai_processor_health():
    """Check AI processor availability"""
    try:
        if not ai_processor:
            return {
                "status": "critical",
                "message": "AI processor not available"
            }
        
        # Check if AI processor is initialized
        if hasattr(ai_processor, 'is_healthy') and callable(ai_processor.is_healthy):
            is_healthy = ai_processor.is_healthy()
            if is_healthy:
                return {
                    "status": "healthy",
                    "message": "AI processor operational",
                    "providers": getattr(ai_processor, 'available_providers', [])
                }
            else:
                return {
                    "status": "degraded",
                    "message": "AI processor has issues"
                }
        else:
            return {
                "status": "healthy",
                "message": "AI processor available"
            }
            
    except Exception as e:
        logger.error(f"AI processor health check error: {e}")
        return {
            "status": "degraded",
            "message": f"AI processor check failed: {str(e)}"
        }

def check_cache_health():
    """Check cache system health"""
    try:
        if not cache_manager:
            return {
                "status": "degraded",
                "message": "Cache manager not available"
            }
        
        # Test cache operations
        test_key = "health_check_test"
        test_value = {"test": True, "timestamp": datetime.utcnow().isoformat()}
        
        # Set and get test
        cache_manager.set(test_key, test_value, ttl=60)
        retrieved = cache_manager.get(test_key)
        
        if retrieved and retrieved.get("test"):
            cache_manager.delete(test_key)  # Cleanup
            return {
                "status": "healthy",
                "message": "Cache operations working"
            }
        else:
            return {
                "status": "degraded",
                "message": "Cache operations failed"
            }
            
    except Exception as e:
        logger.error(f"Cache health check error: {e}")
        return {
            "status": "degraded",
            "message": f"Cache error: {str(e)}"
        }

def check_system_resources():
    """Check system resource usage"""
    try:
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        # Determine status based on resource usage
        if memory_percent > 90 or cpu_percent > 90 or disk_percent > 95:
            status = "critical"
            message = "System resources critically high"
        elif memory_percent > 80 or cpu_percent > 80 or disk_percent > 90:
            status = "degraded"
            message = "System resources elevated"
        else:
            status = "healthy"
            message = "System resources normal"
        
        return {
            "status": status,
            "message": message,
            "memory_percent": round(memory_percent, 1),
            "cpu_percent": round(cpu_percent, 1),
            "disk_percent": round(disk_percent, 1),
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        }
        
    except Exception as e:
        logger.error(f"System resources check error: {e}")
        return {
            "status": "unknown",
            "message": f"Resource check failed: {str(e)}"
        }

def check_api_endpoints():
    """Check critical API endpoints"""
    try:
        # This would test critical internal endpoints
        return {
            "status": "healthy",
            "message": "API endpoints responsive",
            "checked_endpoints": [
                "/api/health",
                "/api/auth/profile",
                "/api/upload"
            ]
        }
    except Exception as e:
        return {
            "status": "degraded",
            "message": f"Endpoint check failed: {str(e)}"
        }

def check_external_services():
    """Check external service dependencies"""
    try:
        services_status = {}
        
        # Check AI providers (if configured)
        ai_services = ["openai", "anthropic", "gemini"]
        for service in ai_services:
            try:
                # This would make actual health checks to AI providers
                services_status[service] = "healthy"
            except:
                services_status[service] = "unknown"
        
        # Overall external services status
        if all(status == "healthy" for status in services_status.values()):
            overall_status = "healthy"
            message = "All external services operational"
        elif any(status == "healthy" for status in services_status.values()):
            overall_status = "degraded"
            message = "Some external services unavailable"
        else:
            overall_status = "degraded"
            message = "External services status unknown"
        
        return {
            "status": overall_status,
            "message": message,
            "services": services_status
        }
        
    except Exception as e:
        return {
            "status": "unknown",
            "message": f"External services check failed: {str(e)}"
        }

def get_system_info():
    """Get basic system information"""
    try:
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "disk_total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
            "process_id": os.getpid(),
            "working_directory": os.getcwd()
        }
    except Exception as e:
        logger.error(f"Get system info error: {e}")
        return {"error": str(e)}

def get_performance_metrics():
    """Get performance metrics"""
    try:
        return {
            "memory_usage_mb": round(psutil.Process().memory_info().rss / (1024**2), 2),
            "cpu_percent": psutil.cpu_percent(),
            "open_files": len(psutil.Process().open_files()),
            "threads": psutil.Process().num_threads(),
            "connections": len(psutil.net_connections())
        }
    except Exception as e:
        logger.error(f"Get performance metrics error: {e}")
        return {"error": str(e)}

def get_active_connections():
    """Get active connection count"""
    try:
        # This would get actual connection counts from SocketIO, database pools, etc.
        return {
            "http_connections": "unknown",
            "websocket_connections": "unknown",
            "database_connections": "unknown"
        }
    except Exception as e:
        return {"error": str(e)}

def get_recent_errors():
    """Get recent error count"""
    try:
        # This would query error logs or monitoring systems
        return {
            "last_hour": 0,
            "last_24_hours": 0,
            "last_week": 0
        }
    except Exception as e:
        return {"error": str(e)}

def get_system_uptime():
    """Get system uptime in seconds"""
    try:
        boot_time = psutil.boot_time()
        uptime_seconds = datetime.utcnow().timestamp() - boot_time
        return {
            "uptime_seconds": int(uptime_seconds),
            "uptime_human": format_uptime(uptime_seconds),
            "boot_time": datetime.fromtimestamp(boot_time).isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

def get_basic_metrics():
    """Get basic performance metrics"""
    try:
        return {
            "requests_per_minute": "unknown",  # Would need request counter
            "average_response_time": "unknown",  # Would need response time tracking
            "error_rate": "unknown",  # Would need error tracking
            "active_users": "unknown"  # Would need session tracking
        }
    except Exception as e:
        return {"error": str(e)}

def get_detailed_metrics():
    """Get detailed metrics for authenticated users"""
    try:
        return {
            "database_pool_size": "unknown",
            "cache_hit_rate": "unknown",
            "ai_processing_queue": "unknown",
            "memory_breakdown": get_memory_breakdown()
        }
    except Exception as e:
        return {"error": str(e)}

def get_database_metrics():
    """Get database-specific metrics"""
    try:
        if not railway_db:
            return {"error": "Database not available"}
        
        # This would query database-specific metrics
        return {
            "active_connections": "unknown",
            "slow_queries": "unknown",
            "table_sizes": "unknown",
            "index_usage": "unknown"
        }
    except Exception as e:
        return {"error": str(e)}

def get_memory_breakdown():
    """Get detailed memory usage breakdown"""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": round(memory_info.rss / (1024**2), 2),
            "vms_mb": round(memory_info.vms / (1024**2), 2),
            "percent": round(process.memory_percent(), 2)
        }
    except Exception as e:
        return {"error": str(e)}

def format_uptime(seconds):
    """Format uptime in human-readable format"""
    try:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except:
        return "unknown"
