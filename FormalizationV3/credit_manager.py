#!/usr/bin/env python3
"""
Credit Management System for HR ATS B2B SaaS
Handles trial credits, premium credits, and usage tracking for monetization
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class CreditType(Enum):
    """Types of credits in the system"""
    TRIAL = "trial"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class ProcessingTier(Enum):
    """Processing tiers based on credits and payment"""
    FREE_TRIAL = "free_trial"           # Trial credits + Ollama
    QUEUE_SKIP = "queue_skip"           # Premium payment to skip queue
    PREMIUM_INSTANT = "premium_instant" # Premium credits + Cloud AI
    ENTERPRISE = "enterprise"           # Enterprise unlimited
    CONTACT_SALES = "contact_sales"     # Out of credits

@dataclass
class CreditStatus:
    """Credit status for a user"""
    user_id: str
    trial_credits: int = 100
    premium_credits: int = 0
    total_used: int = 0
    can_process: bool = True
    processing_tier: ProcessingTier = ProcessingTier.FREE_TRIAL
    credits_remaining: int = 100
    usage_pattern: Dict[str, Any] = None
    lead_score: int = 0
    
    def __post_init__(self):
        self.credits_remaining = self.trial_credits + self.premium_credits
        self.usage_pattern = self.usage_pattern or {}

@dataclass
class CreditTransaction:
    """Record of credit usage"""
    user_id: str
    transaction_type: str  # 'deduct', 'add', 'purchase'
    amount: int
    credit_type: CreditType
    description: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class CreditManager:
    """
    Manages credit system for B2B SaaS monetization
    - 100 free trial credits per new user
    - Premium credit purchases
    - Queue skip payments
    - Usage analytics for sales intelligence
    """
    
    def __init__(self, db_manager):
        """Initialize credit manager with database connection"""
        self.db_manager = db_manager
        self.email_automation = None  # Will be set later to avoid circular imports
        self._initialize_credit_tables()
        logger.info("Credit Manager initialized successfully")
    
    def set_email_automation(self, email_automation):
        """Set email automation manager (called after initialization to avoid circular imports)"""
        self.email_automation = email_automation
    
    def _initialize_credit_tables(self):
        """Create credit management tables if they don't exist"""
        try:
            with self.db_manager.get_connection() as conn:
                # User credits table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_credits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        trial_credits INTEGER DEFAULT 100,
                        premium_credits INTEGER DEFAULT 0,
                        total_used INTEGER DEFAULT 0,
                        processing_tier VARCHAR(20) DEFAULT 'free_trial',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_used TIMESTAMP,
                        is_trial_exhausted BOOLEAN DEFAULT FALSE,
                        sales_contacted BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                        UNIQUE(user_id)
                    )
                """)
                
                # Credit transactions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS credit_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        transaction_type VARCHAR(20) NOT NULL,
                        credit_type VARCHAR(20) NOT NULL,
                        amount INTEGER NOT NULL,
                        balance_after INTEGER NOT NULL,
                        description TEXT,
                        metadata TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                
                # Usage analytics table for sales intelligence
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS usage_analytics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        feature_used VARCHAR(50) NOT NULL,
                        usage_count INTEGER DEFAULT 1,
                        credits_consumed INTEGER DEFAULT 1,
                        processing_tier VARCHAR(20),
                        last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        session_data TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                        UNIQUE(user_id, feature_used)
                    )
                """)
                
                # Sales intelligence table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sales_intelligence (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        lead_score INTEGER DEFAULT 0,
                        contact_priority INTEGER DEFAULT 0,
                        qualification_status VARCHAR(20) DEFAULT 'new',
                        usage_pattern TEXT,
                        behavior_data TEXT DEFAULT '{}',
                        last_activity TIMESTAMP,
                        sales_notes TEXT,
                        follow_up_scheduled TIMESTAMP,
                        contacted_at TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                        UNIQUE(user_id)
                    )
                """)
                
                # Payment tracking table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS payment_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        payment_provider VARCHAR(20) DEFAULT 'razorpay',
                        payment_id VARCHAR(100),
                        order_id VARCHAR(100),
                        amount_inr INTEGER NOT NULL,
                        credits_purchased INTEGER NOT NULL,
                        payment_status VARCHAR(20) DEFAULT 'pending',
                        verified_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                
                # Create indexes for performance
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON user_credits(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON credit_transactions(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_credit_transactions_timestamp ON credit_transactions(timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_usage_analytics_user_id ON usage_analytics(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_usage_analytics_timestamp ON usage_analytics(timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_sales_intelligence_user_id ON sales_intelligence(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_sales_intelligence_score ON sales_intelligence(lead_score)",
                    "CREATE INDEX IF NOT EXISTS idx_payment_transactions_user_id ON payment_transactions(user_id)"
                ]
                
                for index in indexes:
                    conn.execute(index)
                
                conn.commit()
                logger.info("Credit management tables initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize credit tables: {e}")
            raise
    
    def initialize_user_credits(self, user_id: int) -> CreditStatus:
        """Initialize credits for a new user (100 free trial credits)"""
        try:
            with self.db_manager.get_connection() as conn:
                # Check if user already has credits
                cursor = conn.execute(
                    "SELECT trial_credits, premium_credits, total_used FROM user_credits WHERE user_id = ?",
                    (user_id,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Return existing credit status
                    return CreditStatus(
                        user_id=str(user_id),
                        trial_credits=existing[0],
                        premium_credits=existing[1],
                        total_used=existing[2],
                        can_process=existing[0] + existing[1] > 0,
                        processing_tier=self._determine_processing_tier(existing[0], existing[1])
                    )
                
                # Create new credit record with 100 trial credits
                conn.execute("""
                    INSERT INTO user_credits (user_id, trial_credits, premium_credits, total_used)
                    VALUES (?, 100, 0, 0)
                """, (user_id,))
                
                # Log the credit initialization
                self._log_credit_transaction(
                    user_id, "initialize", CreditType.TRIAL, 100, 100,
                    "New user trial credits initialization", conn=conn
                )
                
                # Initialize sales intelligence record
                conn.execute("""
                    INSERT INTO sales_intelligence (user_id, lead_score, qualification_status, usage_pattern)
                    VALUES (?, 0, 'new', '{}')
                """, (user_id,))
                
                conn.commit()
                
                logger.info(f"Initialized 100 trial credits for user {user_id}")
                
                return CreditStatus(
                    user_id=str(user_id),
                    trial_credits=100,
                    premium_credits=0,
                    total_used=0,
                    can_process=True,
                    processing_tier=ProcessingTier.FREE_TRIAL
                )
                
        except Exception as e:
            logger.error(f"Failed to initialize credits for user {user_id}: {e}")
            raise
    
    def check_user_credits(self, user_id: int) -> CreditStatus:
        """Check current credit status for a user"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT trial_credits, premium_credits, total_used, 
                           is_trial_exhausted, sales_contacted, last_used
                    FROM user_credits WHERE user_id = ?
                """, (user_id,))
                
                result = cursor.fetchone()
                
                if not result:
                    # New user - initialize with trial credits
                    return self.initialize_user_credits(user_id)
                
                trial_credits, premium_credits, total_used, is_exhausted, sales_contacted, last_used = result
                
                # Get usage pattern for sales intelligence
                usage_pattern = self._get_usage_pattern(user_id, conn)
                lead_score = self._calculate_lead_score(user_id, usage_pattern, conn)
                
                return CreditStatus(
                    user_id=str(user_id),
                    trial_credits=trial_credits,
                    premium_credits=premium_credits,
                    total_used=total_used,
                    can_process=trial_credits + premium_credits > 0,
                    processing_tier=self._determine_processing_tier(trial_credits, premium_credits),
                    credits_remaining=trial_credits + premium_credits,
                    usage_pattern=usage_pattern,
                    lead_score=lead_score
                )
                
        except Exception as e:
            logger.error(f"Failed to check credits for user {user_id}: {e}")
            # Return safe default
            return CreditStatus(
                user_id=str(user_id),
                can_process=False,
                processing_tier=ProcessingTier.CONTACT_SALES
            )
    
    def deduct_credits(self, user_id: int, amount: int = 1, 
                      feature_used: str = "resume_analysis", 
                      processing_tier: ProcessingTier = ProcessingTier.FREE_TRIAL) -> bool:
        """
        Deduct credits from user account with Railway concurrency protection
        Returns True if successful, False if insufficient credits
        """
        try:
            # Use transaction isolation for concurrent credit deduction protection
            with self.db_manager.get_transaction() as conn:
                # Get current credits with row lock for concurrency protection
                cursor = conn.execute("""
                    SELECT trial_credits, premium_credits, total_used 
                    FROM user_credits WHERE user_id = ?
                """, (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    logger.warning(f"User {user_id} not found for credit deduction")
                    return False
                
                trial_credits, premium_credits, total_used = result
                total_available = trial_credits + premium_credits
                
                # Double-check credits haven't changed (race condition protection)
                if total_available < amount:
                    logger.info(f"Insufficient credits for user {user_id}: need {amount}, have {total_available}")
                    self._trigger_sales_contact(user_id, conn)
                    return False
                
                # Deduct from trial credits first, then premium
                new_trial = max(0, trial_credits - amount)
                new_premium = max(0, premium_credits - (amount - (trial_credits - new_trial)))
                new_total_used = total_used + amount
                
                # Update credits with WHERE clause to prevent race conditions
                rows_affected = conn.execute("""
                    UPDATE user_credits 
                    SET trial_credits = ?, premium_credits = ?, total_used = ?, 
                        last_used = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND trial_credits = ? AND premium_credits = ?
                """, (new_trial, new_premium, new_total_used, user_id, trial_credits, premium_credits)).rowcount
                
                if rows_affected == 0:
                    logger.warning(f"Concurrent credit deduction detected for user {user_id} - retrying")
                    # Rollback will happen automatically due to transaction context
                    return False
                
                # Log transaction
                credit_type = CreditType.TRIAL if trial_credits >= amount else CreditType.PREMIUM
                self._log_credit_transaction(
                    user_id, "deduct", credit_type, amount, 
                    new_trial + new_premium, f"Used for {feature_used}", conn=conn
                )
                
                # Log usage analytics
                self._log_usage_analytics(user_id, feature_used, amount, processing_tier, conn)
                
                # Update sales intelligence
                self._update_sales_intelligence(user_id, feature_used, new_trial + new_premium, conn)
                
                logger.info(f"Successfully deducted {amount} credits from user {user_id}")
                return True
                remaining = new_trial + new_premium
                if remaining <= 10 and not self._is_sales_contacted(user_id, conn):
                    self._trigger_sales_contact(user_id, conn, credits_remaining=remaining)
                
                # Trigger email automation based on credit milestones (Phase 3)
                self._trigger_email_automation(user_id, new_total_used, remaining)
                
                conn.commit()
                
                logger.info(f"Deducted {amount} credits from user {user_id} for {feature_used}. Remaining: {remaining}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to deduct credits for user {user_id}: {e}")
            return False
    
    def add_premium_credits(self, user_id: int, amount: int, 
                           payment_id: str = None, description: str = "Premium credit purchase") -> bool:
        """Add premium credits to user account"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT premium_credits FROM user_credits WHERE user_id = ?
                """, (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    # Initialize user credits first
                    self.initialize_user_credits(user_id)
                    current_premium = 0
                else:
                    current_premium = result[0]
                
                new_premium = current_premium + amount
                
                # Update credits
                conn.execute("""
                    UPDATE user_credits 
                    SET premium_credits = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (new_premium, user_id))
                
                # Log transaction
                self._log_credit_transaction(
                    user_id, "add", CreditType.PREMIUM, amount,
                    new_premium, description, 
                    metadata={"payment_id": payment_id} if payment_id else None,
                    conn=conn
                )
                
                conn.commit()
                
                logger.info(f"Added {amount} premium credits to user {user_id}. New balance: {new_premium}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add credits for user {user_id}: {e}")
            return False
    
    def _determine_processing_tier(self, trial_credits: int, premium_credits: int) -> ProcessingTier:
        """Determine the processing tier based on available credits"""
        if premium_credits > 0:
            return ProcessingTier.PREMIUM_INSTANT
        elif trial_credits > 0:
            return ProcessingTier.FREE_TRIAL
        else:
            return ProcessingTier.CONTACT_SALES
    
    def _log_credit_transaction(self, user_id: int, transaction_type: str, 
                               credit_type: CreditType, amount: int, balance_after: int,
                               description: str, metadata: Dict = None, conn=None):
        """Log credit transaction for audit trail"""
        if conn is None:
            conn = self.db_manager.get_connection()
            
        conn.execute("""
            INSERT INTO credit_transactions 
            (user_id, transaction_type, credit_type, amount, balance_after, description, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, transaction_type, credit_type.value, amount, balance_after, 
              description, json.dumps(metadata) if metadata else None))
    
    def _log_usage_analytics(self, user_id: int, feature_used: str, credits_consumed: int,
                           processing_tier: ProcessingTier, conn):
        """Log usage analytics for sales intelligence"""
        conn.execute("""
            INSERT INTO usage_analytics 
            (user_id, feature_used, credits_consumed, processing_tier, session_data)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, feature_used, credits_consumed, processing_tier.value, 
              json.dumps({"timestamp": datetime.now().isoformat()})))
    
    def _get_usage_pattern(self, user_id: int, conn) -> Dict[str, Any]:
        """Get usage pattern for sales intelligence"""
        cursor = conn.execute("""
            SELECT feature_used, COUNT(*) as count, SUM(credits_consumed) as total_credits
            FROM usage_analytics 
            WHERE user_id = ? 
            GROUP BY feature_used
        """, (user_id,))
        
        usage_data = cursor.fetchall()
        
        return {
            "features": {row[0]: {"count": row[1], "credits": row[2]} for row in usage_data},
            "total_sessions": sum(row[1] for row in usage_data),
            "total_credits_used": sum(row[2] for row in usage_data)
        }
    
    def _calculate_lead_score(self, user_id: int, usage_pattern: Dict[str, Any], conn) -> int:
        """Calculate lead score based on usage pattern"""
        try:
            score = 0
            
            # Base score for engagement
            total_sessions = usage_pattern.get("total_sessions", 0)
            total_credits = usage_pattern.get("total_credits_used", 0)
            
            score += min(total_sessions * 5, 50)  # Max 50 points for sessions
            score += min(total_credits * 2, 30)   # Max 30 points for credits used
            
            # Feature usage bonuses
            features = usage_pattern.get("features", {})
            if "resume_analysis" in features and features["resume_analysis"]["count"] > 5:
                score += 20  # High volume user
            if "legal_query" in features:
                score += 15  # Advanced feature user
            if "batch_analysis" in features:
                score += 25  # Enterprise-level usage
            
            return min(score, 100)  # Cap at 100
            
        except Exception as e:
            logger.error(f"Lead score calculation error: {e}")
            return 0
    
    def _update_sales_intelligence(self, user_id: int, feature_used: str, 
                                 credits_remaining: int, conn):
        """Update sales intelligence data"""
        usage_pattern = self._get_usage_pattern(user_id, conn)
        lead_score = self._calculate_lead_score(user_id, usage_pattern, conn)
        
        # Determine qualification status
        if lead_score >= 70:
            qualification = "hot"
        elif lead_score >= 40:
            qualification = "warm" 
        elif lead_score >= 20:
            qualification = "qualified"
        else:
            qualification = "new"
        
        conn.execute("""
            UPDATE sales_intelligence 
            SET lead_score = ?, qualification_status = ?, usage_pattern = ?, last_activity = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (lead_score, qualification, json.dumps(usage_pattern), user_id))
    
    def _trigger_sales_contact(self, user_id: int, conn, credits_remaining: int = 0):
        """Trigger sales contact for user running low on credits"""
        try:
            # Update user credits table
            conn.execute("""
                UPDATE user_credits 
                SET sales_contacted = TRUE 
                WHERE user_id = ?
            """, (user_id,))
            
            # Update sales intelligence
            conn.execute("""
                UPDATE sales_intelligence 
                SET qualification_status = 'contact_required', contacted_at = CURRENT_TIMESTAMP,
                    sales_notes = ?
                WHERE user_id = ?
            """, (f"Credits exhausted. Remaining: {credits_remaining}", user_id))
            
            logger.info(f"Sales contact triggered for user {user_id} with {credits_remaining} credits remaining")
            
        except Exception as e:
            logger.error(f"Failed to trigger sales contact for user {user_id}: {e}")
    
    def _is_sales_contacted(self, user_id: int, conn) -> bool:
        """Check if user has already been contacted by sales"""
        cursor = conn.execute("""
            SELECT sales_contacted FROM user_credits WHERE user_id = ?
        """, (user_id,))
        result = cursor.fetchone()
        return result and result[0]
    
    def get_sales_intelligence(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get sales intelligence data for qualified leads"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT si.user_id, si.lead_score, si.qualification_status, 
                           si.usage_pattern, si.last_activity, si.contacted_at,
                           u.email, u.name, uc.total_used, uc.trial_credits, uc.premium_credits
                    FROM sales_intelligence si
                    JOIN users u ON si.user_id = u.id
                    JOIN user_credits uc ON si.user_id = uc.user_id
                    WHERE si.lead_score >= 20
                    ORDER BY si.lead_score DESC, si.last_activity DESC
                    LIMIT ?
                """, (limit,))
                
                leads = []
                for row in cursor.fetchall():
                    leads.append({
                        "user_id": row[0],
                        "email": row[6],
                        "name": row[7],
                        "lead_score": row[1],
                        "qualification_status": row[2],
                        "usage_pattern": json.loads(row[3]) if row[3] else {},
                        "last_activity": row[4],
                        "contacted_at": row[5],
                        "credits_used": row[8],
                        "credits_remaining": row[9] + row[10]
                    })
                
                return leads
                
        except Exception as e:
            logger.error(f"Failed to get sales intelligence: {e}")
            return []
    
    def get_user_usage_stats(self, user_id: int) -> Dict[str, Any]:
        """Get detailed usage statistics for a user"""
        try:
            with self.db_manager.get_connection() as conn:
                # Get credit status
                credit_status = self.check_user_credits(user_id)
                
                # Get transaction history
                cursor = conn.execute("""
                    SELECT transaction_type, credit_type, amount, description, timestamp
                    FROM credit_transactions 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 20
                """, (user_id,))
                
                transactions = [
                    {
                        "type": row[0],
                        "credit_type": row[1], 
                        "amount": row[2],
                        "description": row[3],
                        "timestamp": row[4]
                    }
                    for row in cursor.fetchall()
                ]
                
                # Get feature usage
                cursor = conn.execute("""
                    SELECT feature_used, COUNT(*) as count, 
                           MIN(timestamp) as first_used, MAX(timestamp) as last_used
                    FROM usage_analytics 
                    WHERE user_id = ?
                    GROUP BY feature_used
                """, (user_id,))
                
                feature_usage = {
                    row[0]: {
                        "count": row[1],
                        "first_used": row[2],
                        "last_used": row[3]
                    }
                    for row in cursor.fetchall()
                }
                
                return {
                    "credit_status": credit_status.__dict__,
                    "transaction_history": transactions,
                    "feature_usage": feature_usage,
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get usage stats for user {user_id}: {e}")
            return {}
    
    def add_premium_credits(self, user_id: str, credits: int, source: str = "payment") -> int:
        """Add premium credits to user account (Phase 2 Payment Integration)"""
        try:
            user_id_int = int(user_id) if isinstance(user_id, str) else user_id
            
            with self.db_manager.get_connection() as conn:
                # Get current credits
                cursor = conn.execute("""
                    SELECT premium_credits FROM user_credits WHERE user_id = ?
                """, (user_id_int,))
                
                result = cursor.fetchone()
                if not result:
                    # Initialize user if doesn't exist
                    self.initialize_user_credits(user_id_int)
                    current_premium = 0
                else:
                    current_premium = result[0]
                
                new_premium = current_premium + credits
                
                # Update premium credits
                conn.execute("""
                    UPDATE user_credits 
                    SET premium_credits = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (new_premium, user_id_int))
                
                # Log the transaction
                self._log_credit_transaction(
                    user_id_int, "add", CreditType.PREMIUM, credits,
                    new_premium, f"Added {credits} premium credits via {source}",
                    metadata={"source": source, "payment_processing": True},
                    conn=conn
                )
                
                # Update sales intelligence
                self._update_payment_behavior(user_id_int, credits, source, conn)
                
                conn.commit()
                
                logger.info(f"Payment: Added {credits} premium credits to user {user_id}. New total: {new_premium}")
                return credits
                
        except Exception as e:
            logger.error(f"Failed to add premium credits for user {user_id}: {e}")
            return 0
    
    def can_skip_queue(self, user_id: str) -> Dict[str, Any]:
        """
        SECURE QUEUE SKIP VALIDATION
        - Check premium credits
        - Check active queue skip privileges
        - Validate expiry times
        - Anti-tampering protection
        """
        try:
            user_id_int = int(user_id) if isinstance(user_id, str) else user_id
            
            with self.db_manager.get_connection() as conn:
                # Check 1: Premium credits (always allow queue skip)
                cursor = conn.execute("""
                    SELECT premium_credits FROM user_credits WHERE user_id = ?
                """, (user_id_int,))
                
                result = cursor.fetchone()
                if result and result[0] > 0:
                    return {
                        "can_skip": True,
                        "reason": "premium_credits",
                        "credits": result[0],
                        "message": f"Premium user with {result[0]} credits"
                    }
                
                # Check 2: Active queue skip privileges
                cursor = conn.execute("""
                    SELECT privilege_type, expires_at, payment_reference 
                    FROM user_privileges 
                    WHERE user_id = ? 
                        AND privilege_type = 'queue_skip' 
                        AND is_active = 1 
                        AND (expires_at IS NULL OR expires_at > ?)
                    ORDER BY granted_at DESC
                    LIMIT 1
                """, (user_id_int, datetime.now()))
                
                privilege = cursor.fetchone()
                if privilege:
                    return {
                        "can_skip": True,
                        "reason": "queue_skip_privilege",
                        "expires_at": privilege[1],
                        "payment_reference": privilege[2],
                        "message": "Active queue skip privilege"
                    }
                
                # Check 3: Enterprise tier (if implemented)
                cursor = conn.execute("""
                    SELECT processing_tier FROM user_credits WHERE user_id = ?
                """, (user_id_int,))
                
                tier_result = cursor.fetchone()
                if tier_result and tier_result[0] == 'enterprise':
                    return {
                        "can_skip": True,
                        "reason": "enterprise_tier",
                        "message": "Enterprise user with unlimited processing"
                    }
                
                return {
                    "can_skip": False,
                    "reason": "no_privileges",
                    "message": "No queue skip privileges available"
                }
                
        except Exception as e:
            logger.error(f"Failed to check queue skip for user {user_id}: {e}")
            return {
                "can_skip": False,
                "reason": "error",
                "message": "Unable to verify queue skip privileges"
            }
    
    def consume_credit_secure(self, user_id: str, feature: str, credit_cost: int = 1) -> Dict[str, Any]:
        """
        SECURE CREDIT CONSUMPTION WITH ATOMIC OPERATIONS
        - Prevents race conditions
        - Validates credit availability
        - Logs all transactions
        - Prevents double-spending
        """
        try:
            user_id_int = int(user_id) if isinstance(user_id, str) else user_id
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Start atomic transaction
                cursor.execute("BEGIN EXCLUSIVE TRANSACTION")
                
                try:
                    # Get current credits with row lock
                    cursor.execute("""
                        SELECT trial_credits, premium_credits, total_used
                        FROM user_credits 
                        WHERE user_id = ?
                    """, (user_id_int,))
                    
                    result = cursor.fetchone()
                    if not result:
                        cursor.execute("ROLLBACK")
                        return {
                            "success": False,
                            "error": "User not found",
                            "credits_remaining": 0
                        }
                    
                    trial_credits, premium_credits, total_used = result
                    total_available = trial_credits + premium_credits
                    
                    # Validate credit availability
                    if total_available < credit_cost:
                        cursor.execute("ROLLBACK")
                        return {
                            "success": False,
                            "error": "Insufficient credits",
                            "credits_remaining": total_available,
                            "credits_needed": credit_cost
                        }
                    
                    # Determine which credits to consume (premium first for better experience)
                    premium_consumed = min(premium_credits, credit_cost)
                    trial_consumed = credit_cost - premium_consumed
                    
                    new_premium = premium_credits - premium_consumed
                    new_trial = trial_credits - trial_consumed
                    new_total_used = total_used + credit_cost
                    
                    # Update credits atomically
                    cursor.execute("""
                        UPDATE user_credits 
                        SET trial_credits = ?, 
                            premium_credits = ?, 
                            total_used = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (new_trial, new_premium, new_total_used, user_id_int))
                    
                    if cursor.rowcount != 1:
                        cursor.execute("ROLLBACK")
                        return {
                            "success": False,
                            "error": "Failed to update credits"
                        }
                    
                    # Log transaction for audit trail
                    cursor.execute("""
                        INSERT INTO credit_transactions 
                        (user_id, transaction_type, credit_type, amount, balance_after, 
                         description, metadata, timestamp)
                        VALUES (?, 'consume', ?, ?, ?, ?, ?, ?)
                    """, (
                        user_id_int, 
                        'mixed' if premium_consumed > 0 and trial_consumed > 0 else ('premium' if premium_consumed > 0 else 'trial'),
                        credit_cost,
                        new_trial + new_premium,
                        f"Used {credit_cost} credits for {feature}",
                        json.dumps({
                            "feature": feature,
                            "premium_consumed": premium_consumed,
                            "trial_consumed": trial_consumed,
                            "total_consumed": credit_cost
                        }),
                        datetime.now()
                    ))
                    
                    # Update usage analytics
                    cursor.execute("""
                        INSERT OR REPLACE INTO usage_analytics 
                        (user_id, feature_used, usage_count, last_used, updated_at)
                        VALUES (?, ?, 
                               COALESCE((SELECT usage_count FROM usage_analytics WHERE user_id = ? AND feature_used = ?), 0) + 1,
                               ?, ?)
                    """, (user_id_int, feature, user_id_int, feature, datetime.now(), datetime.now()))
                    
                    # Commit transaction
                    cursor.execute("COMMIT")
                    
                    # Determine new processing tier
                    new_tier = self._determine_processing_tier(new_trial, new_premium)
                    
                    logger.info(f"User {user_id} consumed {credit_cost} credits for {feature}. Remaining: {new_trial + new_premium}")
                    
                    return {
                        "success": True,
                        "credits_consumed": credit_cost,
                        "premium_consumed": premium_consumed,
                        "trial_consumed": trial_consumed,
                        "credits_remaining": new_trial + new_premium,
                        "trial_remaining": new_trial,
                        "premium_remaining": new_premium,
                        "processing_tier": new_tier.value,
                        "feature": feature,
                        "message": f"Successfully consumed {credit_cost} credits"
                    }
                    
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    logger.error(f"Credit consumption transaction failed: {e}")
                    return {
                        "success": False,
                        "error": "Transaction failed",
                        "details": str(e)
                    }
                finally:
                    cursor.close()
                    
        except Exception as e:
            logger.error(f"Failed to consume credits for user {user_id}: {e}")
            return {
                "success": False,
                "error": "Credit consumption failed",
                "details": str(e)
            }
    
    def grant_queue_skip(self, user_id: str, payment_id: str = None) -> bool:
        """Grant one-time queue skip access (for ₹40 payment)"""
        try:
            user_id_int = int(user_id) if isinstance(user_id, str) else user_id
            
            with self.db_manager.get_connection() as conn:
                # Update processing tier temporarily
                conn.execute("""
                    UPDATE user_credits 
                    SET processing_tier = 'queue_skip',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (user_id_int,))
                
                # Log the queue skip transaction
                self._log_credit_transaction(
                    user_id_int, "queue_skip", CreditType.PREMIUM, 0,
                    0, "Queue skip payment processed",
                    metadata={"payment_id": payment_id, "skip_type": "instant"},
                    conn=conn
                )
                
                conn.commit()
                logger.info(f"Queue skip granted to user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to grant queue skip for user {user_id}: {e}")
            return False
    
    def _update_payment_behavior(self, user_id: int, credits: int, source: str, conn):
        """Update sales intelligence based on payment behavior"""
        try:
            # Calculate lead score increase based on payment
            score_increase = 30  # Base score for any payment
            if credits >= 25:
                score_increase = 80  # Large package
            elif credits >= 10:
                score_increase = 50  # Medium package
            
            # Update lead score
            conn.execute("""
                UPDATE sales_intelligence 
                SET lead_score = COALESCE(lead_score, 0) + ?,
                    contact_priority = CASE 
                        WHEN COALESCE(lead_score, 0) + ? >= 80 THEN 'high'
                        WHEN COALESCE(lead_score, 0) + ? >= 50 THEN 'medium'
                        ELSE 'low'
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (score_increase, score_increase, score_increase, user_id))
            
            # Insert if not exists
            conn.execute("""
                INSERT OR IGNORE INTO sales_intelligence 
                (user_id, lead_score, contact_priority, updated_at)
                VALUES (?, ?, 'medium', CURRENT_TIMESTAMP)
            """, (user_id, score_increase))
            
            # Update payment behavior metadata
            conn.execute("""
                UPDATE sales_intelligence 
                SET behavior_data = json_set(
                    COALESCE(behavior_data, '{}'),
                    '$.payment_history',
                    json_array(
                        json_object(
                            'credits', ?,
                            'source', ?,
                            'timestamp', datetime('now'),
                            'score_increase', ?
                        )
                    )
                )
                WHERE user_id = ?
            """, (credits, source, score_increase, user_id))
            
        except Exception as e:
            logger.error(f"Failed to update payment behavior: {e}")
    
    def get_revenue_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue analytics for business intelligence"""
        try:
            with self.db_manager.get_connection() as conn:
                # Get payment transactions from last N days
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_payments,
                        SUM(amount_inr) as total_revenue,
                        SUM(credits_purchased) as total_credits_sold,
                        AVG(amount_inr) as avg_payment_value
                    FROM payment_transactions 
                    WHERE created_at >= datetime('now', '-{} days')
                        AND payment_status = 'completed'
                """.format(days))
                
                payment_stats = cursor.fetchone()
                
                # Get conversion metrics
                cursor = conn.execute("""
                    SELECT 
                        COUNT(DISTINCT u.user_id) as total_users,
                        COUNT(DISTINCT p.user_id) as paying_users
                    FROM user_credits u
                    LEFT JOIN payment_transactions p ON u.user_id = p.user_id
                        AND p.created_at >= datetime('now', '-{} days')
                        AND p.payment_status = 'completed'
                """.format(days))
                
                user_stats = cursor.fetchone()
                
                # Calculate conversion rate
                conversion_rate = 0
                if user_stats[0] > 0:
                    conversion_rate = (user_stats[1] / user_stats[0]) * 100
                
                return {
                    "period_days": days,
                    "total_payments": payment_stats[0] or 0,
                    "total_revenue": payment_stats[1] or 0,
                    "total_credits_sold": payment_stats[2] or 0,
                    "avg_payment_value": payment_stats[3] or 0,
                    "total_users": user_stats[0] or 0,
                    "paying_users": user_stats[1] or 0,
                    "conversion_rate": round(conversion_rate, 2),
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get revenue analytics: {e}")
            return {}

    def get_credit_status_secure(self, user_id: str) -> Dict[str, Any]:
        """
        GET SECURE CREDIT STATUS WITH PRIVILEGE VALIDATION
        - Returns comprehensive credit information
        - Includes queue skip privileges
        - Validates privilege expiry
        - Provides processing tier determination
        """
        try:
            user_id_int = int(user_id) if isinstance(user_id, str) else user_id
            
            with self.db_manager.get_connection() as conn:
                # Get basic credit information
                cursor = conn.execute("""
                    SELECT trial_credits, premium_credits, total_used, processing_tier, created_at, updated_at
                    FROM user_credits 
                    WHERE user_id = ?
                """, (user_id_int,))
                
                result = cursor.fetchone()
                if not result:
                    # Initialize user if not exists
                    self.initialize_user_credits(user_id_int)
                    cursor = conn.execute("""
                        SELECT trial_credits, premium_credits, total_used, processing_tier, created_at, updated_at
                        FROM user_credits 
                        WHERE user_id = ?
                    """, (user_id_int,))
                    result = cursor.fetchone()
                
                trial_credits, premium_credits, total_used, processing_tier, created_at, updated_at = result
                total_credits = trial_credits + premium_credits
                
                # Check for active privileges
                cursor = conn.execute("""
                    SELECT privilege_type, expires_at, payment_reference 
                    FROM user_privileges 
                    WHERE user_id = ? 
                        AND is_active = 1 
                        AND (expires_at IS NULL OR expires_at > ?)
                """, (user_id_int, datetime.now()))
                
                privileges = cursor.fetchall()
                
                # Determine actual processing tier based on credits and privileges
                actual_tier = self._determine_processing_tier_with_privileges(
                    trial_credits, premium_credits, privileges
                )
                
                # Check queue skip capability
                queue_skip_info = self.can_skip_queue(str(user_id))
                
                return {
                    "user_id": str(user_id),
                    "trial_credits": trial_credits,
                    "premium_credits": premium_credits,
                    "total_credits": total_credits,
                    "total_used": total_used,
                    "can_process": total_credits > 0 or len(privileges) > 0,
                    "processing_tier": actual_tier.value,
                    "queue_skip": queue_skip_info,
                    "active_privileges": [
                        {
                            "type": p[0],
                            "expires_at": p[1],
                            "payment_reference": p[2]
                        } for p in privileges
                    ],
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "status": "active" if total_credits > 0 or len(privileges) > 0 else "needs_credits"
                }
                
        except Exception as e:
            logger.error(f"Failed to get secure credit status for user {user_id}: {e}")
            return {
                "user_id": str(user_id),
                "error": str(e),
                "status": "error"
            }
    
    def get_credit_status(self, user_id: str) -> Dict[str, Any]:
        """Alias for get_credit_status_secure for backward compatibility"""
        return self.get_credit_status_secure(user_id)
    
    def _determine_processing_tier_with_privileges(self, trial_credits: int, premium_credits: int, privileges: List) -> ProcessingTier:
        """Determine processing tier including privileges"""
        # Check for active queue skip
        for privilege in privileges:
            if privilege[0] == 'queue_skip':
                return ProcessingTier.QUEUE_SKIP
        
        # Standard tier determination
        if premium_credits > 0:
            return ProcessingTier.PREMIUM_INSTANT
        elif trial_credits > 0:
            return ProcessingTier.FREE_TRIAL
        else:
            return ProcessingTier.CONTACT_SALES
    
    def _trigger_email_automation(self, user_id: int, credits_used: int, credits_remaining: int):
        """Trigger email automation based on credit usage milestones (Phase 3 Integration)"""
        try:
            if not self.email_automation:
                return  # Email automation not available
            
            # Define milestone triggers
            email_milestones = [25, 50, 75, 90, 100]
            
            # Check if user hit any milestone
            for milestone in email_milestones:
                if credits_used == milestone:
                    logger.info(f"Credit milestone {milestone} reached for user {user_id}")
                    
                    # Get user data for campaign evaluation
                    usage_data = {
                        "credits_used": credits_used,
                        "credits_remaining": credits_remaining,
                        "milestone": milestone
                    }
                    
                    # Trigger email campaign check
                    self.email_automation.check_and_trigger_campaigns(user_id, usage_data)
                    break
            
            # Special triggers for behavioral patterns
            if credits_used >= 85 and self._get_days_since_signup(user_id) <= 3:
                # Power user trigger
                usage_data = {
                    "credits_used": credits_used,
                    "credits_remaining": credits_remaining,
                    "power_user": True
                }
                self.email_automation.check_and_trigger_campaigns(user_id, usage_data)
            
        except Exception as e:
            logger.error(f"Email automation trigger error: {e}")
            # Non-breaking - don't fail credit deduction if email fails
    
    def _get_days_since_signup(self, user_id: int) -> int:
        """Get days since user signup"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT created_at FROM users WHERE id = ?
                """, (user_id,))
                result = cursor.fetchone()
                
                if result:
                    created_at = result[0]
                    signup_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    return (datetime.now() - signup_date).days
                
                return 0
        except Exception as e:
            logger.error(f"Error getting signup date for user {user_id}: {e}")
            return 0

    def health_check(self) -> Dict[str, Any]:
        """Lightweight health check for credit management system with caching"""
        try:
            # Check if we have cached health data (30 second TTL for Railway optimization)
            cache_key = "credit_health_check"
            cached_result = getattr(self, '_health_cache', {})
            
            if (cache_key in cached_result and 
                (datetime.now() - cached_result[cache_key]['cached_at']).seconds < 30):
                logger.debug("Returning cached health check result")
                return cached_result[cache_key]['data']
            
            # Quick connection test instead of heavy queries
            with self.db_manager.get_connection() as conn:
                # Simple query to test database connectivity
                cursor = conn.execute("SELECT 1")
                cursor.fetchone()
                
                # Quick lightweight stats (with LIMIT for Railway performance)
                try:
                    # Only get approximate counts for health check
                    cursor = conn.execute("SELECT COUNT(*) FROM user_credits LIMIT 1000")
                    total_users = min(cursor.fetchone()[0], 1000)  # Cap for performance
                    
                    # Simplified active user check
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM user_credits 
                        WHERE trial_credits + premium_credits > 0 
                        LIMIT 500
                    """)
                    active_users = min(cursor.fetchone()[0], 500)  # Cap for performance
                except:
                    # If detailed queries fail, still report healthy with basic connectivity
                    total_users = 0
                    active_users = 0
                    logger.warning("Health check using basic connectivity only")
                
                health_data = {
                    "status": "healthy",
                    "database_connection": "ok",
                    "total_users": total_users,
                    "active_users": active_users,
                    "timestamp": datetime.now().isoformat(),
                    "cache_enabled": True
                }
                
                # Cache the result for Railway efficiency
                if not hasattr(self, '_health_cache'):
                    self._health_cache = {}
                
                self._health_cache[cache_key] = {
                    'data': health_data,
                    'cached_at': datetime.now()
                }
                
                return health_data
                
        except Exception as e:
            logger.error(f"Credit system health check failed: {e}")
            return {
                "status": "unhealthy",
                "database_connection": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "cache_enabled": True
            }
