#!/usr/bin/env python3
"""
RazorPay Payment Manager for HR ATS B2B SaaS
Handles payment processing, verification, and credit management integration
"""

import os
import json
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

import razorpay
from config import Config

logger = logging.getLogger(__name__)

class PaymentType(Enum):
    """Types of payments in the system"""
    QUEUE_SKIP = "queue_skip"
    CREDIT_PACKAGE_10 = "credit_package_10"
    CREDIT_PACKAGE_25 = "credit_package_25"
    ENTERPRISE_UPGRADE = "enterprise_upgrade"

class PaymentStatus(Enum):
    """Payment status tracking"""
    CREATED = "created"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class PaymentPackage:
    """Payment package configuration"""
    payment_type: PaymentType
    amount: int      # Amount in paisa (INR * 100)
    credits: int     # Credits to add upon successful payment
    name: str        # Display name
    description: str # Package description
    priority: bool = False  # Whether this gives priority processing

# Package definitions
PAYMENT_PACKAGES = {
    PaymentType.QUEUE_SKIP: PaymentPackage(
        payment_type=PaymentType.QUEUE_SKIP,
        amount=4000,  # ₹40
        credits=0,    # Instant processing, no credit addition
        name="Queue Skip",
        description="Skip the queue and get instant processing",
        priority=True
    ),
    PaymentType.CREDIT_PACKAGE_10: PaymentPackage(
        payment_type=PaymentType.CREDIT_PACKAGE_10,
        amount=30000,  # ₹300
        credits=10,
        name="10 Credits Package",
        description="10 premium credits for enhanced AI processing"
    ),
    PaymentType.CREDIT_PACKAGE_25: PaymentPackage(
        payment_type=PaymentType.CREDIT_PACKAGE_25,
        amount=65000,  # ₹650
        credits=25,
        name="25 Credits Package",
        description="25 premium credits with better value"
    ),
    PaymentType.ENTERPRISE_UPGRADE: PaymentPackage(
        payment_type=PaymentType.ENTERPRISE_UPGRADE,
        amount=500000,  # ₹5000
        credits=1000,
        name="Enterprise Package",
        description="Unlimited processing with enterprise features"
    )
}

@dataclass
class PaymentOrder:
    """Payment order tracking"""
    order_id: str
    razorpay_order_id: str
    user_id: str
    payment_type: PaymentType
    amount: int
    currency: str = "INR"
    status: PaymentStatus = PaymentStatus.CREATED
    created_at: datetime = None
    paid_at: Optional[datetime] = None
    razorpay_payment_id: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class RazorPayManager:
    """RazorPay integration manager"""
    
    def __init__(self, db_manager, credit_manager):
        """Initialize RazorPay client and dependencies"""
        self.config = Config()
        self.db_manager = db_manager
        self.credit_manager = credit_manager
        
        # Initialize RazorPay client
        key_id = os.getenv('RAZORPAY_KEY_ID')
        key_secret = os.getenv('RAZORPAY_KEY_SECRET')
        
        if not key_id or not key_secret:
            raise ValueError("RazorPay credentials not configured")
            
        self.client = razorpay.Client(auth=(key_id, key_secret))
        self.webhook_secret = os.getenv('RAZORPAY_WEBHOOK_SECRET', '')
        
        # Initialize orders storage
        self._initialize_payment_tables()
        
        logger.info("RazorPay Manager initialized successfully")
    
    def _initialize_payment_tables(self):
        """Create payment tracking tables if they don't exist"""
        try:
            cursor = self.db_manager.get_connection().cursor()
            
            # Payment orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payment_orders (
                    order_id TEXT PRIMARY KEY,
                    razorpay_order_id TEXT UNIQUE,
                    user_id TEXT NOT NULL,
                    payment_type TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    currency TEXT DEFAULT 'INR',
                    status TEXT DEFAULT 'created',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP,
                    razorpay_payment_id TEXT,
                    metadata TEXT
                )
            ''')
            
            # Payment transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payment_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    razorpay_payment_id TEXT,
                    amount INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    credits_added INTEGER DEFAULT 0,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    webhook_data TEXT,
                    FOREIGN KEY (order_id) REFERENCES payment_orders (order_id)
                )
            ''')
            
            # User privileges table for queue skip and special permissions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_privileges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    privilege_type TEXT NOT NULL,
                    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    payment_reference TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    UNIQUE(user_id, privilege_type, payment_reference)
                )
            ''')
            
            # Create indexes for performance and security
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_payment_orders_user_id ON payment_orders(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_payment_orders_razorpay_payment_id ON payment_orders(razorpay_payment_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_payment_transactions_order_id ON payment_transactions(order_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_privileges_user_id ON user_privileges(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_privileges_expires_at ON user_privileges(expires_at)')
            
            cursor.close()
            self.db_manager.get_connection().commit()
            
        except Exception as e:
            logger.error(f"Failed to initialize payment tables: {e}")
            raise
    
    def create_payment_order(self, user_id: str, payment_type: PaymentType, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a RazorPay order for payment"""
        try:
            package = PAYMENT_PACKAGES.get(payment_type)
            if not package:
                raise ValueError(f"Invalid payment type: {payment_type}")
            
            # Generate unique order ID
            order_id = f"hrATS_{user_id}_{payment_type.value}_{int(datetime.now().timestamp())}"
            
            # Create RazorPay order
            razorpay_order_data = {
                "amount": package.amount,
                "currency": "INR",
                "receipt": order_id,
                "notes": {
                    "user_id": user_id,
                    "payment_type": payment_type.value,
                    "credits": package.credits
                }
            }
            
            if metadata:
                razorpay_order_data["notes"].update(metadata)
            
            # Create order with RazorPay
            razorpay_order = self.client.order.create(razorpay_order_data)
            
            # Store order in database
            payment_order = PaymentOrder(
                order_id=order_id,
                razorpay_order_id=razorpay_order['id'],
                user_id=user_id,
                payment_type=payment_type,
                amount=package.amount
            )
            
            self._store_payment_order(payment_order, metadata)
            
            # Return order details for frontend
            return {
                "success": True,
                "order_id": order_id,
                "razorpay_order_id": razorpay_order['id'],
                "amount": package.amount,
                "currency": "INR",
                "package_info": {
                    "name": package.name,
                    "description": package.description,
                    "credits": package.credits,
                    "priority": package.priority
                },
                "key_id": os.getenv('RAZORPAY_KEY_ID')
            }
            
        except Exception as e:
            logger.error(f"Failed to create payment order: {e}")
            return {"success": False, "error": str(e)}
    
    def verify_payment(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str, user_id: str = None) -> Dict[str, Any]:
        """
        SECURE PAYMENT VERIFICATION WITH MULTIPLE LAYERS
        - RazorPay signature verification
        - Database consistency checks  
        - Anti-fraud validation
        - Idempotency protection
        """
        try:
            # Layer 1: RazorPay signature verification
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            
            # RazorPay signature verification - CRITICAL SECURITY CHECK
            self.client.utility.verify_payment_signature(params_dict)
            logger.info(f"RazorPay signature verified for payment {razorpay_payment_id}")
            
            # Layer 2: Database consistency checks
            payment_order = self._get_payment_order_by_razorpay_id(razorpay_order_id)
            if not payment_order:
                logger.error(f"Payment order not found for razorpay_order_id: {razorpay_order_id}")
                return {"success": False, "error": "Payment order not found"}
            
            # Layer 3: Anti-fraud validation
            if not self._validate_payment_integrity(payment_order, razorpay_payment_id, user_id):
                logger.error(f"Payment integrity validation failed for {razorpay_payment_id}")
                return {"success": False, "error": "Payment validation failed"}
            
            # Layer 4: Idempotency check - prevent double processing
            if payment_order['status'] == 'paid':
                logger.warning(f"Payment {razorpay_payment_id} already processed")
                return {
                    "success": True,
                    "message": "Payment already processed",
                    "order_id": payment_order['order_id'],
                    "duplicate": True
                }
            
            # Layer 5: Fetch and verify payment details from RazorPay
            try:
                razorpay_payment = self.client.payment.fetch(razorpay_payment_id)
                if not self._verify_razorpay_payment_details(razorpay_payment, payment_order):
                    return {"success": False, "error": "Payment details verification failed"}
            except Exception as e:
                logger.error(f"Failed to fetch payment details from RazorPay: {e}")
                return {"success": False, "error": "Payment verification failed"}
            
            # ATOMIC TRANSACTION: Update payment status and process credits
            result = self._process_verified_payment(payment_order, razorpay_payment_id, razorpay_payment)
            
            if result["success"]:
                logger.info(f"Payment {razorpay_payment_id} verified and processed successfully")
                return result
            else:
                logger.error(f"Failed to process verified payment: {result.get('error')}")
                return result
            
        except razorpay.errors.SignatureVerificationError as e:
            logger.error(f"RazorPay signature verification failed: {e}")
            return {"success": False, "error": "Invalid payment signature"}
        except Exception as e:
            logger.error(f"Payment verification failed: {e}")
            return {"success": False, "error": "Payment verification failed"}
    
    def _validate_payment_integrity(self, payment_order: Dict[str, Any], razorpay_payment_id: str, user_id: str = None) -> bool:
        """Validate payment integrity with anti-fraud checks"""
        try:
            # Check 1: User ID consistency
            if user_id and payment_order['user_id'] != user_id:
                logger.error(f"User ID mismatch: expected {payment_order['user_id']}, got {user_id}")
                return False
            
            # Check 2: Payment ID uniqueness across all orders
            cursor = self.db_manager.get_connection().cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM payment_orders 
                WHERE razorpay_payment_id = ? AND order_id != ?
            ''', (razorpay_payment_id, payment_order['order_id']))
            
            if cursor.fetchone()[0] > 0:
                logger.error(f"Payment ID {razorpay_payment_id} already used in another order")
                cursor.close()
                return False
            
            # Check 3: Order creation time (prevent old order replay)
            order_created = datetime.fromisoformat(payment_order['created_at'].replace('Z', '+00:00'))
            time_diff = datetime.now() - order_created
            if time_diff.total_seconds() > 3600:  # 1 hour limit
                logger.error(f"Order too old: {time_diff.total_seconds()} seconds")
                cursor.close()
                return False
            
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"Payment integrity validation error: {e}")
            return False
    
    def _verify_razorpay_payment_details(self, razorpay_payment: Dict[str, Any], payment_order: Dict[str, Any]) -> bool:
        """Verify payment details from RazorPay API"""
        try:
            # Verify payment status
            if razorpay_payment['status'] != 'captured':
                logger.error(f"Payment not captured: {razorpay_payment['status']}")
                return False
            
            # Verify amount matches
            if razorpay_payment['amount'] != payment_order['amount']:
                logger.error(f"Amount mismatch: RazorPay={razorpay_payment['amount']}, Order={payment_order['amount']}")
                return False
            
            # Verify currency
            if razorpay_payment['currency'] != 'INR':
                logger.error(f"Invalid currency: {razorpay_payment['currency']}")
                return False
            
            # Verify order ID matches
            if razorpay_payment['order_id'] != payment_order['razorpay_order_id']:
                logger.error(f"Order ID mismatch: RazorPay={razorpay_payment['order_id']}, DB={payment_order['razorpay_order_id']}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"RazorPay payment details verification failed: {e}")
            return False
    
    def _process_verified_payment(self, payment_order: Dict[str, Any], razorpay_payment_id: str, razorpay_payment: Dict[str, Any]) -> Dict[str, Any]:
        """Process verified payment in atomic transaction"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Update payment order status
            cursor.execute('''
                UPDATE payment_orders 
                SET status = 'paid', paid_at = ?, razorpay_payment_id = ?
                WHERE order_id = ?
            ''', (datetime.now(), razorpay_payment_id, payment_order['order_id']))
            
            # Verify the update
            if cursor.rowcount != 1:
                raise Exception("Failed to update payment order status")
            
            # Process payment based on type
            payment_type = PaymentType(payment_order['payment_type'])
            processing_result = self._process_successful_payment_atomic(
                payment_order, payment_type, cursor, razorpay_payment
            )
            
            if not processing_result["success"]:
                raise Exception(processing_result.get("error", "Payment processing failed"))
            
            # Commit transaction
            conn.commit()
            cursor.close()
            
            return {
                "success": True,
                "order_id": payment_order['order_id'],
                "payment_type": payment_type.value,
                "credits_added": processing_result.get('credits_added', 0),
                "processing_tier": processing_result.get('processing_tier'),
                "message": processing_result.get('message', 'Payment processed successfully'),
                "razorpay_payment_id": razorpay_payment_id
            }
            
        except Exception as e:
            # Rollback transaction
            conn.rollback()
            cursor.close()
            logger.error(f"Payment processing failed, transaction rolled back: {e}")
            return {"success": False, "error": str(e)}
    
    def _process_successful_payment_atomic(self, payment_order: Dict[str, Any], payment_type: PaymentType, 
                                         cursor, razorpay_payment: Dict[str, Any]) -> Dict[str, Any]:
        """Process successful payment atomically within transaction"""
        try:
            user_id = payment_order['user_id']
            package = PAYMENT_PACKAGES[payment_type]
            
            result = {
                "success": True,
                "credits_added": 0,
                "processing_tier": "free_trial",
                "message": "Payment processed"
            }
            
            if payment_type == PaymentType.QUEUE_SKIP:
                # Queue skip - grant immediate processing privilege
                cursor.execute('''
                    INSERT OR REPLACE INTO user_privileges 
                    (user_id, privilege_type, granted_at, expires_at, payment_reference)
                    VALUES (?, 'queue_skip', ?, ?, ?)
                ''', (
                    user_id, 
                    datetime.now(), 
                    datetime.now() + timedelta(hours=1),  # 1 hour queue skip
                    payment_order['order_id']
                ))
                
                result.update({
                    "processing_tier": "queue_skip",
                    "message": "Queue skip activated - 1 hour instant processing",
                    "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
                })
                
            else:
                # Credit package - add premium credits
                credits_to_add = package.credits
                
                # Get current premium credits
                cursor.execute('SELECT premium_credits FROM user_credits WHERE user_id = ?', (user_id,))
                current_result = cursor.fetchone()
                current_premium = current_result[0] if current_result else 0
                
                new_premium = current_premium + credits_to_add
                
                # Update premium credits atomically
                cursor.execute('''
                    UPDATE user_credits 
                    SET premium_credits = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (new_premium, user_id))
                
                if cursor.rowcount != 1:
                    raise Exception("Failed to update user credits")
                
                # Log credit transaction
                cursor.execute('''
                    INSERT INTO credit_transactions 
                    (user_id, transaction_type, credit_type, amount, balance_after, description, payment_reference, timestamp)
                    VALUES (?, 'add', 'premium', ?, ?, ?, ?, ?)
                ''', (
                    user_id, credits_to_add, new_premium, 
                    f"Payment: {package.name}", payment_order['order_id'], datetime.now()
                ))
                
                result.update({
                    "credits_added": credits_to_add,
                    "processing_tier": "premium_instant",
                    "message": f"Added {credits_to_add} premium credits",
                    "new_balance": new_premium
                })
            
            # Record payment transaction
            cursor.execute('''
                INSERT INTO payment_transactions 
                (order_id, razorpay_payment_id, amount, status, credits_added, processed_at, webhook_data)
                VALUES (?, ?, ?, 'completed', ?, ?, ?)
            ''', (
                payment_order['order_id'], 
                razorpay_payment.get('id'),
                payment_order['amount'], 
                result.get('credits_added', 0),
                datetime.now(),
                json.dumps(razorpay_payment)
            ))
            
            return result
            
        except Exception as e:
            logger.error(f"Atomic payment processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    def handle_webhook(self, payload: str, signature: str) -> Dict[str, Any]:
        """Handle RazorPay webhook notifications"""
        try:
            # Verify webhook signature if secret is configured
            if self.webhook_secret:
                expected_signature = hmac.new(
                    self.webhook_secret.encode('utf-8'),
                    payload.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                if not hmac.compare_digest(signature, expected_signature):
                    logger.warning("Webhook signature verification failed")
                    return {"success": False, "error": "Invalid signature"}
            
            # Parse webhook data
            webhook_data = json.loads(payload)
            event = webhook_data.get('event')
            
            if event == 'payment.captured':
                payment_data = webhook_data['payload']['payment']['entity']
                order_id = payment_data['order_id']
                payment_id = payment_data['id']
                
                # Process webhook payment
                result = self._process_webhook_payment(order_id, payment_id, webhook_data)
                return {"success": True, "processed": result}
            
            logger.info(f"Unhandled webhook event: {event}")
            return {"success": True, "processed": False}
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _store_payment_order(self, payment_order: PaymentOrder, metadata: Dict[str, Any] = None):
        """Store payment order in database"""
        cursor = self.db_manager.get_connection().cursor()
        cursor.execute('''
            INSERT INTO payment_orders 
            (order_id, razorpay_order_id, user_id, payment_type, amount, currency, status, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            payment_order.order_id,
            payment_order.razorpay_order_id,
            payment_order.user_id,
            payment_order.payment_type.value,
            payment_order.amount,
            payment_order.currency,
            payment_order.status.value,
            payment_order.created_at,
            json.dumps(metadata) if metadata else None
        ))
        cursor.close()
        self.db_manager.get_connection().commit()
    
    def _get_payment_order_by_razorpay_id(self, razorpay_order_id: str) -> Optional[Dict[str, Any]]:
        """Get payment order by RazorPay order ID"""
        cursor = self.db_manager.get_connection().cursor()
        cursor.execute('''
            SELECT * FROM payment_orders WHERE razorpay_order_id = ?
        ''', (razorpay_order_id,))
        
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, result))
        return None
    
    def _update_payment_status(self, order_id: str, status: PaymentStatus, razorpay_payment_id: str = None):
        """Update payment order status"""
        cursor = self.db_manager.get_connection().cursor()
        
        if status == PaymentStatus.PAID:
            cursor.execute('''
                UPDATE payment_orders 
                SET status = ?, paid_at = ?, razorpay_payment_id = ?
                WHERE order_id = ?
            ''', (status.value, datetime.now(), razorpay_payment_id, order_id))
        else:
            cursor.execute('''
                UPDATE payment_orders 
                SET status = ?
                WHERE order_id = ?
            ''', (status.value, order_id))
        
        cursor.close()
        self.db_manager.get_connection().commit()
    
    def _process_successful_payment(self, payment_order: Dict[str, Any], payment_type: PaymentType) -> Dict[str, Any]:
        """Process successful payment and update credits"""
        user_id = payment_order['user_id']
        package = PAYMENT_PACKAGES[payment_type]
        
        result = {
            "credits_added": 0,
            "processing_tier": "free_trial",
            "message": "Payment processed"
        }
        
        if payment_type == PaymentType.QUEUE_SKIP:
            # Queue skip - grant immediate processing
            result.update({
                "processing_tier": "queue_skip",
                "message": "Queue skip activated - processing immediately",
                "priority_processing": True
            })
            
            # Record the queue skip transaction
            self._record_payment_transaction(
                payment_order['order_id'],
                payment_order['razorpay_payment_id'],
                payment_order['amount'],
                "queue_skip",
                0
            )
            
        else:
            # Credit package - add credits to user account
            credits_added = self.credit_manager.add_premium_credits(
                user_id, 
                package.credits,
                f"Payment: {package.name}"
            )
            
            result.update({
                "credits_added": credits_added,
                "processing_tier": "premium_instant",
                "message": f"Added {credits_added} premium credits"
            })
            
            # Record the credit transaction
            self._record_payment_transaction(
                payment_order['order_id'],
                payment_order['razorpay_payment_id'],
                payment_order['amount'],
                "completed",
                credits_added
            )
        
        # Update sales intelligence
        self._update_sales_intelligence(user_id, payment_type, payment_order['amount'])
        
        return result
    
    def _process_webhook_payment(self, razorpay_order_id: str, razorpay_payment_id: str, webhook_data: Dict[str, Any]) -> bool:
        """Process payment from webhook notification"""
        try:
            payment_order = self._get_payment_order_by_razorpay_id(razorpay_order_id)
            if not payment_order:
                logger.warning(f"Webhook: Payment order not found for {razorpay_order_id}")
                return False
            
            if payment_order['status'] == 'paid':
                logger.info(f"Webhook: Payment already processed for {razorpay_order_id}")
                return True
            
            # Update payment status
            self._update_payment_status(payment_order['order_id'], PaymentStatus.PAID, razorpay_payment_id)
            
            # Process payment
            payment_type = PaymentType(payment_order['payment_type'])
            self._process_successful_payment(payment_order, payment_type)
            
            logger.info(f"Webhook: Successfully processed payment {razorpay_payment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Webhook payment processing failed: {e}")
            return False
    
    def _record_payment_transaction(self, order_id: str, razorpay_payment_id: str, amount: int, status: str, credits_added: int):
        """Record payment transaction for tracking"""
        cursor = self.db_manager.get_connection().cursor()
        cursor.execute('''
            INSERT INTO payment_transactions 
            (order_id, razorpay_payment_id, amount, status, credits_added, processed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (order_id, razorpay_payment_id, amount, status, credits_added, datetime.now()))
        cursor.close()
        self.db_manager.get_connection().commit()
    
    def _update_sales_intelligence(self, user_id: str, payment_type: PaymentType, amount: int):
        """Update sales intelligence based on payment behavior"""
        try:
            # Update user payment behavior
            payment_data = {
                "payment_type": payment_type.value,
                "amount": amount,
                "timestamp": datetime.now().isoformat()
            }
            
            # Increase lead score based on payment
            score_increase = 50  # Base increase for any payment
            if payment_type == PaymentType.ENTERPRISE_UPGRADE:
                score_increase = 200  # High value for enterprise
            elif payment_type in [PaymentType.CREDIT_PACKAGE_10, PaymentType.CREDIT_PACKAGE_25]:
                score_increase = 100  # Medium value for credit packages
            
            # Update through credit manager's sales intelligence
            if hasattr(self.credit_manager, 'update_sales_intelligence'):
                self.credit_manager.update_sales_intelligence(
                    user_id, 
                    {"payment_behavior": payment_data, "lead_score_increase": score_increase}
                )
                
        except Exception as e:
            logger.error(f"Failed to update sales intelligence: {e}")
    
    def get_payment_packages(self) -> List[Dict[str, Any]]:
        """Get available payment packages for frontend"""
        packages = []
        for payment_type, package in PAYMENT_PACKAGES.items():
            packages.append({
                "type": payment_type.value,
                "name": package.name,
                "description": package.description,
                "amount": package.amount,
                "amount_inr": package.amount / 100,  # Convert paisa to rupees
                "credits": package.credits,
                "priority": package.priority
            })
        return packages
    
    def get_user_payments(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's payment history"""
        cursor = self.db_manager.get_connection().cursor()
        cursor.execute('''
            SELECT * FROM payment_orders 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        results = cursor.fetchall()
        cursor.close()
        
        payments = []
        if results:
            columns = [description[0] for description in cursor.description]
            for result in results:
                payment = dict(zip(columns, result))
                # Convert amount to rupees for display
                payment['amount_inr'] = payment['amount'] / 100
                payments.append(payment)
        
        return payments
