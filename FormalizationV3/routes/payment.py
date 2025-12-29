#!/usr/bin/env python3
"""
Payment Routes for RazorPay Integration - Phase 2
Handles payment creation, verification, and webhook processing
"""

import os
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from functools import wraps

from payment_manager import RazorPayManager, PaymentType

logger = logging.getLogger(__name__)

# Create payment blueprint
payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')

# Global variables for dependency injection
payment_manager = None
auth_middleware = None

def init_payment_routes(db_manager, credit_manager, auth_handler):
    """Initialize payment routes with dependencies"""
    global payment_manager, auth_middleware
    payment_manager = RazorPayManager(db_manager, credit_manager)
    auth_middleware = auth_handler
    logger.info("Payment routes initialized successfully")

def require_auth(f):
    """Authentication decorator for payment routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not auth_middleware:
            return jsonify({"error": "Authentication not configured"}), 500
            
        try:
            # Get user from authentication middleware
            user_info = auth_middleware.get_current_user(request)
            if not user_info:
                return jsonify({
                    "error": "Authentication required",
                    "message": "Please log in to access payment features"
                }), 401
                
            # Add user info to request context
            request.user = user_info
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Authentication check failed: {e}")
            return jsonify({"error": "Authentication failed"}), 401
    
    return decorated_function

@payment_bp.route('/packages', methods=['GET'])
@require_auth
def get_payment_packages():
    """Get available payment packages"""
    try:
        if not payment_manager:
            return jsonify({"error": "Payment system not initialized"}), 500
            
        packages = payment_manager.get_payment_packages()
        
        return jsonify({
            "success": True,
            "packages": packages,
            "currency": "INR",
            "message": "Available payment packages"
        })
        
    except Exception as e:
        logger.error(f"Failed to get payment packages: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to load payment packages"
        }), 500

@payment_bp.route('/create-order', methods=['POST'])
@require_auth
def create_payment_order():
    """Create a RazorPay order for payment"""
    try:
        if not payment_manager:
            return jsonify({"error": "Payment system not initialized"}), 500
            
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        # Validate required fields
        payment_type_str = data.get('payment_type')
        if not payment_type_str:
            return jsonify({"error": "Payment type is required"}), 400
            
        try:
            payment_type = PaymentType(payment_type_str)
        except ValueError:
            return jsonify({"error": "Invalid payment type"}), 400
            
        user_id = str(request.user.get('id'))
        metadata = {
            "user_email": request.user.get('email'),
            "created_via": "web_app",
            "timestamp": datetime.now().isoformat()
        }
        
        # Create payment order
        result = payment_manager.create_payment_order(
            user_id=user_id,
            payment_type=payment_type,
            metadata=metadata
        )
        
        if result['success']:
            logger.info(f"Payment order created for user {user_id}: {result['order_id']}")
            return jsonify(result)
        else:
            logger.error(f"Payment order creation failed for user {user_id}: {result.get('error')}")
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Create payment order error: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to create payment order"
        }), 500

@payment_bp.route('/verify', methods=['POST'])
@require_auth
def verify_payment():
    """Verify payment signature and process payment"""
    try:
        if not payment_manager:
            return jsonify({"error": "Payment system not initialized"}), 500
            
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        # Validate required fields
        required_fields = ['razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Verify payment
        result = payment_manager.verify_payment(
            razorpay_order_id=data['razorpay_order_id'],
            razorpay_payment_id=data['razorpay_payment_id'],
            razorpay_signature=data['razorpay_signature']
        )
        
        if result['success']:
            user_id = str(request.user.get('id'))
            logger.info(f"Payment verified successfully for user {user_id}: {result['order_id']}")
            
            return jsonify({
                "success": True,
                "message": result.get('message', 'Payment verified successfully'),
                "credits_added": result.get('credits_added', 0),
                "processing_tier": result.get('processing_tier'),
                "order_id": result.get('order_id')
            })
        else:
            logger.error(f"Payment verification failed: {result.get('error')}")
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        return jsonify({
            "success": False,
            "error": "Payment verification failed"
        }), 500

@payment_bp.route('/webhook', methods=['POST'])
def payment_webhook():
    """Handle RazorPay webhook notifications"""
    try:
        if not payment_manager:
            logger.error("Payment webhook received but payment system not initialized")
            return jsonify({"error": "Payment system not initialized"}), 500
            
        # Get webhook payload and signature
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-Razorpay-Signature', '')
        
        if not payload:
            logger.warning("Webhook received with empty payload")
            return jsonify({"error": "Empty payload"}), 400
            
        # Process webhook
        result = payment_manager.handle_webhook(payload, signature)
        
        if result['success']:
            logger.info(f"Webhook processed successfully: {result.get('processed', False)}")
            return jsonify({"status": "ok"}), 200
        else:
            logger.error(f"Webhook processing failed: {result.get('error')}")
            return jsonify({"error": result.get('error')}), 400
            
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return jsonify({"error": "Webhook processing failed"}), 500

@payment_bp.route('/history', methods=['GET'])
@require_auth
def get_payment_history():
    """Get user's payment history"""
    try:
        if not payment_manager:
            return jsonify({"error": "Payment system not initialized"}), 500
            
        user_id = str(request.user.get('id'))
        limit = request.args.get('limit', 10, type=int)
        
        # Validate limit
        if limit > 50:
            limit = 50
        elif limit < 1:
            limit = 10
            
        payments = payment_manager.get_user_payments(user_id, limit)
        
        return jsonify({
            "success": True,
            "payments": payments,
            "total_shown": len(payments),
            "user_id": user_id
        })
        
    except Exception as e:
        logger.error(f"Failed to get payment history: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to load payment history"
        }), 500

@payment_bp.route('/status/<order_id>', methods=['GET'])
@require_auth
def get_payment_status(order_id):
    """Get payment status by order ID"""
    try:
        if not payment_manager:
            return jsonify({"error": "Payment system not initialized"}), 500
            
        user_id = str(request.user.get('id'))
        
        # Get user's payment history to find the order
        payments = payment_manager.get_user_payments(user_id, 50)
        
        # Find the specific order
        order_payment = None
        for payment in payments:
            if payment['order_id'] == order_id:
                order_payment = payment
                break
                
        if not order_payment:
            return jsonify({
                "success": False,
                "error": "Payment order not found"
            }), 404
            
        return jsonify({
            "success": True,
            "order": order_payment,
            "message": f"Payment status: {order_payment['status']}"
        })
        
    except Exception as e:
        logger.error(f"Failed to get payment status: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get payment status"
        }), 500

@payment_bp.route('/queue-skip-check', methods=['GET'])
@require_auth
def check_queue_skip_availability():
    """Check if user can skip queue or needs to pay"""
    try:
        if not payment_manager:
            return jsonify({"error": "Payment system not initialized"}), 500
            
        user_id = str(request.user.get('id'))
        
        # Check if user can skip queue
        can_skip = payment_manager.credit_manager.can_skip_queue(user_id)
        
        # Get credit status for additional info
        try:
            user_id_int = int(user_id)
            credit_status = payment_manager.credit_manager.get_credit_status(user_id_int)
            
            return jsonify({
                "success": True,
                "can_skip_queue": can_skip,
                "processing_tier": credit_status.processing_tier.value,
                "premium_credits": credit_status.premium_credits,
                "trial_credits": credit_status.trial_credits,
                "queue_skip_price": 40,  # ₹40
                "message": "Queue skip available" if can_skip else "Payment required for queue skip"
            })
            
        except Exception as e:
            logger.warning(f"Failed to get detailed credit status: {e}")
            return jsonify({
                "success": True,
                "can_skip_queue": can_skip,
                "queue_skip_price": 40,
                "message": "Queue skip available" if can_skip else "Payment required for queue skip"
            })
            
    except Exception as e:
        logger.error(f"Failed to check queue skip availability: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to check queue skip availability"
        }), 500

@payment_bp.route('/analytics', methods=['GET'])
@require_auth
def get_payment_analytics():
    """Get payment analytics (admin only)"""
    try:
        if not payment_manager:
            return jsonify({"error": "Payment system not initialized"}), 500
            
        # Check if user is admin
        user_email = request.user.get('email', '')
        admin_emails = os.getenv('ADMIN_EMAILS', '').split(',')
        
        if user_email not in admin_emails:
            return jsonify({
                "success": False,
                "error": "Admin access required"
            }), 403
            
        days = request.args.get('days', 30, type=int)
        if days > 365:
            days = 365
        elif days < 1:
            days = 30
            
        analytics = payment_manager.credit_manager.get_revenue_analytics(days)
        
        return jsonify({
            "success": True,
            "analytics": analytics,
            "message": f"Revenue analytics for last {days} days"
        })
        
    except Exception as e:
        logger.error(f"Failed to get payment analytics: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to load payment analytics"
        }), 500
