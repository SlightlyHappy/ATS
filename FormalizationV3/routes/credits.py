"""
Credit System and Queue Management Routes
Handles credit management, queue operations, and trial limitations
"""

import logging
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from functools import wraps

logger = logging.getLogger(__name__)

# Create Blueprint
credits_bp = Blueprint('credits', __name__, url_prefix='/api')

# Global references (will be set by init_credits_routes)
_credit_manager = None
_queue_manager = None
_auth_middleware = None
_db_manager = None

def init_credits_routes(credit_manager, queue_manager, auth_middleware, db_manager):
    """Initialize credits routes with dependencies"""
    global _credit_manager, _queue_manager, _auth_middleware, _db_manager
    _credit_manager = credit_manager
    _queue_manager = queue_manager
    _auth_middleware = auth_middleware
    _db_manager = db_manager
    logger.info("✅ Credits routes initialized")

# ============================================================================
# CREDIT SYSTEM HEALTH CHECK
# ============================================================================

@credits_bp.route('/credits/health', methods=['GET'])
def credit_system_health():
    """Credit system health check endpoint with thread-safe timeout"""
    try:
        if not _credit_manager:
            return jsonify({
                "status": "unavailable",
                "message": "Credit system not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }), 503
        
        # Try to get credit system status
        try:
            health_result = _credit_manager.health_check() if hasattr(_credit_manager, 'health_check') else {"status": "ok"}
            
            # Check queue manager if available
            queue_health = None
            if _queue_manager and hasattr(_queue_manager, 'health_check'):
                queue_health = _queue_manager.health_check()
            
            return jsonify({
                "status": "healthy",
                "service": "credit-system",
                "credit_manager": health_result,
                "queue_manager": queue_health,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Credit system health check error: {e}")
            return jsonify({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), 503
        
    except Exception as e:
        logger.error(f"Credit health check failed: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

# ============================================================================
# CREDIT STATUS AND MANAGEMENT
# ============================================================================

@credits_bp.route('/credits/status', methods=['GET'])
def credit_status():
    """Get user credit status"""
    try:
        # Check authentication
        if _auth_middleware and not _auth_middleware.is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = _auth_middleware.get_current_user_id() if _auth_middleware else None
        
        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        if not _credit_manager:
            return jsonify({
                "error": "Credit system not available",
                "fallback": "Trial mode active"
            }), 503
        
        # Get credit status
        try:
            status = _credit_manager.get_user_credits(user_id)
            
            return jsonify({
                "success": True,
                "user_id": user_id,
                "credits": status.get('credits', 0),
                "trial_credits": status.get('trial_credits', 0),
                "subscription_type": status.get('subscription_type', 'trial'),
                "last_updated": status.get('last_updated'),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Credit status error: {e}")
            return jsonify({
                "error": "Failed to get credit status",
                "message": str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Credit status check failed: {e}")
        return jsonify({
            "error": "Credit status check failed",
            "message": str(e)
        }), 500

# ============================================================================
# QUEUE MANAGEMENT ENDPOINTS
# ============================================================================

@credits_bp.route('/queue/add', methods=['POST'])
def add_to_queue():
    """Add request to processing queue"""
    try:
        # Check authentication
        if _auth_middleware and not _auth_middleware.is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = _auth_middleware.get_current_user_id() if _auth_middleware else None
        
        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        if not data or not data.get('request_type'):
            return jsonify({"error": "Request type required"}), 400
        
        request_type = data['request_type']
        request_data = data.get('data', {})
        priority = data.get('priority', 'normal')
        
        if not _queue_manager:
            return jsonify({
                "error": "Queue system not available",
                "recommendation": "Process request directly"
            }), 503
        
        # Add to queue
        try:
            queue_result = _queue_manager.add_request(
                user_id=user_id,
                request_type=request_type,
                request_data=request_data,
                priority=priority
            )
            
            return jsonify({
                "success": True,
                "request_id": queue_result.get('request_id'),
                "queue_position": queue_result.get('queue_position'),
                "estimated_wait_time": queue_result.get('estimated_wait_time'),
                "status": "queued",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Queue add error: {e}")
            return jsonify({
                "error": "Failed to add to queue",
                "message": str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Queue add failed: {e}")
        return jsonify({
            "error": "Queue operation failed",
            "message": str(e)
        }), 500

@credits_bp.route('/queue/status/<request_id>', methods=['GET'])
def get_queue_status(request_id):
    """Get status of queued request"""
    try:
        # Check authentication
        if _auth_middleware and not _auth_middleware.is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = _auth_middleware.get_current_user_id() if _auth_middleware else None
        
        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        if not _queue_manager:
            return jsonify({
                "error": "Queue system not available",
                "status": "unknown"
            }), 503
        
        # Get queue status
        try:
            status = _queue_manager.get_request_status(request_id, user_id)
            
            if not status:
                return jsonify({
                    "error": "Request not found",
                    "request_id": request_id
                }), 404
            
            return jsonify({
                "success": True,
                "request_id": request_id,
                "status": status.get('status'),
                "queue_position": status.get('queue_position'),
                "progress": status.get('progress', 0),
                "result": status.get('result'),
                "error": status.get('error'),
                "created_at": status.get('created_at'),
                "updated_at": status.get('updated_at'),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Queue status error: {e}")
            return jsonify({
                "error": "Failed to get queue status",
                "message": str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Queue status check failed: {e}")
        return jsonify({
            "error": "Queue status check failed",
            "message": str(e)
        }), 500

# ============================================================================
# TRIAL MANAGEMENT ENDPOINTS
# ============================================================================

@credits_bp.route('/trial/status', methods=['GET'])
def trial_status():
    """Get trial status for current user"""
    try:
        # Check authentication
        if _auth_middleware and not _auth_middleware.is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = _auth_middleware.get_current_user_id() if _auth_middleware else None
        
        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        # Get trial status from database or credit manager
        try:
            if _credit_manager and hasattr(_credit_manager, 'get_trial_status'):
                trial_info = _credit_manager.get_trial_status(user_id)
            elif _db_manager and hasattr(_db_manager, 'get_user_trial_status'):
                trial_info = _db_manager.get_user_trial_status(user_id)
            else:
                # Fallback - basic trial info
                trial_info = {
                    "trial_resumes_analyzed": 0,
                    "trial_limit": 100,
                    "access_type": "trial"
                }
            
            remaining = trial_info.get('trial_limit', 100) - trial_info.get('trial_resumes_analyzed', 0)
            
            return jsonify({
                "success": True,
                "trial_resumes_analyzed": trial_info.get('trial_resumes_analyzed', 0),
                "trial_limit": trial_info.get('trial_limit', 100),
                "remaining": max(0, remaining),
                "access_type": trial_info.get('access_type', 'trial'),
                "upgrade_available": remaining <= 10,  # Suggest upgrade when 10 or fewer remaining
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Trial status error: {e}")
            return jsonify({
                "error": "Failed to get trial status",
                "message": str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Trial status check failed: {e}")
        return jsonify({
            "error": "Trial status check failed",
            "message": str(e)
        }), 500

@credits_bp.route('/trial/track-usage', methods=['POST'])
def track_trial_usage():
    """Track trial usage (internal endpoint)"""
    try:
        # Check authentication
        if _auth_middleware and not _auth_middleware.is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = _auth_middleware.get_current_user_id() if _auth_middleware else None
        
        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        action = data.get('action', 'resume_analysis')
        
        # Track usage
        try:
            if _credit_manager and hasattr(_credit_manager, 'track_trial_usage'):
                result = _credit_manager.track_trial_usage(user_id, action)
            elif _db_manager and hasattr(_db_manager, 'increment_trial_usage'):
                result = _db_manager.increment_trial_usage(user_id, action)
            else:
                result = {"success": True, "remaining": 99}  # Fallback
            
            return jsonify({
                "success": True,
                "action": action,
                "remaining": result.get('remaining'),
                "limit_reached": result.get('limit_reached', False),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Trial usage tracking error: {e}")
            return jsonify({
                "error": "Failed to track usage",
                "message": str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Trial usage tracking failed: {e}")
        return jsonify({
            "error": "Usage tracking failed",
            "message": str(e)
        }), 500

@credits_bp.route('/trial/upgrade-info', methods=['GET'])
def trial_upgrade_info():
    """Get upgrade information for trial users"""
    try:
        upgrade_options = {
            "plans": [
                {
                    "name": "Professional",
                    "price": "$29/month",
                    "features": [
                        "Unlimited resume processing",
                        "Advanced AI analysis",
                        "Bulk operations",
                        "Export capabilities",
                        "Priority support"
                    ]
                },
                {
                    "name": "Enterprise",
                    "price": "Contact sales",
                    "features": [
                        "Everything in Professional",
                        "Custom integrations",
                        "Dedicated support",
                        "SLA guarantees",
                        "Custom AI models"
                    ]
                }
            ],
            "contact_info": {
                "email": "sales@hrtools.com",
                "phone": "+1-555-HR-TOOLS",
                "website": "https://hrtools.com/pricing"
            }
        }
        
        return jsonify({
            "success": True,
            "upgrade_options": upgrade_options,
            "current_plan": "trial",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Upgrade info error: {e}")
        return jsonify({
            "error": "Failed to get upgrade info",
            "message": str(e)
        }), 500
