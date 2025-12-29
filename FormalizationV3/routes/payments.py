"""
Payment Management Routes
Handles payment processing, subscription management, and billing
"""

import logging
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from functools import wraps

logger = logging.getLogger(__name__)

# Create Blueprint
payments_bp = Blueprint('payments', __name__, url_prefix='/api')

# Global references (will be set by init_payments_routes)
_payment_manager = None
_credit_manager = None
_auth_middleware = None
_db_manager = None

def init_payments_routes(payment_manager, credit_manager, auth_middleware, db_manager):
    """Initialize payments routes with dependencies"""
    global _payment_manager, _credit_manager, _auth_middleware, _db_manager
    _payment_manager = payment_manager
    _credit_manager = credit_manager
    _auth_middleware = auth_middleware
    _db_manager = db_manager
    logger.info("✅ Payments routes initialized")

# ============================================================================
# PAYMENT SYSTEM HEALTH CHECK
# ============================================================================

@payments_bp.route('/payments/health', methods=['GET'])
def payment_system_health():
    """Payment system health check endpoint"""
    try:
        if not _payment_manager:
            return jsonify({
                "status": "unavailable",
                "message": "Payment system not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }), 503
        
        # Try to get payment system status
        try:
            health_result = _payment_manager.health_check() if hasattr(_payment_manager, 'health_check') else {"status": "ok"}
            
            return jsonify({
                "status": "healthy",
                "service": "payment-system",
                "payment_manager": health_result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Payment system health check error: {e}")
            return jsonify({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), 503
        
    except Exception as e:
        logger.error(f"Payment health check failed: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

# ============================================================================
# SUBSCRIPTION MANAGEMENT
# ============================================================================

@payments_bp.route('/subscription/status', methods=['GET'])
def subscription_status():
    """Get user subscription status"""
    try:
        # Check authentication
        if _auth_middleware and not _auth_middleware.is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = _auth_middleware.get_current_user_id() if _auth_middleware else None
        
        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        # Get subscription status
        try:
            if _payment_manager and hasattr(_payment_manager, 'get_subscription_status'):
                subscription = _payment_manager.get_subscription_status(user_id)
            elif _db_manager and hasattr(_db_manager, 'get_user_subscription'):
                subscription = _db_manager.get_user_subscription(user_id)
            else:
                # Fallback - trial status
                subscription = {
                    "plan": "trial",
                    "status": "active",
                    "expires_at": None,
                    "features": ["limited_resumes"]
                }
            
            return jsonify({
                "success": True,
                "user_id": user_id,
                "subscription": {
                    "plan": subscription.get('plan', 'trial'),
                    "status": subscription.get('status', 'active'),
                    "expires_at": subscription.get('expires_at'),
                    "features": subscription.get('features', []),
                    "billing_cycle": subscription.get('billing_cycle'),
                    "next_billing_date": subscription.get('next_billing_date')
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Subscription status error: {e}")
            return jsonify({
                "error": "Failed to get subscription status",
                "message": str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Subscription status check failed: {e}")
        return jsonify({
            "error": "Subscription status check failed",
            "message": str(e)
        }), 500

@payments_bp.route('/subscription/plans', methods=['GET'])
def get_subscription_plans():
    """Get available subscription plans"""
    try:
        plans = [
            {
                "id": "trial",
                "name": "Trial Plan",
                "price": 0,
                "currency": "USD",
                "billing_cycle": "one-time",
                "features": [
                    "100 resume analyses",
                    "Basic AI insights",
                    "Standard support",
                    "Export to PDF"
                ],
                "limitations": [
                    "Limited to 100 resumes",
                    "No bulk operations",
                    "No advanced analytics"
                ]
            },
            {
                "id": "professional",
                "name": "Professional Plan", 
                "price": 29,
                "currency": "USD",
                "billing_cycle": "monthly",
                "features": [
                    "Unlimited resume processing",
                    "Advanced AI analysis",
                    "Bulk operations",
                    "Advanced analytics",
                    "Export capabilities",
                    "Priority support",
                    "Custom templates"
                ],
                "limitations": []
            },
            {
                "id": "enterprise",
                "name": "Enterprise Plan",
                "price": 99,
                "currency": "USD", 
                "billing_cycle": "monthly",
                "features": [
                    "Everything in Professional",
                    "Custom integrations",
                    "Dedicated support",
                    "SLA guarantees",
                    "Custom AI models",
                    "White-label options",
                    "Advanced security"
                ],
                "limitations": []
            }
        ]
        
        return jsonify({
            "success": True,
            "plans": plans,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get plans error: {e}")
        return jsonify({
            "error": "Failed to get subscription plans",
            "message": str(e)
        }), 500

# ============================================================================
# PAYMENT PROCESSING
# ============================================================================

@payments_bp.route('/payments/create-intent', methods=['POST'])
def create_payment_intent():
    """Create payment intent for subscription"""
    try:
        # Check authentication
        if _auth_middleware and not _auth_middleware.is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = _auth_middleware.get_current_user_id() if _auth_middleware else None
        
        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        if not data or not data.get('plan_id'):
            return jsonify({"error": "Plan ID required"}), 400
        
        plan_id = data['plan_id']
        
        if not _payment_manager:
            return jsonify({
                "error": "Payment system not available",
                "message": "Contact support for manual billing"
            }), 503
        
        # Create payment intent
        try:
            intent = _payment_manager.create_payment_intent(
                user_id=user_id,
                plan_id=plan_id,
                metadata=data.get('metadata', {})
            )
            
            return jsonify({
                "success": True,
                "payment_intent": {
                    "id": intent.get('id'),
                    "client_secret": intent.get('client_secret'),
                    "amount": intent.get('amount'),
                    "currency": intent.get('currency'),
                    "status": intent.get('status')
                },
                "plan_id": plan_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Payment intent creation error: {e}")
            return jsonify({
                "error": "Failed to create payment intent",
                "message": str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Payment intent failed: {e}")
        return jsonify({
            "error": "Payment intent creation failed",
            "message": str(e)
        }), 500

@payments_bp.route('/payments/confirm', methods=['POST'])
def confirm_payment():
    """Confirm payment and activate subscription"""
    try:
        # Check authentication
        if _auth_middleware and not _auth_middleware.is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = _auth_middleware.get_current_user_id() if _auth_middleware else None
        
        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        if not data or not data.get('payment_intent_id'):
            return jsonify({"error": "Payment intent ID required"}), 400
        
        payment_intent_id = data['payment_intent_id']
        
        if not _payment_manager:
            return jsonify({
                "error": "Payment system not available"
            }), 503
        
        # Confirm payment
        try:
            result = _payment_manager.confirm_payment(
                user_id=user_id,
                payment_intent_id=payment_intent_id
            )
            
            # Update subscription status if payment successful
            if result.get('success') and _credit_manager:
                _credit_manager.activate_subscription(
                    user_id=user_id,
                    plan_id=result.get('plan_id'),
                    payment_id=payment_intent_id
                )
            
            return jsonify({
                "success": result.get('success', False),
                "subscription_status": result.get('subscription_status'),
                "plan_activated": result.get('plan_id'),
                "payment_status": result.get('payment_status'),
                "message": result.get('message'),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Payment confirmation error: {e}")
            return jsonify({
                "error": "Failed to confirm payment",
                "message": str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Payment confirmation failed: {e}")
        return jsonify({
            "error": "Payment confirmation failed",
            "message": str(e)
        }), 500

# ============================================================================
# BILLING MANAGEMENT
# ============================================================================

@payments_bp.route('/billing/history', methods=['GET'])
def billing_history():
    """Get user billing history"""
    try:
        # Check authentication
        if _auth_middleware and not _auth_middleware.is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = _auth_middleware.get_current_user_id() if _auth_middleware else None
        
        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        # Get billing history
        try:
            if _payment_manager and hasattr(_payment_manager, 'get_billing_history'):
                history = _payment_manager.get_billing_history(user_id)
            elif _db_manager and hasattr(_db_manager, 'get_user_payments'):
                history = _db_manager.get_user_payments(user_id)
            else:
                history = []  # Fallback - no history
            
            return jsonify({
                "success": True,
                "user_id": user_id,
                "billing_history": history,
                "total_payments": len(history),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Billing history error: {e}")
            return jsonify({
                "error": "Failed to get billing history",
                "message": str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Billing history check failed: {e}")
        return jsonify({
            "error": "Billing history check failed",
            "message": str(e)
        }), 500

@payments_bp.route('/billing/invoice/<invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    """Get specific invoice details"""
    try:
        # Check authentication
        if _auth_middleware and not _auth_middleware.is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = _auth_middleware.get_current_user_id() if _auth_middleware else None
        
        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        # Get invoice
        try:
            if _payment_manager and hasattr(_payment_manager, 'get_invoice'):
                invoice = _payment_manager.get_invoice(invoice_id, user_id)
            elif _db_manager and hasattr(_db_manager, 'get_user_invoice'):
                invoice = _db_manager.get_user_invoice(invoice_id, user_id)
            else:
                return jsonify({"error": "Invoice not found"}), 404
            
            if not invoice:
                return jsonify({"error": "Invoice not found"}), 404
            
            return jsonify({
                "success": True,
                "invoice": invoice,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Invoice retrieval error: {e}")
            return jsonify({
                "error": "Failed to get invoice",
                "message": str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Invoice retrieval failed: {e}")
        return jsonify({
            "error": "Invoice retrieval failed",
            "message": str(e)
        }), 500

# ============================================================================
# SUBSCRIPTION MANAGEMENT
# ============================================================================

@payments_bp.route('/subscription/cancel', methods=['POST'])
def cancel_subscription():
    """Cancel user subscription"""
    try:
        # Check authentication
        if _auth_middleware and not _auth_middleware.is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = _auth_middleware.get_current_user_id() if _auth_middleware else None
        
        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json() or {}
        reason = data.get('reason', 'user_request')
        immediate = data.get('immediate', False)
        
        if not _payment_manager:
            return jsonify({
                "error": "Payment system not available",
                "message": "Contact support for manual cancellation"
            }), 503
        
        # Cancel subscription
        try:
            result = _payment_manager.cancel_subscription(
                user_id=user_id,
                reason=reason,
                immediate=immediate
            )
            
            return jsonify({
                "success": True,
                "cancellation_result": result,
                "effective_date": result.get('effective_date'),
                "refund_amount": result.get('refund_amount'),
                "message": "Subscription cancelled successfully",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Subscription cancellation error: {e}")
            return jsonify({
                "error": "Failed to cancel subscription",
                "message": str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Subscription cancellation failed: {e}")
        return jsonify({
            "error": "Subscription cancellation failed",
            "message": str(e)
        }), 500

@payments_bp.route('/subscription/update', methods=['POST'])
def update_subscription():
    """Update user subscription plan"""
    try:
        # Check authentication
        if _auth_middleware and not _auth_middleware.is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = _auth_middleware.get_current_user_id() if _auth_middleware else None
        
        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        if not data or not data.get('new_plan_id'):
            return jsonify({"error": "New plan ID required"}), 400
        
        new_plan_id = data['new_plan_id']
        prorate = data.get('prorate', True)
        
        if not _payment_manager:
            return jsonify({
                "error": "Payment system not available",
                "message": "Contact support for manual plan changes"
            }), 503
        
        # Update subscription
        try:
            result = _payment_manager.update_subscription(
                user_id=user_id,
                new_plan_id=new_plan_id,
                prorate=prorate
            )
            
            return jsonify({
                "success": True,
                "update_result": result,
                "new_plan": new_plan_id,
                "effective_date": result.get('effective_date'),
                "proration_amount": result.get('proration_amount'),
                "message": "Subscription updated successfully",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Subscription update error: {e}")
            return jsonify({
                "error": "Failed to update subscription",
                "message": str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Subscription update failed: {e}")
        return jsonify({
            "error": "Subscription update failed",
            "message": str(e)
        }), 500
