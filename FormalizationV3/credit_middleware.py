#!/usr/bin/env python3
"""
Credit-Aware Route Middleware
Non-breaking enhancement to existing routes for B2B monetization
"""

import logging
from functools import wraps
from typing import Dict, Any, Optional, Callable
from flask import request, jsonify, g

from credit_manager import CreditManager, ProcessingTier, CreditStatus
from queue_manager import BasicRequestQueue, QueueStatus

logger = logging.getLogger(__name__)

class CreditRouteMiddleware:
    """
    Non-breaking middleware to add credit awareness to existing routes
    Enhances routes without changing existing functionality
    """
    
    def __init__(self, credit_manager: CreditManager, queue_manager: BasicRequestQueue):
        """Initialize middleware with credit and queue managers"""
        self.credit_manager = credit_manager
        self.queue_manager = queue_manager
        logger.info("Credit route middleware initialized")
    
    def with_credit_check(self, feature_name: str = "general", credits_required: int = 1):
        """
        Decorator to add credit checking to existing routes
        Non-breaking: if credit system fails, allows request to proceed
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    # Get current user (assuming auth middleware sets this)
                    user = getattr(g, 'current_user', None)
                    if not user:
                        # No user context - proceed with original function
                        logger.warning("No user context for credit check, proceeding")
                        return func(*args, **kwargs)
                    
                    user_id = user.get('user_id')
                    if not user_id:
                        # No user ID - proceed with original function
                        return func(*args, **kwargs)
                    
                    # Check credit status
                    credit_status = self.credit_manager.check_user_credits(user_id)
                    
                    # Store credit status in request context
                    g.credit_status = credit_status
                    g.credits_available = credit_status.can_process
                    
                    # If no credits available, return monetization response
                    if not credit_status.can_process:
                        return self._handle_no_credits(credit_status, feature_name)
                    
                    # Check queue status for routing decision
                    queue_status = self.queue_manager.get_queue_status()
                    
                    # If Ollama busy and user on trial, offer queue or skip options
                    if (queue_status in [QueueStatus.BUSY, QueueStatus.OVERLOADED] and 
                        credit_status.processing_tier == ProcessingTier.FREE_TRIAL):
                        return self._handle_queue_options(credit_status, feature_name, func, args, kwargs)
                    
                    # Proceed with original function
                    # Credits will be deducted by the queue manager during processing
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    # If credit system fails, log error but proceed with original function
                    logger.error(f"Credit middleware error: {e}")
                    return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def _handle_no_credits(self, credit_status: CreditStatus, feature_name: str) -> Dict[str, Any]:
        """Handle users with no credits - offer premium options or sales contact"""
        return jsonify({
            "success": False,
            "error": "insufficient_credits",
            "message": "Your trial credits have been exhausted",
            "credit_status": {
                "trial_credits": credit_status.trial_credits,
                "premium_credits": credit_status.premium_credits,
                "total_used": credit_status.total_used,
                "credits_remaining": credit_status.credits_remaining
            },
            "monetization_options": {
                "premium_credits": {
                    "10_credits": {
                        "price_inr": 300,
                        "price_usd": 4.00,
                        "description": "10 premium credits for instant processing"
                    },
                    "25_credits": {
                        "price_inr": 650,
                        "price_usd": 8.50,
                        "description": "25 premium credits - best value"
                    }
                },
                "contact_sales": {
                    "message": "For high-volume usage, contact our sales team for enterprise pricing",
                    "email": "sales@bearsystems.co.in",
                    "features": ["Unlimited processing", "Priority support", "Custom integrations"]
                }
            },
            "usage_summary": {
                "total_sessions": credit_status.usage_pattern.get("total_sessions", 0),
                "features_used": list(credit_status.usage_pattern.get("features", {}).keys()),
                "lead_score": credit_status.lead_score
            },
            "trial_completed": True
        }), 402  # Payment Required
    
    def _handle_queue_options(self, credit_status: CreditStatus, feature_name: str, 
                            func: Callable, args: tuple, kwargs: dict) -> Dict[str, Any]:
        """Handle queue busy situation - offer queue or skip options"""
        queue_stats = self.queue_manager.get_queue_stats()
        
        return jsonify({
            "success": False, 
            "status": "queue_busy",
            "message": "System is currently busy. You can wait in queue or skip for instant processing.",
            "queue_info": {
                "status": queue_stats["queue_status"],
                "pending_requests": queue_stats["pending_requests"],
                "estimated_wait_minutes": max(2, queue_stats["pending_requests"] * 2)  # Rough estimate
            },
            "options": {
                "wait_in_queue": {
                    "description": "Free - wait in queue for processing",
                    "estimated_wait": f"{max(2, queue_stats['pending_requests'] * 2)} minutes",
                    "action": "POST /api/queue/add",
                    "cost": 0
                },
                "skip_queue": {
                    "description": "Skip the queue for instant processing",
                    "price_inr": 40,
                    "price_usd": 0.50,
                    "action": "POST /api/payment/queue-skip",
                    "instant": True
                }
            },
            "credit_status": {
                "trial_credits": credit_status.trial_credits,
                "credits_remaining": credit_status.credits_remaining
            },
            "request_context": {
                "feature": feature_name,
                "can_queue": True,
                "can_skip": True
            }
        }), 202  # Accepted - will be processed later
    
    def queue_request(self, user_id: str, request_type: str, request_data: Dict[str, Any],
                     processing_tier: ProcessingTier = ProcessingTier.FREE_TRIAL) -> Dict[str, Any]:
        """Add request to queue and return queue info"""
        try:
            request_id, queue_info = self.queue_manager.add_request(
                user_id, request_type, request_data, processing_tier
            )
            
            return {
                "success": True,
                "status": "queued",
                "request_id": request_id,
                "queue_info": queue_info,
                "message": f"Request queued at position {queue_info['position']}"
            }
            
        except Exception as e:
            logger.error(f"Failed to queue request: {e}")
            return {
                "success": False,
                "error": "queue_failed",
                "message": "Failed to add request to queue"
            }
    
    def get_request_status(self, request_id: str) -> Dict[str, Any]:
        """Get status of a queued request"""
        try:
            status = self.queue_manager.get_request_status(request_id)
            return {
                "success": True,
                "request_status": status
            }
        except Exception as e:
            logger.error(f"Failed to get request status: {e}")
            return {
                "success": False,
                "error": "status_check_failed"
            }
    
    def skip_queue_with_payment(self, request_id: str, payment_verified: bool = False) -> Dict[str, Any]:
        """Skip queue with verified payment"""
        try:
            if not payment_verified:
                return {
                    "success": False,
                    "error": "payment_not_verified",
                    "message": "Payment must be verified before skipping queue"
                }
            
            success = self.queue_manager.skip_queue(request_id, payment_verified)
            
            if success:
                return {
                    "success": True,
                    "message": "Request moved to priority processing",
                    "status": "premium_processing"
                }
            else:
                return {
                    "success": False,
                    "error": "skip_failed",
                    "message": "Failed to skip queue - request may not exist"
                }
                
        except Exception as e:
            logger.error(f"Failed to skip queue: {e}")
            return {
                "success": False,
                "error": "skip_queue_error"
            }
    
    def offer_premium_options(self, credit_status: CreditStatus) -> Dict[str, Any]:
        """Generate premium options based on user usage pattern"""
        usage_pattern = credit_status.usage_pattern or {}
        total_sessions = usage_pattern.get("total_sessions", 0)
        
        # Personalized recommendations based on usage
        if total_sessions > 20:
            # High volume user - enterprise recommendation
            primary_option = {
                "type": "enterprise",
                "title": "Enterprise Plan Recommended",
                "description": "Based on your usage, our enterprise plan would be most cost-effective",
                "action": "contact_sales",
                "benefits": ["Unlimited processing", "Priority support", "Custom features"]
            }
        elif total_sessions > 10:
            # Medium usage - premium credits
            primary_option = {
                "type": "premium_credits",
                "title": "Premium Credits Package",
                "description": "Get 25 premium credits for extended usage",
                "price_inr": 650,
                "price_usd": 8.50,
                "action": "purchase_credits"
            }
        else:
            # Light usage - small pack
            primary_option = {
                "type": "starter_credits", 
                "title": "Starter Credits Package",
                "description": "Get 10 premium credits to continue",
                "price_inr": 300,
                "price_usd": 4.00,
                "action": "purchase_credits"
            }
        
        return {
            "primary_recommendation": primary_option,
            "all_options": {
                "instant_skip": {
                    "price_inr": 40,
                    "description": "Skip queue once for immediate processing"
                },
                "premium_10": {
                    "price_inr": 300,
                    "description": "10 premium credits"
                },
                "premium_25": {
                    "price_inr": 650,
                    "description": "25 premium credits - best value"
                },
                "enterprise": {
                    "description": "Unlimited usage with enterprise features",
                    "action": "contact_sales"
                }
            },
            "usage_insights": {
                "sessions": total_sessions,
                "lead_score": credit_status.lead_score,
                "value_demonstrated": total_sessions > 5
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for credit middleware"""
        try:
            credit_health = self.credit_manager.health_check()
            queue_health = self.queue_manager.health_check()
            
            return {
                "status": "healthy" if credit_health["status"] == "healthy" and queue_health["status"] in ["healthy", "degraded"] else "unhealthy",
                "credit_system": credit_health,
                "queue_system": queue_health,
                "middleware_ready": True,
                "timestamp": credit_health.get("timestamp")
            }
            
        except Exception as e:
            logger.error(f"Credit middleware health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "middleware_ready": False
            }

# Convenience functions for route integration
def create_credit_aware_route(credit_middleware: CreditRouteMiddleware, 
                            feature_name: str = "general", 
                            credits_required: int = 1):
    """
    Create a credit-aware route decorator
    Usage: @create_credit_aware_route(middleware, "resume_analysis", 1)
    """
    return credit_middleware.with_credit_check(feature_name, credits_required)

def handle_queue_request(credit_middleware: CreditRouteMiddleware):
    """Handle queue request from frontend"""
    try:
        data = request.get_json() or {}
        user = getattr(g, 'current_user', {})
        user_id = user.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User authentication required"}), 401
        
        request_type = data.get('request_type', 'resume_analysis')
        request_data = data.get('request_data', {})
        
        result = credit_middleware.queue_request(user_id, request_type, request_data)
        
        if result["success"]:
            return jsonify(result), 202
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Queue request handler error: {e}")
        return jsonify({"error": "Failed to handle queue request"}), 500

def handle_request_status(credit_middleware: CreditRouteMiddleware, request_id: str):
    """Handle request status check"""
    try:
        result = credit_middleware.get_request_status(request_id)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Request status handler error: {e}")
        return jsonify({"error": "Failed to get request status"}), 500
