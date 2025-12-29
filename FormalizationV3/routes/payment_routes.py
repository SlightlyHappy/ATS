"""
Payment and credit system routes - extracted from monolithic app.py
Handles: credit management, payment processing, subscription management, queue operations
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

# Create blueprint
payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')

# Global dependencies (will be injected during initialization)
db_manager = None
auth_middleware = None
credit_manager = None
queue_manager = None
payment_manager = None
railway_db = None

def init_payment_routes(database_manager, auth_mid, credit_mgr=None, queue_mgr=None,
                       payment_mgr=None, railway_database=None):
    """Initialize payment routes with dependencies"""
    global db_manager, auth_middleware, credit_manager, queue_manager
    global payment_manager, railway_db
    
    db_manager = database_manager
    auth_middleware = auth_mid
    credit_manager = credit_mgr
    queue_manager = queue_mgr
    payment_manager = payment_mgr
    railway_db = railway_database
    
    logger.info("✅ Payment routes initialized with all dependencies")

@payment_bp.route('/credits/status', methods=['GET'])
def get_credit_status():
    """Get current user's credit status"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
        
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        if not credit_manager:
            return jsonify({"error": "Credit system not available"}), 500
        
        user_id = user['user_id']
        credit_status = credit_manager.check_user_credits(user_id)
        
        response_data = {
            "success": True,
            "credit_status": {
                "user_id": user_id,
                "trial_credits": credit_status.trial_credits,
                "premium_credits": credit_status.premium_credits,
                "credits_remaining": credit_status.credits_remaining,
                "total_used": credit_status.total_used,
                "processing_tier": credit_status.processing_tier.value if credit_status.processing_tier else 'trial',
                "can_process": credit_status.can_process,
                "trial_exhausted": credit_status.credits_remaining <= 0 and not user.get('is_premium')
            }
        }
        
        # Add usage breakdown if available
        if hasattr(credit_status, 'usage_breakdown'):
            response_data["usage_breakdown"] = credit_status.usage_breakdown
        
        # Add subscription info if premium user
        if user.get('is_premium'):
            try:
                subscription_info = get_subscription_info(user_id)
                response_data["subscription"] = subscription_info
            except Exception as sub_error:
                logger.warning(f"Failed to get subscription info: {sub_error}")
        
        # Add monetization options if trial exhausted
        if response_data["credit_status"]["trial_exhausted"]:
            response_data["monetization_options"] = get_premium_options()
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Get credit status error: {e}")
        return jsonify({"error": "Failed to get credit status"}), 500

@payment_bp.route('/plans', methods=['GET'])
def get_pricing_plans():
    """Get available pricing plans"""
    try:
        plans = [
            {
                "id": "professional",
                "name": "Professional",
                "description": "Perfect for recruiters and small teams",
                "price_monthly": 2500,
                "price_yearly": 25000,
                "credits_included": 100,
                "features": [
                    "Advanced AI Resume Analysis",
                    "Batch Processing (up to 20 resumes)",
                    "Priority Queue Processing",
                    "Detailed Analytics",
                    "Email Support",
                    "Export to PDF/CSV"
                ],
                "popular": True
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "description": "For large organizations and high-volume usage",
                "price_monthly": 7500,
                "price_yearly": 75000,
                "credits_included": 500,
                "features": [
                    "All Professional Features",
                    "Custom AI Models",
                    "API Access",
                    "Unlimited Batch Processing",
                    "White-label Options",
                    "Dedicated Support",
                    "Custom Integrations",
                    "Advanced Analytics & Reporting"
                ],
                "enterprise": True
            },
            {
                "id": "pay_per_use",
                "name": "Pay Per Use",
                "description": "Flexible credit packs for occasional usage",
                "credits_options": [
                    {"credits": 10, "price": 500, "per_credit": 50},
                    {"credits": 25, "price": 1000, "per_credit": 40},
                    {"credits": 50, "price": 1750, "per_credit": 35},
                    {"credits": 100, "price": 3000, "per_credit": 30}
                ],
                "features": [
                    "No Monthly Commitment",
                    "Credits Never Expire",
                    "Same Advanced AI Analysis",
                    "Basic Support"
                ]
            }
        ]
        
        return jsonify({
            "success": True,
            "plans": plans,
            "currency": "INR",
            "trial_credits": 10,
            "features_comparison": {
                "ai_analysis": "All plans include advanced AI analysis",
                "batch_processing": "Professional: 20 resumes, Enterprise: Unlimited",
                "queue_priority": "Professional & Enterprise get priority processing",
                "support": "Professional: Email, Enterprise: Dedicated"
            }
        })
        
    except Exception as e:
        logger.error(f"Get pricing plans error: {e}")
        return jsonify({"error": "Failed to get pricing plans"}), 500

@payment_bp.route('/purchase', methods=['POST'])
def purchase_credits():
    """Purchase credits or subscription"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
        
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        if not payment_manager:
            return jsonify({"error": "Payment system not available"}), 500
        
        data = request.get_json() or {}
        purchase_type = data.get('type')  # 'subscription', 'credits'
        plan_id = data.get('plan_id')
        billing_cycle = data.get('billing_cycle', 'monthly')  # 'monthly', 'yearly'
        
        user_id = user['user_id']
        
        if purchase_type == 'subscription':
            result = process_subscription_purchase(user_id, plan_id, billing_cycle, data)
        elif purchase_type == 'credits':
            credit_amount = data.get('credits', 0)
            result = process_credit_purchase(user_id, credit_amount, data)
        else:
            return jsonify({"error": "Invalid purchase type"}), 400
        
        if result.success:
            return jsonify({
                "success": True,
                "message": "Purchase initiated successfully",
                "payment_url": result.payment_url,
                "order_id": result.order_id,
                "amount": result.amount
            })
        else:
            return jsonify({
                "success": False,
                "error": result.error_message
            }), 400
            
    except Exception as e:
        logger.error(f"Purchase error: {e}")
        return jsonify({"error": "Purchase failed"}), 500

@payment_bp.route('/webhook', methods=['POST'])
def payment_webhook():
    """Handle payment gateway webhooks"""
    try:
        if not payment_manager:
            return jsonify({"error": "Payment system not available"}), 500
        
        # Verify webhook signature
        signature = request.headers.get('X-Razorpay-Signature') or request.headers.get('X-Payment-Signature')
        if not payment_manager.verify_webhook_signature(request.data, signature):
            logger.warning("Invalid webhook signature")
            return jsonify({"error": "Invalid signature"}), 400
        
        webhook_data = request.get_json()
        event_type = webhook_data.get('event')
        
        if event_type == 'payment.captured':
            result = handle_payment_success(webhook_data)
        elif event_type == 'payment.failed':
            result = handle_payment_failure(webhook_data)
        elif event_type == 'subscription.charged':
            result = handle_subscription_renewal(webhook_data)
        else:
            logger.info(f"Unhandled webhook event: {event_type}")
            return jsonify({"status": "ignored"})
        
        if result.success:
            return jsonify({"status": "processed"})
        else:
            logger.error(f"Webhook processing failed: {result.error_message}")
            return jsonify({"error": "Processing failed"}), 500
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": "Webhook processing failed"}), 500

@payment_bp.route('/queue-skip', methods=['POST'])
def skip_queue():
    """Skip queue for instant processing - Premium feature"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
        
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        if not queue_manager:
            return jsonify({"error": "Queue system not available"}), 500
        
        data = request.get_json() or {}
        request_id = data.get('request_id')
        
        if not request_id:
            return jsonify({"error": "Request ID is required"}), 400
        
        user_id = user['user_id']
        
        # Check if user has pending request in queue
        queue_request = queue_manager.get_request_status(request_id)
        if not queue_request or queue_request.user_id != str(user_id):
            return jsonify({"error": "Queue request not found"}), 404
        
        # Process payment for queue skip (₹40)
        skip_price = 40  # INR
        
        if payment_manager:
            payment_result = payment_manager.create_instant_payment(
                user_id, skip_price, "queue_skip", {
                    "request_id": request_id,
                    "feature": "queue_skip"
                }
            )
            
            if payment_result.success:
                return jsonify({
                    "success": True,
                    "message": "Queue skip payment initiated",
                    "payment_url": payment_result.payment_url,
                    "amount": skip_price,
                    "request_id": request_id
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Payment initiation failed"
                }), 400
        else:
            # Process queue skip without payment (for testing)
            skip_result = queue_manager.skip_queue(request_id, str(user_id))
            
            if skip_result.success:
                return jsonify({
                    "success": True,
                    "message": "Queue skipped successfully",
                    "processing_status": "priority_processing"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": skip_result.error_message
                }), 400
            
    except Exception as e:
        logger.error(f"Queue skip error: {e}")
        return jsonify({"error": "Queue skip failed"}), 500

@payment_bp.route('/history', methods=['GET'])
def get_payment_history():
    """Get user's payment history"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
        
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = user['user_id']
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)
        
        if not railway_db:
            return jsonify({"error": "Database not available"}), 500
        
        # Get payment history
        offset = (page - 1) * per_page
        
        payments = railway_db.execute_read("""
            SELECT 
                transaction_id, amount, currency, status, payment_method,
                purchase_type, purchase_details, created_at, updated_at
            FROM payment_transactions 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
        """, (user_id, per_page, offset))
        
        # Get total count
        total_count = railway_db.execute_read(
            "SELECT COUNT(*) as count FROM payment_transactions WHERE user_id = %s",
            (user_id,)
        )
        total_payments = total_count[0]['count'] if total_count else 0
        
        # Get credit usage history
        credit_history = railway_db.execute_read("""
            SELECT 
                action, credits_used, operation_type, details, created_at
            FROM credit_usage_log 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 10
        """, (user_id,))
        
        return jsonify({
            "success": True,
            "payments": payments or [],
            "credit_history": credit_history or [],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_payments,
                "pages": (total_payments + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"Get payment history error: {e}")
        return jsonify({"error": "Failed to get payment history"}), 500

@payment_bp.route('/refund', methods=['POST'])
def request_refund():
    """Request refund for a payment"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
        
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json() or {}
        transaction_id = data.get('transaction_id')
        reason = data.get('reason', '').strip()
        
        if not transaction_id:
            return jsonify({"error": "Transaction ID is required"}), 400
        
        if not reason:
            return jsonify({"error": "Refund reason is required"}), 400
        
        user_id = user['user_id']
        
        # Verify transaction belongs to user
        transaction = railway_db.execute_read("""
            SELECT transaction_id, amount, status, created_at
            FROM payment_transactions 
            WHERE transaction_id = %s AND user_id = %s
        """, (transaction_id, user_id))
        
        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404
        
        transaction_data = transaction[0]
        
        # Check if refund is possible (within 30 days and successful payment)
        payment_date = transaction_data['created_at']
        days_ago = (datetime.utcnow() - payment_date).days
        
        if days_ago > 30:
            return jsonify({
                "error": "Refund requests are only accepted within 30 days of payment"
            }), 400
        
        if transaction_data['status'] != 'completed':
            return jsonify({
                "error": "Refund can only be requested for completed payments"
            }), 400
        
        # Create refund request
        refund_id = f"refund_{transaction_id}_{int(datetime.utcnow().timestamp())}"
        
        railway_db.execute_write("""
            INSERT INTO refund_requests (
                refund_id, transaction_id, user_id, amount, reason, 
                status, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            refund_id, transaction_id, user_id, transaction_data['amount'],
            reason, 'pending', datetime.utcnow()
        ))
        
        # Log the refund request
        log_payment_activity(user_id, 'refund_requested', {
            'transaction_id': transaction_id,
            'refund_id': refund_id,
            'reason': reason
        })
        
        return jsonify({
            "success": True,
            "message": "Refund request submitted successfully",
            "refund_id": refund_id,
            "processing_time": "3-5 business days"
        })
        
    except Exception as e:
        logger.error(f"Refund request error: {e}")
        return jsonify({"error": "Refund request failed"}), 500

# Helper functions

def get_premium_options():
    """Get premium monetization options"""
    return {
        "trial_exhausted": True,
        "recommended_plan": "Professional",
        "quick_options": [
            {
                "type": "credits",
                "name": "10 Credits",
                "price": 500,
                "description": "Perfect for trying premium features"
            },
            {
                "type": "subscription",
                "name": "Professional Monthly",
                "price": 2500,
                "description": "100 credits + premium features"
            }
        ],
        "benefits": [
            "Advanced AI Analysis",
            "Batch Processing",
            "Priority Queue",
            "Detailed Reports"
        ]
    }

def get_subscription_info(user_id):
    """Get user's subscription information"""
    try:
        if railway_db:
            subscription = railway_db.execute_read("""
                SELECT 
                    subscription_id, plan_id, status, current_period_start,
                    current_period_end, billing_cycle, amount
                FROM user_subscriptions 
                WHERE user_id = %s AND status = 'active'
                ORDER BY created_at DESC 
                LIMIT 1
            """, (user_id,))
            
            return subscription[0] if subscription else None
    except Exception as e:
        logger.error(f"Failed to get subscription info: {e}")
        return None

def process_subscription_purchase(user_id, plan_id, billing_cycle, data):
    """Process subscription purchase"""
    try:
        # This would integrate with your payment processor
        # For now, return a mock result
        class MockResult:
            def __init__(self):
                self.success = True
                self.payment_url = "https://payment-gateway.example.com/pay/123"
                self.order_id = f"order_{int(datetime.utcnow().timestamp())}"
                self.amount = 2500 if plan_id == "professional" else 7500
                
        return MockResult()
    except Exception as e:
        logger.error(f"Subscription purchase error: {e}")
        class ErrorResult:
            def __init__(self, error):
                self.success = False
                self.error_message = str(error)
        return ErrorResult(e)

def process_credit_purchase(user_id, credit_amount, data):
    """Process credit purchase"""
    try:
        # Calculate price based on credit amount
        price_per_credit = 50  # Base price
        if credit_amount >= 25:
            price_per_credit = 40
        elif credit_amount >= 50:
            price_per_credit = 35
        elif credit_amount >= 100:
            price_per_credit = 30
            
        total_amount = credit_amount * price_per_credit
        
        class MockResult:
            def __init__(self):
                self.success = True
                self.payment_url = f"https://payment-gateway.example.com/pay/credits_{int(datetime.utcnow().timestamp())}"
                self.order_id = f"credits_{user_id}_{int(datetime.utcnow().timestamp())}"
                self.amount = total_amount
                
        return MockResult()
    except Exception as e:
        logger.error(f"Credit purchase error: {e}")
        class ErrorResult:
            def __init__(self, error):
                self.success = False
                self.error_message = str(error)
        return ErrorResult(e)

def handle_payment_success(webhook_data):
    """Handle successful payment webhook"""
    try:
        payment_data = webhook_data.get('payload', {}).get('payment', {})
        order_id = payment_data.get('order_id')
        amount = payment_data.get('amount', 0) / 100  # Convert from paise to rupees
        
        # Update payment transaction status
        if railway_db:
            railway_db.execute_write("""
                UPDATE payment_transactions 
                SET status = 'completed', updated_at = %s 
                WHERE order_id = %s
            """, (datetime.utcnow(), order_id))
            
            # Get transaction details
            transaction = railway_db.execute_read("""
                SELECT user_id, purchase_type, purchase_details
                FROM payment_transactions 
                WHERE order_id = %s
            """, (order_id,))
            
            if transaction:
                user_id = transaction[0]['user_id']
                purchase_type = transaction[0]['purchase_type']
                
                # Process based on purchase type
                if purchase_type == 'credits' and credit_manager:
                    credit_amount = json.loads(transaction[0]['purchase_details']).get('credits', 0)
                    credit_manager.add_premium_credits(user_id, credit_amount, "purchase")
                elif purchase_type == 'subscription':
                    # Activate subscription
                    activate_subscription(user_id, transaction[0]['purchase_details'])
        
        class SuccessResult:
            def __init__(self):
                self.success = True
                
        return SuccessResult()
        
    except Exception as e:
        logger.error(f"Payment success handling error: {e}")
        class ErrorResult:
            def __init__(self, error):
                self.success = False
                self.error_message = str(error)
        return ErrorResult(e)

def handle_payment_failure(webhook_data):
    """Handle failed payment webhook"""
    try:
        payment_data = webhook_data.get('payload', {}).get('payment', {})
        order_id = payment_data.get('order_id')
        
        # Update payment transaction status
        if railway_db:
            railway_db.execute_write("""
                UPDATE payment_transactions 
                SET status = 'failed', updated_at = %s 
                WHERE order_id = %s
            """, (datetime.utcnow(), order_id))
        
        class SuccessResult:
            def __init__(self):
                self.success = True
                
        return SuccessResult()
        
    except Exception as e:
        logger.error(f"Payment failure handling error: {e}")
        class ErrorResult:
            def __init__(self, error):
                self.success = False
                self.error_message = str(error)
        return ErrorResult(e)

def handle_subscription_renewal(webhook_data):
    """Handle subscription renewal webhook"""
    try:
        # Process subscription renewal
        # This would update subscription status and add credits
        
        class SuccessResult:
            def __init__(self):
                self.success = True
                
        return SuccessResult()
        
    except Exception as e:
        logger.error(f"Subscription renewal handling error: {e}")
        class ErrorResult:
            def __init__(self, error):
                self.success = False
                self.error_message = str(error)
        return ErrorResult(e)

def activate_subscription(user_id, purchase_details):
    """Activate user subscription"""
    try:
        if railway_db:
            details = json.loads(purchase_details)
            plan_id = details.get('plan_id')
            billing_cycle = details.get('billing_cycle', 'monthly')
            
            # Calculate subscription period
            start_date = datetime.utcnow()
            if billing_cycle == 'yearly':
                end_date = start_date + timedelta(days=365)
            else:
                end_date = start_date + timedelta(days=30)
            
            # Create subscription record
            railway_db.execute_write("""
                INSERT INTO user_subscriptions (
                    user_id, plan_id, status, current_period_start,
                    current_period_end, billing_cycle, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, plan_id, 'active', start_date, end_date, billing_cycle, datetime.utcnow()))
            
            # Update user to premium
            railway_db.execute_write("""
                UPDATE users 
                SET is_premium = true, subscription_plan = %s 
                WHERE user_id = %s
            """, (plan_id, user_id))
            
            # Add subscription credits
            if credit_manager:
                credits_to_add = 100 if plan_id == 'professional' else 500
                credit_manager.add_premium_credits(user_id, credits_to_add, "subscription_activation")
                
    except Exception as e:
        logger.error(f"Subscription activation error: {e}")

def log_payment_activity(user_id, action, details):
    """Log payment-related activity"""
    try:
        if railway_db:
            railway_db.execute_write("""
                INSERT INTO user_activity_log (user_id, action, details, created_at)
                VALUES (%s, %s, %s, %s)
            """, (user_id, action, json.dumps(details), datetime.utcnow()))
    except Exception as e:
        logger.warning(f"Failed to log payment activity: {e}")
