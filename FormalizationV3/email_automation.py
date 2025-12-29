#!/usr/bin/env python3
"""
Email Automation System for HR ATS B2B SaaS
Railway-optimized async email sequences with connection pooling and background processing
"""

import logging
import json
import smtplib
import asyncio
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import time
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class EmailJob:
    """Email job for background processing"""
    to_email: str
    subject: str
    html_content: str
    user_name: str
    template_name: str
    priority: int = 5  # 1 = highest, 5 = lowest
    max_retries: int = 3
    retry_count: int = 0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class EmailTriggerType(Enum):
    """Types of email triggers"""
    CREDIT_MILESTONE = "credit_milestone"
    BEHAVIOR_PATTERN = "behavior_pattern"
    TRIAL_EXPIRY = "trial_expiry"
    PAYMENT_TRIGGER = "payment_trigger"
    SALES_QUALIFICATION = "sales_qualification"

class EmailTemplate(Enum):
    """Email template types"""
    WELCOME_25 = "welcome_25"
    MILESTONE_50 = "milestone_50"
    RUNNING_LOW_75 = "running_low_75"
    ALMOST_OUT_90 = "almost_out_90"
    TRIAL_COMPLETE_100 = "trial_complete_100"
    POWER_USER = "power_user"
    FEATURE_EXPLORER = "feature_explorer"
    BATCH_PROCESSOR = "batch_processor"
    COMPLIANCE_FOCUSED = "compliance_focused"
    HOT_LEAD = "hot_lead"
    ENTERPRISE_READY = "enterprise_ready"

@dataclass
class EmailCampaign:
    """Email campaign configuration"""
    template: EmailTemplate
    trigger_type: EmailTriggerType
    trigger_condition: str
    subject: str
    priority: int  # 1 = highest, 5 = lowest
    delay_hours: int = 0  # Delay before sending
    personalization_data: Dict[str, Any] = None
    
    def __post_init__(self):
        self.personalization_data = self.personalization_data or {}

# Email Campaign Definitions for Maximum Conversion
EMAIL_CAMPAIGNS = {
    # Credit Milestone Campaigns
    EmailTemplate.WELCOME_25: EmailCampaign(
        template=EmailTemplate.WELCOME_25,
        trigger_type=EmailTriggerType.CREDIT_MILESTONE,
        trigger_condition="credits_used == 25",
        subject="🚀 Welcome to HR ATS! You've analyzed 25 resumes - here's how to maximize your remaining 75 credits",
        priority=2,
        delay_hours=1
    ),
    
    EmailTemplate.MILESTONE_50: EmailCampaign(
        template=EmailTemplate.MILESTONE_50,
        trigger_type=EmailTriggerType.CREDIT_MILESTONE,
        trigger_condition="credits_used == 50",
        subject="⚡ Halfway milestone! Seeing great results? Let's discuss scaling your hiring process",
        priority=2,
        delay_hours=2
    ),
    
    EmailTemplate.RUNNING_LOW_75: EmailCampaign(
        template=EmailTemplate.RUNNING_LOW_75,
        trigger_type=EmailTriggerType.CREDIT_MILESTONE,
        trigger_condition="credits_used == 75",
        subject="⚠️ Running low on credits? Let's discuss your hiring volume needs",
        priority=1,
        delay_hours=0
    ),
    
    EmailTemplate.ALMOST_OUT_90: EmailCampaign(
        template=EmailTemplate.ALMOST_OUT_90,
        trigger_type=EmailTriggerType.CREDIT_MILESTONE,
        trigger_condition="credits_used == 90",
        subject="🔥 Only 10 credits left - Schedule your enterprise consultation now",
        priority=1,
        delay_hours=0
    ),
    
    EmailTemplate.TRIAL_COMPLETE_100: EmailCampaign(
        template=EmailTemplate.TRIAL_COMPLETE_100,
        trigger_type=EmailTriggerType.TRIAL_EXPIRY,
        trigger_condition="credits_used >= 100",
        subject="🏆 Trial complete! Here's your ROI summary + next steps",
        priority=1,
        delay_hours=1
    ),
    
    # Behavior-Based Campaigns
    EmailTemplate.POWER_USER: EmailCampaign(
        template=EmailTemplate.POWER_USER,
        trigger_type=EmailTriggerType.BEHAVIOR_PATTERN,
        trigger_condition="credits_used >= 85 AND days_since_signup <= 3",
        subject="🌟 Power User Alert! Let's discuss enterprise scaling immediately",
        priority=1,
        delay_hours=0
    ),
    
    EmailTemplate.FEATURE_EXPLORER: EmailCampaign(
        template=EmailTemplate.FEATURE_EXPLORER,
        trigger_type=EmailTriggerType.BEHAVIOR_PATTERN,
        trigger_condition="features_used >= 4",
        subject="🎯 You're a product champion! Perfect fit for our enterprise features",
        priority=2,
        delay_hours=4
    ),
    
    EmailTemplate.BATCH_PROCESSOR: EmailCampaign(
        template=EmailTemplate.BATCH_PROCESSOR,
        trigger_type=EmailTriggerType.BEHAVIOR_PATTERN,
        trigger_condition="batch_analyses >= 3",
        subject="📊 High-volume hiring detected - Enterprise solution recommended",
        priority=1,
        delay_hours=2
    ),
    
    EmailTemplate.COMPLIANCE_FOCUSED: EmailCampaign(
        template=EmailTemplate.COMPLIANCE_FOCUSED,
        trigger_type=EmailTriggerType.BEHAVIOR_PATTERN,
        trigger_condition="legal_queries >= 5 AND resume_analyses >= 10",
        subject="⚖️ Compliance-focused hiring? We have specialized enterprise features",
        priority=2,
        delay_hours=6
    ),
    
    # Sales Qualification Campaigns
    EmailTemplate.HOT_LEAD: EmailCampaign(
        template=EmailTemplate.HOT_LEAD,
        trigger_type=EmailTriggerType.SALES_QUALIFICATION,
        trigger_condition="lead_score >= 80",
        subject="🔥 URGENT: Hot lead qualification - Immediate attention required",
        priority=1,
        delay_hours=0
    ),
    
    EmailTemplate.ENTERPRISE_READY: EmailCampaign(
        template=EmailTemplate.ENTERPRISE_READY,
        trigger_type=EmailTriggerType.SALES_QUALIFICATION,
        trigger_condition="lead_score >= 70 AND payment_behavior == 'willing'",
        subject="🏢 Enterprise readiness confirmed - Let's schedule your demo",
        priority=1,
        delay_hours=1
    )
}

class EmailAutomationManager:
    """Railway-optimized async email automation with background processing"""
    
    def __init__(self, db_manager, credit_manager):
        """Initialize async email automation system"""
        self.db_manager = db_manager
        self.credit_manager = credit_manager
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.email_user)
        self.sales_email = os.getenv('SALES_EMAIL', 'sales@hrtools.com')
        
        # Railway-optimized async email processing
        self.email_queue = queue.PriorityQueue()
        self.email_executor = ThreadPoolExecutor(max_workers=2)  # Railway resource limit
        self.email_cache = {}  # Prevent duplicate emails
        self.batch_size = 5  # Process 5 emails per batch for Railway
        self.rate_limit_delay = 1.0  # 1 second between emails for Railway
        
        # Background email processor
        self._shutdown = False
        self._processor_thread = threading.Thread(target=self._process_email_queue, daemon=True)
        self._processor_thread.start()
        
        # SMTP connection pool for Railway efficiency
        self._smtp_pool = queue.Queue(maxsize=3)  # Max 3 SMTP connections
        self._initialize_smtp_pool()
        
        logger.info("Railway-optimized async email automation initialized")
    
    def _initialize_smtp_pool(self):
        """Initialize SMTP connection pool for Railway"""
        if not self.email_user or not self.email_password:
            logger.warning("Email credentials not configured")
            return
        
        # Pre-create SMTP connections for Railway efficiency
        for _ in range(2):  # Start with 2 connections
            try:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.email_user, self.email_password)
                self._smtp_pool.put(server)
                logger.debug("SMTP connection added to pool")
            except Exception as e:
                logger.warning(f"Failed to create SMTP connection: {e}")
    
    def _get_smtp_connection(self):
        """Get SMTP connection from pool with Railway optimization"""
        try:
            # Try to get existing connection
            server = self._smtp_pool.get(timeout=2)
            # Test connection
            server.noop()
            return server
        except (queue.Empty, Exception) as e:
            # Create new connection if pool is empty or connection is bad
            try:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.email_user, self.email_password)
                return server
            except Exception as e:
                logger.error(f"Failed to create SMTP connection: {e}")
                return None
    
    def _return_smtp_connection(self, server):
        """Return SMTP connection to pool"""
        try:
            if self._smtp_pool.qsize() < 3:  # Max pool size for Railway
                self._smtp_pool.put(server)
            else:
                server.quit()
        except Exception as e:
            logger.debug(f"Error returning SMTP connection to pool: {e}")
    
    def _process_email_queue(self):
        """Background email processor for Railway"""
        while not self._shutdown:
            try:
                batch = []
                # Collect batch of emails
                for _ in range(self.batch_size):
                    try:
                        priority, email_job = self.email_queue.get(timeout=5)
                        batch.append(email_job)
                    except queue.Empty:
                        break
                
                if batch:
                    self._process_email_batch(batch)
                else:
                    time.sleep(1)  # No work available
                    
            except Exception as e:
                logger.error(f"Email queue processor error: {e}")
                time.sleep(5)
    
    def _process_email_batch(self, batch: List[EmailJob]):
        """Process batch of emails with Railway optimization"""
        server = self._get_smtp_connection()
        if not server:
            logger.error("No SMTP connection available for batch processing")
            return
        
        try:
            for email_job in batch:
                try:
                    # Check for duplicate prevention
                    cache_key = f"{email_job.to_email}:{email_job.template_name}"
                    if cache_key in self.email_cache:
                        last_sent = self.email_cache[cache_key]
                        if (datetime.now() - last_sent).hours < 24:  # Prevent duplicates within 24h
                            logger.info(f"Duplicate email prevented: {cache_key}")
                            continue
                    
                    # Send email
                    self._send_email_via_connection(server, email_job)
                    
                    # Update cache
                    self.email_cache[cache_key] = datetime.now()
                    
                    # Railway rate limiting
                    time.sleep(self.rate_limit_delay)
                    
                except Exception as e:
                    logger.error(f"Failed to send email to {email_job.to_email}: {e}")
                    # Retry logic
                    if email_job.retry_count < email_job.max_retries:
                        email_job.retry_count += 1
                        # Re-add to queue with lower priority
                        self.email_queue.put((email_job.priority + 1, email_job))
                        
        finally:
            self._return_smtp_connection(server)
    
    def _send_email_via_connection(self, server, email_job: EmailJob) -> bool:
        """Send email via existing SMTP connection"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = email_job.subject
            msg['From'] = f"HR ATS Team <{self.from_email}>"
            msg['To'] = email_job.to_email
            
            # Attach HTML content
            html_part = MIMEText(email_job.html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            server.send_message(msg)
            
            # Update performance metrics
            self._update_email_performance(email_job.template_name, "sent")
            
            logger.info(f"Email sent successfully to {email_job.to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email via connection: {e}")
            return False
    
    def queue_email(self, to_email: str, subject: str, html_content: str, 
                   user_name: str = "", template_name: str = "generic", priority: int = 5):
        """Queue email for async processing"""
        email_job = EmailJob(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            user_name=user_name,
            template_name=template_name,
            priority=priority
        )
        
        # Add to priority queue (lower number = higher priority)
        self.email_queue.put((priority, email_job))
        logger.info(f"Email queued for {to_email} with priority {priority}")
    
    def send_campaign_email_async(self, user_id: int, template: EmailTemplate, 
                                personalization_data: Dict[str, Any] = None):
        """Send campaign email asynchronously"""
        try:
            # Get user details
            user_data = self._get_user_data(user_id)
            if not user_data:
                logger.warning(f"User {user_id} not found for email campaign")
                return False
            
            # Get campaign configuration
            campaign = EMAIL_CAMPAIGNS.get(template)
            if not campaign:
                logger.error(f"Campaign template {template} not found")
                return False
            
            # Build personalized email content
            html_content = self._build_email_content(
                template, user_data, personalization_data or {}
            )
            
            # Queue for async processing
            self.queue_email(
                to_email=user_data['email'],
                subject=campaign.subject,
                html_content=html_content,
                user_name=user_data['name'],
                template_name=template.value,
                priority=campaign.priority
            )
            
            # Log campaign send
            self._log_campaign_send(user_id, template.value, campaign.trigger_type.value)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue campaign email: {e}")
            return False
        
        # Initialize email tracking tables
        self._initialize_email_tables()
        
        logger.info("Email Automation Manager initialized successfully")
    
    def _initialize_email_tables(self):
        """Create email tracking tables"""
        try:
            with self.db_manager.get_connection() as conn:
                # Email campaigns sent
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS email_campaigns_sent (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        template_name VARCHAR(50) NOT NULL,
                        trigger_type VARCHAR(30) NOT NULL,
                        trigger_data TEXT,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        subject TEXT,
                        status VARCHAR(20) DEFAULT 'sent',
                        opened_at TIMESTAMP,
                        clicked_at TIMESTAMP,
                        responded_at TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                
                # Email automation triggers
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS email_automation_triggers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        trigger_type VARCHAR(30) NOT NULL,
                        trigger_condition TEXT,
                        triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processed BOOLEAN DEFAULT FALSE,
                        scheduled_send_at TIMESTAMP,
                        campaign_data TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                
                # Email performance tracking
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS email_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        template_name VARCHAR(50) NOT NULL,
                        sent_count INTEGER DEFAULT 0,
                        opened_count INTEGER DEFAULT 0,
                        clicked_count INTEGER DEFAULT 0,
                        responded_count INTEGER DEFAULT 0,
                        conversion_count INTEGER DEFAULT 0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                logger.info("Email automation tables initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize email tables: {e}")
    
    def check_and_trigger_campaigns(self, user_id: int, usage_data: Dict[str, Any] = None):
        """Check if user qualifies for any email campaigns and trigger them with thread-safe timeout"""
        import concurrent.futures
        
        def _do_campaign_check():
            try:
                # Get user data for campaign evaluation
                user_data = self._get_user_campaign_data(user_id, usage_data)
                
                if not user_data:
                    return
                
                # Check each campaign for trigger conditions (with fallback)
                processed_campaigns = 0
                for template, campaign in EMAIL_CAMPAIGNS.items():
                    try:
                        if self._should_trigger_campaign(user_id, user_data, campaign):
                            self._schedule_email_campaign(user_id, campaign, user_data)
                        processed_campaigns += 1
                        
                        # Prevent excessive processing in single call
                        if processed_campaigns >= 5:
                            logger.warning(f"Campaign processing limited to 5 per call for user {user_id}")
                            break
                            
                    except Exception as campaign_error:
                        logger.warning(f"Failed to process campaign {template} for user {user_id}: {campaign_error}")
                        continue
                
                # Process scheduled campaigns (with limited batch size)
                self._process_scheduled_campaigns(limit=10)
                
            except Exception as e:
                logger.error(f"Campaign check failed for user {user_id}: {e}")
                raise
        
        try:
            # Use ThreadPoolExecutor for thread-safe timeout
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(_do_campaign_check)
                try:
                    future.result(timeout=10)  # 10-second timeout
                except concurrent.futures.TimeoutError:
                    logger.warning(f"Campaign check timed out for user {user_id}, skipping")
                    return
                
        except Exception as e:
            logger.error(f"Failed to check campaigns for user {user_id}: {e}")
            # Don't re-raise to prevent breaking caller
    
    def _get_user_campaign_data(self, user_id: int, usage_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get comprehensive user data for campaign evaluation"""
        try:
            with self.db_manager.get_connection() as conn:
                # Get user basic info
                cursor = conn.execute("""
                    SELECT email, name, created_at FROM users WHERE id = ?
                """, (user_id,))
                user_result = cursor.fetchone()
                
                if not user_result:
                    return None
                
                email, name, created_at = user_result
                
                # Get credit status
                credit_status = self.credit_manager.check_user_credits(user_id)
                
                # Get usage analytics
                cursor = conn.execute("""
                    SELECT feature_used, COUNT(*) as count
                    FROM usage_analytics 
                    WHERE user_id = ?
                    GROUP BY feature_used
                """, (user_id,))
                
                feature_usage = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Get payment behavior
                cursor = conn.execute("""
                    SELECT COUNT(*) as payment_count, MAX(processed_at) as last_payment
                    FROM payment_transactions 
                    WHERE user_id = ? AND status = 'completed'
                """, (user_id,))
                payment_result = cursor.fetchone()
                payment_count = payment_result[0] if payment_result else 0
                
                # Calculate derived metrics
                days_since_signup = (datetime.now() - datetime.fromisoformat(created_at.replace('Z', '+00:00'))).days
                
                return {
                    "user_id": user_id,
                    "email": email,
                    "name": name,
                    "credits_used": credit_status.total_used,
                    "credits_remaining": credit_status.credits_remaining,
                    "lead_score": credit_status.lead_score,
                    "days_since_signup": days_since_signup,
                    "features_used": len(feature_usage),
                    "feature_usage": feature_usage,
                    "resume_analyses": feature_usage.get("resume_analysis", 0),
                    "legal_queries": feature_usage.get("legal_query", 0),
                    "batch_analyses": feature_usage.get("batch_analysis", 0),
                    "payment_count": payment_count,
                    "payment_behavior": "willing" if payment_count > 0 else "reluctant"
                }
                
        except Exception as e:
            logger.error(f"Failed to get user campaign data for {user_id}: {e}")
            return None
    
    def _should_trigger_campaign(self, user_id: int, user_data: Dict[str, Any], campaign: EmailCampaign) -> bool:
        """Evaluate if campaign should be triggered for user"""
        try:
            # Check if already sent
            if self._is_campaign_already_sent(user_id, campaign.template):
                return False
            
            # Evaluate trigger condition
            condition = campaign.trigger_condition
            
            # Replace variables in condition with actual values
            for key, value in user_data.items():
                condition = condition.replace(key, str(value))
            
            # Replace logical operators
            condition = condition.replace(" AND ", " and ").replace(" OR ", " or ")
            condition = condition.replace("==", "==").replace(">=", ">=").replace("<=", "<=")
            
            # Safely evaluate condition
            try:
                result = eval(condition)
                return bool(result)
            except:
                logger.warning(f"Invalid condition for campaign {campaign.template}: {condition}")
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating campaign trigger: {e}")
            return False
    
    def _is_campaign_already_sent(self, user_id: int, template: EmailTemplate) -> bool:
        """Check if campaign was already sent to user"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM email_campaigns_sent 
                    WHERE user_id = ? AND template_name = ?
                """, (user_id, template.value))
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            logger.error(f"Error checking campaign sent status: {e}")
            return True  # Err on side of caution
    
    def _schedule_email_campaign(self, user_id: int, campaign: EmailCampaign, user_data: Dict[str, Any]):
        """Schedule email campaign for delivery"""
        try:
            scheduled_time = datetime.now() + timedelta(hours=campaign.delay_hours)
            
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO email_automation_triggers 
                    (user_id, trigger_type, trigger_condition, scheduled_send_at, campaign_data)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user_id,
                    campaign.trigger_type.value,
                    campaign.trigger_condition,
                    scheduled_time,
                    json.dumps({
                        "template": campaign.template.value,
                        "subject": campaign.subject,
                        "priority": campaign.priority,
                        "user_data": user_data
                    })
                ))
                
            logger.info(f"Scheduled {campaign.template.value} campaign for user {user_id} at {scheduled_time}")
            
        except Exception as e:
            logger.error(f"Failed to schedule campaign: {e}")
    
    def _process_scheduled_campaigns(self, limit: int = 10):
        """Process and send scheduled email campaigns with configurable limit"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, user_id, campaign_data 
                    FROM email_automation_triggers 
                    WHERE processed = FALSE 
                        AND scheduled_send_at <= ?
                    ORDER BY scheduled_send_at ASC
                    LIMIT ?
                """, (datetime.now(), limit))
                
                pending_campaigns = cursor.fetchall()
                
                for trigger_id, user_id, campaign_data_json in pending_campaigns:
                    try:
                        campaign_data = json.loads(campaign_data_json)
                        self._send_campaign_email(user_id, campaign_data)
                        
                        # Mark as processed
                        conn.execute("""
                            UPDATE email_automation_triggers 
                            SET processed = TRUE 
                            WHERE id = ?
                        """, (trigger_id,))
                        
                    except Exception as e:
                        logger.error(f"Failed to process campaign {trigger_id}: {e}")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to process scheduled campaigns: {e}")
    
    def _send_campaign_email(self, user_id: int, campaign_data: Dict[str, Any]):
        """Send individual campaign email"""
        try:
            template_name = campaign_data["template"]
            subject = campaign_data["subject"]
            user_data = campaign_data["user_data"]
            
            # Generate email content
            html_content = self._generate_email_content(template_name, user_data)
            
            if not html_content:
                logger.error(f"Failed to generate content for template {template_name}")
                return
            
            # Send email
            success = self._send_email(
                to_email=user_data["email"],
                subject=subject,
                html_content=html_content,
                user_name=user_data.get("name", "")
            )
            
            if success:
                # Log sent campaign
                with self.db_manager.get_connection() as conn:
                    conn.execute("""
                        INSERT INTO email_campaigns_sent 
                        (user_id, template_name, trigger_type, trigger_data, subject, status)
                        VALUES (?, ?, ?, ?, ?, 'sent')
                    """, (
                        user_id,
                        template_name,
                        campaign_data.get("trigger_type", "unknown"),
                        json.dumps(user_data),
                        subject
                    ))
                
                # Update performance metrics
                self._update_email_performance(template_name, "sent")
                
                logger.info(f"Successfully sent {template_name} campaign to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send campaign email to user {user_id}: {e}")
    
    def _generate_email_content(self, template_name: str, user_data: Dict[str, Any]) -> str:
        """Generate personalized email content"""
        templates = {
            "welcome_25": self._template_welcome_25,
            "milestone_50": self._template_milestone_50,
            "running_low_75": self._template_running_low_75,
            "almost_out_90": self._template_almost_out_90,
            "trial_complete_100": self._template_trial_complete_100,
            "power_user": self._template_power_user,
            "feature_explorer": self._template_feature_explorer,
            "batch_processor": self._template_batch_processor,
            "compliance_focused": self._template_compliance_focused,
            "hot_lead": self._template_hot_lead,
            "enterprise_ready": self._template_enterprise_ready
        }
        
        template_func = templates.get(template_name)
        if template_func:
            return template_func(user_data)
        
        logger.error(f"Template not found: {template_name}")
        return ""
    
    def _template_welcome_25(self, user_data: Dict[str, Any]) -> str:
        """Welcome email template for 25 credits used"""
        name = user_data.get("name", "there")
        credits_remaining = user_data.get("credits_remaining", 75)
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0;">🚀 Welcome to HR ATS, {name}!</h2>
                
                <p>Congratulations! You've successfully analyzed 25 resumes and experienced the power of our AI-driven hiring platform.</p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Your Trial Progress:</h3>
                    <ul>
                        <li>✅ 25 resumes analyzed</li>
                        <li>⚡ {credits_remaining} credits remaining</li>
                        <li>🎯 Advanced features unlocked</li>
                    </ul>
                </div>
                
                <h3>📈 Maximize Your Remaining Credits:</h3>
                <ol>
                    <li><strong>Batch Analysis:</strong> Analyze multiple resumes at once (5 credits)</li>
                    <li><strong>Legal Compliance Queries:</strong> Get HR legal advice (1 credit)</li>
                    <li><strong>Advanced Scoring:</strong> Detailed candidate assessments</li>
                </ol>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://hrtool-sable.vercel.app/dashboard" 
                       style="background: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Continue Analysis →
                    </a>
                </div>
                
                <p>Need help? Reply to this email or schedule a demo call.</p>
                
                <p>Best regards,<br>The HR ATS Team</p>
            </div>
        </body>
        </html>
        """
    
    def _template_running_low_75(self, user_data: Dict[str, Any]) -> str:
        """Running low email template for 75 credits used"""
        name = user_data.get("name", "there")
        credits_remaining = user_data.get("credits_remaining", 25)
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #e74c3c;">⚠️ Running Low on Credits, {name}</h2>
                
                <p>You've used 75 of your 100 trial credits! With only <strong>{credits_remaining} credits remaining</strong>, now's the perfect time to discuss your hiring volume needs.</p>
                
                <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <h3>📊 Your Usage Pattern Analysis:</h3>
                    <ul>
                        <li>Resume analyses: {user_data.get('resume_analyses', 0)}</li>
                        <li>Legal queries: {user_data.get('legal_queries', 0)}</li>
                        <li>Features explored: {user_data.get('features_used', 0)}</li>
                    </ul>
                </div>
                
                <h3>🚀 Ready to Scale? We Have Options:</h3>
                
                <div style="display: flex; gap: 20px; margin: 20px 0;">
                    <div style="flex: 1; background: #f8f9fa; padding: 15px; border-radius: 8px;">
                        <h4>💎 Premium Credits</h4>
                        <p>10 credits for ₹300<br>25 credits for ₹650</p>
                        <a href="https://hrtool-sable.vercel.app/pricing" 
                           style="background: #007bff; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block;">
                            Buy Credits
                        </a>
                    </div>
                    
                    <div style="flex: 1; background: #e8f5e8; padding: 15px; border-radius: 8px;">
                        <h4>🏢 Enterprise Discussion</h4>
                        <p>Unlimited processing<br>Custom integrations</p>
                        <a href="mailto:{self.sales_email}?subject=Enterprise Discussion Request" 
                           style="background: #28a745; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block;">
                            Contact Sales
                        </a>
                    </div>
                </div>
                
                <p><strong>⏰ Don't lose momentum!</strong> Your hiring process is too important to pause.</p>
                
                <p>Best regards,<br>Your HR ATS Success Team</p>
            </div>
        </body>
        </html>
        """
    
    def _template_power_user(self, user_data: Dict[str, Any]) -> str:
        """Power user template for high usage in short time"""
        name = user_data.get("name", "there")
        credits_used = user_data.get("credits_used", 85)
        days_since_signup = user_data.get("days_since_signup", 3)
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #dc3545;">🌟 POWER USER ALERT: {name}</h2>
                
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3>🚨 Exceptional Usage Detected!</h3>
                    <p style="font-size: 18px; margin: 0;">
                        <strong>{credits_used} credits used in just {days_since_signup} days</strong><br>
                        You're processing resumes at enterprise volume!
                    </p>
                </div>
                
                <p>This level of usage indicates you have serious hiring needs. Our enterprise solution is designed exactly for power users like you.</p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>🏢 Enterprise Features You Need:</h3>
                    <ul>
                        <li>✅ <strong>Unlimited Processing</strong> - No credit limits ever</li>
                        <li>✅ <strong>Priority Queue</strong> - Instant results, no waiting</li>
                        <li>✅ <strong>Bulk Operations</strong> - Process 100+ resumes at once</li>
                        <li>✅ <strong>Custom Integrations</strong> - API access, webhooks</li>
                        <li>✅ <strong>Dedicated Support</strong> - Direct line to our team</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0; padding: 20px; background: #fff3cd; border-radius: 8px; border: 2px solid #ffc107;">
                    <h3 style="color: #856404; margin-top: 0;">⚡ URGENT: Let's Talk Now</h3>
                    <p style="color: #856404;">Your usage pattern qualifies you for immediate enterprise onboarding</p>
                    <a href="mailto:{self.sales_email}?subject=Power User - Enterprise Discussion Urgent&body=Hi, I'm using {credits_used} credits in {days_since_signup} days and need enterprise scaling immediately." 
                       style="background: #dc3545; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                        🔥 SCHEDULE IMMEDIATE CALL
                    </a>
                </div>
                
                <p><strong>Don't let credit limits slow down your hiring momentum.</strong> Enterprise customers see 300% faster time-to-hire.</p>
                
                <p>Best regards,<br>Enterprise Sales Team</p>
            </div>
        </body>
        </html>
        """
    
    # Add more email templates...
    def _template_milestone_50(self, user_data: Dict[str, Any]) -> str:
        return f"<html><body><h2>Milestone 50 Template</h2><p>Placeholder for {user_data.get('name', 'user')}</p></body></html>"
    
    def _template_almost_out_90(self, user_data: Dict[str, Any]) -> str:
        return f"<html><body><h2>Almost Out 90 Template</h2><p>Placeholder for {user_data.get('name', 'user')}</p></body></html>"
    
    def _template_trial_complete_100(self, user_data: Dict[str, Any]) -> str:
        return f"<html><body><h2>Trial Complete Template</h2><p>Placeholder for {user_data.get('name', 'user')}</p></body></html>"
    
    def _template_feature_explorer(self, user_data: Dict[str, Any]) -> str:
        return f"<html><body><h2>Feature Explorer Template</h2><p>Placeholder for {user_data.get('name', 'user')}</p></body></html>"
    
    def _template_batch_processor(self, user_data: Dict[str, Any]) -> str:
        return f"<html><body><h2>Batch Processor Template</h2><p>Placeholder for {user_data.get('name', 'user')}</p></body></html>"
    
    def _template_compliance_focused(self, user_data: Dict[str, Any]) -> str:
        return f"<html><body><h2>Compliance Focused Template</h2><p>Placeholder for {user_data.get('name', 'user')}</p></body></html>"
    
    def _template_hot_lead(self, user_data: Dict[str, Any]) -> str:
        return f"<html><body><h2>Hot Lead Template</h2><p>Placeholder for {user_data.get('name', 'user')}</p></body></html>"
    
    def _template_enterprise_ready(self, user_data: Dict[str, Any]) -> str:
        return f"<html><body><h2>Enterprise Ready Template</h2><p>Placeholder for {user_data.get('name', 'user')}</p></body></html>"
    
    def _send_email(self, to_email: str, subject: str, html_content: str, user_name: str = "") -> bool:
        """Send email via SMTP"""
        try:
            if not self.email_user or not self.email_password:
                logger.warning("Email credentials not configured - email not sent")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"HR ATS Team <{self.from_email}>"
            msg['To'] = to_email
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _update_email_performance(self, template_name: str, action: str):
        """Update email performance metrics"""
        try:
            with self.db_manager.get_connection() as conn:
                # Get or create performance record
                cursor = conn.execute("""
                    SELECT sent_count, opened_count, clicked_count, responded_count, conversion_count
                    FROM email_performance WHERE template_name = ?
                """, (template_name,))
                
                result = cursor.fetchone()
                
                if result:
                    sent, opened, clicked, responded, converted = result
                    
                    if action == "sent":
                        sent += 1
                    elif action == "opened":
                        opened += 1
                    elif action == "clicked":
                        clicked += 1
                    elif action == "responded":
                        responded += 1
                    elif action == "converted":
                        converted += 1
                    
                    conn.execute("""
                        UPDATE email_performance 
                        SET sent_count = ?, opened_count = ?, clicked_count = ?, 
                            responded_count = ?, conversion_count = ?, last_updated = ?
                        WHERE template_name = ?
                    """, (sent, opened, clicked, responded, converted, datetime.now(), template_name))
                else:
                    # Create new record
                    initial_counts = [0, 0, 0, 0, 0]
                    if action == "sent":
                        initial_counts[0] = 1
                    
                    conn.execute("""
                        INSERT INTO email_performance 
                        (template_name, sent_count, opened_count, clicked_count, responded_count, conversion_count)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (template_name, *initial_counts))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to update email performance: {e}")
    
    def get_email_analytics(self) -> Dict[str, Any]:
        """Get email campaign performance analytics"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT template_name, sent_count, opened_count, clicked_count, 
                           responded_count, conversion_count
                    FROM email_performance
                    ORDER BY sent_count DESC
                """)
                
                campaigns = []
                total_sent = 0
                total_opened = 0
                total_clicked = 0
                total_converted = 0
                
                for row in cursor.fetchall():
                    template, sent, opened, clicked, responded, converted = row
                    
                    total_sent += sent
                    total_opened += opened
                    total_clicked += clicked
                    total_converted += converted
                    
                    campaigns.append({
                        "template": template,
                        "sent": sent,
                        "opened": opened,
                        "clicked": clicked,
                        "responded": responded,
                        "converted": converted,
                        "open_rate": round((opened / sent * 100) if sent > 0 else 0, 2),
                        "click_rate": round((clicked / sent * 100) if sent > 0 else 0, 2),
                        "conversion_rate": round((converted / sent * 100) if sent > 0 else 0, 2)
                    })
                
                return {
                    "campaigns": campaigns,
                    "totals": {
                        "sent": total_sent,
                        "opened": total_opened,
                        "clicked": total_clicked,
                        "converted": total_converted,
                        "overall_open_rate": round((total_opened / total_sent * 100) if total_sent > 0 else 0, 2),
                        "overall_click_rate": round((total_clicked / total_sent * 100) if total_sent > 0 else 0, 2),
                        "overall_conversion_rate": round((total_converted / total_sent * 100) if total_sent > 0 else 0, 2)
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get email analytics: {e}")
            return {"campaigns": [], "totals": {}}
    
    def manually_trigger_campaign(self, user_id: int, template_name: str, admin_user: str = "admin") -> bool:
        """Manually trigger a specific campaign for a user"""
        try:
            # Get user data
            user_data = self._get_user_campaign_data(user_id)
            if not user_data:
                return False
            
            # Check if campaign exists
            template_enum = None
            for template in EmailTemplate:
                if template.value == template_name:
                    template_enum = template
                    break
            
            if not template_enum or template_enum not in EMAIL_CAMPAIGNS:
                logger.error(f"Invalid template: {template_name}")
                return False
            
            campaign = EMAIL_CAMPAIGNS[template_enum]
            
            # Schedule immediately
            campaign_data = {
                "template": template_name,
                "subject": f"[Manual] {campaign.subject}",
                "priority": 1,
                "user_data": user_data,
                "manual_trigger": True,
                "triggered_by": admin_user
            }
            
            self._send_campaign_email(user_id, campaign_data)
            
            logger.info(f"Manually triggered {template_name} campaign for user {user_id} by {admin_user}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to manually trigger campaign: {e}")
            return False
