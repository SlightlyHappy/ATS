#!/usr/bin/env python3
"""
Sales Intelligence Dashboard for HR ATS B2B SaaS
Real-time prospect intelligence, lead management, and sales automation
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

class LeadPriority(Enum):
    """Lead priority levels"""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class SalesAction(Enum):
    """Recommended sales actions"""
    CALL_IMMEDIATELY = "call_immediately"
    SCHEDULE_DEMO = "schedule_demo"
    SEND_PROPOSAL = "send_proposal"
    NURTURE_EMAIL = "nurture_email"
    FOLLOW_UP = "follow_up"
    ENTERPRISE_PITCH = "enterprise_pitch"

@dataclass
class SalesLead:
    """Sales lead with intelligence data"""
    user_id: int
    email: str
    name: str
    company: Optional[str]
    lead_score: float
    conversion_probability: float
    priority: LeadPriority
    recommended_action: SalesAction
    revenue_potential: float
    days_since_signup: int
    credits_used: int
    credits_remaining: int
    last_activity: str
    usage_summary: Dict[str, Any]
    behavioral_signals: List[str]
    pain_points: List[str]
    decision_timeline: str
    contact_history: List[Dict[str, Any]]

class SalesIntelligenceDashboard:
    """Sales intelligence dashboard with actionable insights"""
    
    def __init__(self, db_manager, credit_manager, analytics_engine, email_automation):
        """Initialize sales intelligence dashboard"""
        self.db_manager = db_manager
        self.credit_manager = credit_manager
        self.analytics_engine = analytics_engine
        self.email_automation = email_automation
        
        # Sales intelligence configuration
        self.urgency_thresholds = {
            "hot_lead_score": 80,
            "high_engagement": 5,
            "enterprise_signals": 3,
            "credit_exhaustion": 10
        }
        
        self.revenue_tiers = {
            "enterprise": 150000,
            "mid_market": 75000,
            "small_business": 25000
        }
        
        logger.info("Sales Intelligence Dashboard initialized successfully")
    
    def get_hot_leads(self, limit: int = 20) -> List[SalesLead]:
        """Get hot leads requiring immediate attention"""
        try:
            hot_leads = []
            
            with self.db_manager.get_connection() as conn:
                # Get users with high engagement or running out of credits
                cursor = conn.execute("""
                    SELECT u.id, u.email, u.name, u.company, uc.total_used, 
                           uc.trial_credits + uc.premium_credits as remaining,
                           si.lead_score, si.qualification_status, si.last_activity,
                           u.created_at
                    FROM users u
                    JOIN user_credits uc ON u.id = uc.user_id
                    LEFT JOIN sales_intelligence si ON u.id = si.user_id
                    WHERE (
                        si.lead_score >= ? OR
                        uc.total_used >= 90 OR
                        (uc.total_used >= 75 AND (uc.trial_credits + uc.premium_credits) <= 10)
                    )
                    AND u.created_at >= date('now', '-30 days')
                    ORDER BY si.lead_score DESC, uc.total_used DESC
                    LIMIT ?
                """, (self.urgency_thresholds["hot_lead_score"], limit))
                
                for row in cursor.fetchall():
                    user_id, email, name, company, credits_used, remaining, lead_score, status, last_activity, created_at = row
                    
                    # Get comprehensive analytics
                    analytics = self.analytics_engine.analyze_user_comprehensive(user_id)
                    
                    # Determine priority and action
                    priority, action = self._determine_priority_and_action(analytics, credits_used, remaining)
                    
                    # Get behavioral signals
                    behavioral_signals = self._extract_behavioral_signals(analytics)
                    
                    # Get pain points
                    pain_points = self._identify_pain_points(analytics)
                    
                    # Calculate days since signup
                    days_since_signup = (datetime.now() - datetime.fromisoformat(created_at.replace('Z', '+00:00'))).days
                    
                    # Get contact history
                    contact_history = self._get_contact_history(user_id)
                    
                    hot_leads.append(SalesLead(
                        user_id=user_id,
                        email=email,
                        name=name or "Unknown",
                        company=company,
                        lead_score=lead_score or 0,
                        conversion_probability=analytics.conversion_probability,
                        priority=priority,
                        recommended_action=action,
                        revenue_potential=analytics.revenue_potential,
                        days_since_signup=days_since_signup,
                        credits_used=credits_used,
                        credits_remaining=remaining,
                        last_activity=last_activity or "No activity",
                        usage_summary=self._create_usage_summary(analytics),
                        behavioral_signals=behavioral_signals,
                        pain_points=pain_points,
                        decision_timeline=self._estimate_decision_timeline(analytics),
                        contact_history=contact_history
                    ))
            
            return hot_leads
            
        except Exception as e:
            logger.error(f"Failed to get hot leads: {e}")
            return []
    
    def _determine_priority_and_action(self, analytics, credits_used: int, remaining: int) -> tuple:
        """Determine lead priority and recommended action"""
        try:
            # URGENT priority conditions
            if (analytics.conversion_probability >= 0.8 or 
                credits_used >= 95 or
                analytics.segment.value == "power_user"):
                return LeadPriority.URGENT, SalesAction.CALL_IMMEDIATELY
            
            # HIGH priority conditions
            if (analytics.conversion_probability >= 0.6 or
                remaining <= 10 or
                analytics.enterprise_readiness >= 0.7):
                if analytics.enterprise_readiness >= 0.7:
                    return LeadPriority.HIGH, SalesAction.ENTERPRISE_PITCH
                else:
                    return LeadPriority.HIGH, SalesAction.SCHEDULE_DEMO
            
            # MEDIUM priority conditions
            if (analytics.conversion_probability >= 0.4 or
                credits_used >= 50):
                return LeadPriority.MEDIUM, SalesAction.SEND_PROPOSAL
            
            # LOW priority default
            return LeadPriority.LOW, SalesAction.NURTURE_EMAIL
            
        except Exception as e:
            logger.error(f"Error determining priority and action: {e}")
            return LeadPriority.LOW, SalesAction.FOLLOW_UP
    
    def _extract_behavioral_signals(self, analytics) -> List[str]:
        """Extract behavioral signals indicating buying intent"""
        signals = []
        
        try:
            # High usage signals
            if analytics.credits_used >= 80:
                signals.append("🔥 High volume usage - serious hiring needs")
            
            # Feature exploration signals
            if analytics.feature_adoption_rate >= 0.75:
                signals.append("🎯 Exploring advanced features - product champion")
                
            # Batch processing signals
            if analytics.feature_usage.get("batch_analysis", 0) >= 3:
                signals.append("📊 Multiple batch analyses - enterprise volume")
            
            # Compliance focus signals
            if analytics.feature_usage.get("legal_query", 0) >= 5:
                signals.append("⚖️ Legal compliance focus - regulated industry")
            
            # Payment behavior signals
            if analytics.payment_behavior.get("total_payments", 0) > 0:
                signals.append("💳 Payment willing - ready to invest")
            
            # Engagement velocity signals
            if analytics.engagement_velocity >= 7:
                signals.append("⚡ High engagement velocity - urgent hiring")
            
            # Time pressure signals
            if analytics.days_since_signup <= 3 and analytics.credits_used >= 50:
                signals.append("⏰ Fast adoption - time-sensitive hiring")
            
            return signals[:5]  # Limit to top 5 signals
            
        except Exception as e:
            logger.error(f"Error extracting behavioral signals: {e}")
            return ["📊 Analysis pending"]
    
    def _identify_pain_points(self, analytics) -> List[str]:
        """Identify user pain points for targeted messaging"""
        pain_points = []
        
        try:
            # Credit exhaustion pain point
            if analytics.credits_remaining <= 15:
                pain_points.append("Credit limits blocking hiring progress")
            
            # Time pressure pain point
            if analytics.engagement_velocity >= 6:
                pain_points.append("Time pressure for hiring decisions")
            
            # Volume hiring pain point
            if analytics.feature_usage.get("batch_analysis", 0) >= 2:
                pain_points.append("Manual resume screening inefficiency")
            
            # Compliance pain point
            if analytics.feature_usage.get("legal_query", 0) >= 3:
                pain_points.append("HR compliance complexity")
            
            # Quality vs. speed pain point
            if analytics.credits_used >= 60:
                pain_points.append("Balancing hiring quality with speed")
            
            return pain_points[:3]  # Limit to top 3 pain points
            
        except Exception as e:
            logger.error(f"Error identifying pain points: {e}")
            return ["General hiring challenges"]
    
    def _estimate_decision_timeline(self, analytics) -> str:
        """Estimate decision-making timeline"""
        try:
            # Immediate decision indicators
            if (analytics.conversion_probability >= 0.8 or
                analytics.credits_remaining <= 5):
                return "Immediate (within 24 hours)"
            
            # Short-term decision indicators
            if (analytics.conversion_probability >= 0.6 or
                analytics.enterprise_readiness >= 0.7):
                return "Short-term (1-3 days)"
            
            # Medium-term decision indicators
            if analytics.conversion_probability >= 0.4:
                return "Medium-term (1-2 weeks)"
            
            # Long-term evaluation
            return "Long-term evaluation (2+ weeks)"
            
        except Exception as e:
            logger.error(f"Error estimating decision timeline: {e}")
            return "Timeline unclear"
    
    def _create_usage_summary(self, analytics) -> Dict[str, Any]:
        """Create usage summary for sales context"""
        return {
            "total_credits_used": analytics.credits_used,
            "credits_remaining": analytics.credits_remaining,
            "features_adopted": len(analytics.feature_usage),
            "engagement_score": analytics.engagement_velocity,
            "primary_use_case": self._determine_primary_use_case(analytics.feature_usage),
            "usage_intensity": "High" if analytics.engagement_velocity >= 5 else "Medium" if analytics.engagement_velocity >= 2 else "Low"
        }
    
    def _determine_primary_use_case(self, feature_usage: Dict[str, int]) -> str:
        """Determine primary use case based on feature usage"""
        if not feature_usage:
            return "Evaluation"
        
        # Sort features by usage
        sorted_features = sorted(feature_usage.items(), key=lambda x: x[1], reverse=True)
        primary_feature = sorted_features[0][0]
        
        use_case_mapping = {
            "resume_analysis": "Individual Screening",
            "batch_analysis": "Volume Hiring",
            "legal_query": "Compliance Management",
            "queue_skip": "Urgent Hiring"
        }
        
        return use_case_mapping.get(primary_feature, "General Hiring")
    
    def _get_contact_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Get contact history for user"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT template_name, subject, sent_at, status, opened_at, clicked_at
                    FROM email_campaigns_sent 
                    WHERE user_id = ?
                    ORDER BY sent_at DESC
                    LIMIT 5
                """, (user_id,))
                
                history = []
                for row in cursor.fetchall():
                    template, subject, sent_at, status, opened_at, clicked_at = row
                    history.append({
                        "type": "email",
                        "template": template,
                        "subject": subject,
                        "sent_at": sent_at,
                        "status": status,
                        "opened": opened_at is not None,
                        "clicked": clicked_at is not None
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Error getting contact history for user {user_id}: {e}")
            return []
    
    def get_sales_pipeline_overview(self) -> Dict[str, Any]:
        """Get sales pipeline overview with key metrics"""
        try:
            with self.db_manager.get_connection() as conn:
                # Get pipeline metrics
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_leads,
                        COUNT(CASE WHEN si.lead_score >= 80 THEN 1 END) as hot_leads,
                        COUNT(CASE WHEN si.lead_score >= 60 THEN 1 END) as warm_leads,
                        COUNT(CASE WHEN si.lead_score >= 40 THEN 1 END) as qualified_leads,
                        COUNT(CASE WHEN uc.total_used >= 90 THEN 1 END) as trial_ending,
                        COUNT(CASE WHEN pt.status = 'completed' THEN 1 END) as converted,
                        SUM(CASE WHEN pt.status = 'completed' THEN pt.amount ELSE 0 END) as revenue
                    FROM users u
                    LEFT JOIN user_credits uc ON u.id = uc.user_id
                    LEFT JOIN sales_intelligence si ON u.id = si.user_id
                    LEFT JOIN payment_transactions pt ON u.id = pt.user_id
                    WHERE u.created_at >= date('now', '-30 days')
                """)
                
                result = cursor.fetchone()
                total, hot, warm, qualified, trial_ending, converted, revenue = result
                
                # Calculate conversion rates
                hot_conversion_rate = (converted / hot) if hot > 0 else 0
                overall_conversion_rate = (converted / total) if total > 0 else 0
                
                # Get revenue projections
                revenue_analytics = self.analytics_engine.get_revenue_analytics()
                
                return {
                    "pipeline_summary": {
                        "total_leads": total,
                        "hot_leads": hot,
                        "warm_leads": warm,
                        "qualified_leads": qualified,
                        "trial_ending_soon": trial_ending,
                        "converted_customers": converted
                    },
                    "conversion_metrics": {
                        "hot_lead_conversion_rate": round(hot_conversion_rate, 3),
                        "overall_conversion_rate": round(overall_conversion_rate, 3),
                        "target_conversion_rate": 0.15  # 15% target
                    },
                    "revenue_metrics": {
                        "current_month_revenue": revenue or 0,
                        "projected_monthly": revenue_analytics.get("projections", {}).get("next_month", 0),
                        "pipeline_value": hot * 150000,  # Potential value of hot leads
                        "average_deal_size": (revenue / converted) if converted > 0 else 0
                    },
                    "urgency_indicators": {
                        "immediate_attention_required": hot,
                        "trial_expiring_24h": self._count_expiring_trials(1),
                        "trial_expiring_week": self._count_expiring_trials(7),
                        "high_value_prospects": self._count_high_value_prospects()
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get sales pipeline overview: {e}")
            return {}
    
    def _count_expiring_trials(self, days: int) -> int:
        """Count trials expiring within specified days"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*)
                    FROM user_credits uc
                    JOIN users u ON uc.user_id = u.id
                    WHERE uc.trial_credits + uc.premium_credits <= 10
                        AND u.created_at <= date('now', '-' || (30 - ?) || ' days')
                        AND u.created_at >= date('now', '-30 days')
                """, (days,))
                
                return cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Error counting expiring trials: {e}")
            return 0
    
    def _count_high_value_prospects(self) -> int:
        """Count high-value prospects (enterprise potential)"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*)
                    FROM users u
                    JOIN user_credits uc ON u.id = uc.user_id
                    LEFT JOIN sales_intelligence si ON u.id = si.user_id
                    WHERE (
                        uc.total_used >= 80 OR
                        si.lead_score >= 70 OR
                        EXISTS (
                            SELECT 1 FROM usage_analytics ua 
                            WHERE ua.user_id = u.id 
                                AND ua.feature_used = 'batch_analysis'
                            GROUP BY ua.user_id 
                            HAVING COUNT(*) >= 3
                        )
                    )
                """)
                
                return cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Error counting high-value prospects: {e}")
            return 0
    
    def get_lead_recommendations(self, user_id: int) -> Dict[str, Any]:
        """Get specific recommendations for a lead"""
        try:
            # Get comprehensive analytics
            analytics = self.analytics_engine.analyze_user_comprehensive(user_id)
            
            # Generate specific talking points
            talking_points = self._generate_talking_points(analytics)
            
            # Generate objection handling
            objection_handling = self._generate_objection_handling(analytics)
            
            # Generate pricing strategy
            pricing_strategy = self._generate_pricing_strategy(analytics)
            
            # Get competitive advantages to highlight
            competitive_advantages = self._get_competitive_advantages(analytics)
            
            return {
                "user_analytics": {
                    "segment": analytics.segment.value,
                    "conversion_probability": analytics.conversion_probability,
                    "enterprise_readiness": analytics.enterprise_readiness,
                    "revenue_potential": analytics.revenue_potential
                },
                "sales_strategy": {
                    "primary_approach": self._determine_sales_approach(analytics),
                    "talking_points": talking_points,
                    "pain_points_to_address": self._identify_pain_points(analytics),
                    "value_proposition": self._create_value_proposition(analytics)
                },
                "objection_handling": objection_handling,
                "pricing_strategy": pricing_strategy,
                "competitive_advantages": competitive_advantages,
                "next_steps": analytics.recommendations,
                "timeline_pressure": self._get_timeline_pressure_points(analytics)
            }
            
        except Exception as e:
            logger.error(f"Failed to get lead recommendations for user {user_id}: {e}")
            return {}
    
    def _generate_talking_points(self, analytics) -> List[str]:
        """Generate specific talking points for sales conversation"""
        points = []
        
        if analytics.credits_used >= 80:
            points.append(f"You've processed {analytics.credits_used} resumes - that's serious hiring volume")
        
        if analytics.feature_adoption_rate >= 0.75:
            points.append("You're using our advanced features - shows you understand the platform's value")
        
        if analytics.payment_behavior.get("total_payments", 0) > 0:
            points.append("You've already invested in premium features - let's discuss scaling")
        
        if analytics.engagement_velocity >= 5:
            points.append("Your usage pattern shows urgent hiring needs - perfect for enterprise solution")
        
        if analytics.feature_usage.get("legal_query", 0) >= 3:
            points.append("HR compliance is clearly important to you - our enterprise solution includes dedicated compliance features")
        
        return points[:4]  # Top 4 talking points
    
    def _generate_objection_handling(self, analytics) -> Dict[str, str]:
        """Generate objection handling strategies"""
        return {
            "price_objection": f"Based on your {analytics.credits_used} resume analyses, you're saving 20+ hours per week. That's worth ₹{analytics.revenue_potential//10} in time savings monthly.",
            "feature_objection": f"You've already adopted {len(analytics.feature_usage)} features successfully. Enterprise adds unlimited processing and priority support.",
            "timing_objection": f"You're using {analytics.engagement_velocity:.1f} credits per day - at this rate, you'll need more capacity within days, not months.",
            "authority_objection": "Let's schedule a quick demo for your decision-maker. I can show ROI calculations specific to your usage pattern."
        }
    
    def _generate_pricing_strategy(self, analytics) -> Dict[str, Any]:
        """Generate pricing strategy recommendations"""
        if analytics.enterprise_readiness >= 0.7:
            return {
                "recommended_tier": "Enterprise",
                "starting_price": 150000,
                "discount_available": 20,
                "payment_terms": "Quarterly with 15% discount",
                "justification": "High-volume usage and enterprise signals justify premium pricing"
            }
        elif analytics.conversion_probability >= 0.6:
            return {
                "recommended_tier": "Professional",
                "starting_price": 75000,
                "discount_available": 15,
                "payment_terms": "Monthly with annual discount option",
                "justification": "Strong conversion probability allows for mid-tier pricing"
            }
        else:
            return {
                "recommended_tier": "Starter",
                "starting_price": 25000,
                "discount_available": 25,
                "payment_terms": "Monthly with flexible terms",
                "justification": "Price-sensitive prospect requires competitive entry pricing"
            }
    
    def _get_competitive_advantages(self, analytics) -> List[str]:
        """Get competitive advantages to highlight"""
        advantages = [
            "AI-powered analysis with 95% accuracy vs industry average of 70%",
            "Integrated HR legal compliance - no additional tools needed",
            "Batch processing capabilities - analyze 100+ resumes in minutes"
        ]
        
        if analytics.feature_usage.get("legal_query", 0) >= 3:
            advantages.insert(0, "Only platform with integrated HR legal expertise")
        
        if analytics.engagement_velocity >= 5:
            advantages.insert(0, "Fastest processing in the market - no queue delays")
        
        return advantages[:4]
    
    def _determine_sales_approach(self, analytics) -> str:
        """Determine primary sales approach"""
        if analytics.segment.value == "power_user":
            return "Direct enterprise pitch - emphasize unlimited processing"
        elif analytics.enterprise_readiness >= 0.7:
            return "Solution selling - focus on business impact and ROI"
        elif analytics.conversion_probability >= 0.6:
            return "Value demonstration - show cost savings and efficiency gains"
        else:
            return "Educational approach - build understanding of platform value"
    
    def _create_value_proposition(self, analytics) -> str:
        """Create personalized value proposition"""
        time_saved = analytics.credits_used * 15  # 15 minutes per resume
        hours_saved = time_saved / 60
        
        return f"Based on your {analytics.credits_used} resume analyses, you've already saved {hours_saved:.1f} hours. Enterprise scaling could save {hours_saved * 5:.0f}+ hours monthly while improving hiring quality by 40%."
    
    def _get_timeline_pressure_points(self, analytics) -> List[str]:
        """Get timeline pressure points for urgency creation"""
        pressure_points = []
        
        if analytics.credits_remaining <= 10:
            pressure_points.append(f"Only {analytics.credits_remaining} credits remaining - hiring process at risk")
        
        if analytics.engagement_velocity >= 6:
            pressure_points.append("High-velocity hiring pattern suggests immediate scaling needs")
        
        if analytics.days_since_signup <= 5:
            pressure_points.append("Fast adoption indicates urgent hiring requirements")
        
        return pressure_points
    
    def trigger_sales_action(self, user_id: int, action_type: str, sales_rep: str) -> bool:
        """Trigger specific sales action for a lead"""
        try:
            with self.db_manager.get_connection() as conn:
                # Log sales action
                conn.execute("""
                    INSERT INTO sales_actions 
                    (user_id, action_type, sales_rep, triggered_at, status)
                    VALUES (?, ?, ?, ?, 'pending')
                """, (user_id, action_type, sales_rep, datetime.now()))
                
                # Update sales intelligence
                conn.execute("""
                    UPDATE sales_intelligence 
                    SET contacted_at = ?, sales_notes = ?
                    WHERE user_id = ?
                """, (datetime.now(), f"Action triggered: {action_type} by {sales_rep}", user_id))
                
                # Trigger email if needed
                if action_type in ["call_immediately", "schedule_demo"]:
                    self.email_automation.manually_trigger_campaign(
                        user_id, "hot_lead", sales_rep
                    )
                
                conn.commit()
                
                logger.info(f"Sales action {action_type} triggered for user {user_id} by {sales_rep}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to trigger sales action: {e}")
            return False
    
    def update_lead_status(self, user_id: int, status: str, notes: str, sales_rep: str) -> bool:
        """Update lead status and add sales notes"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                    UPDATE sales_intelligence 
                    SET qualification_status = ?, sales_notes = ?, updated_at = ?
                    WHERE user_id = ?
                """, (status, notes, datetime.now(), user_id))
                
                # Log status change
                conn.execute("""
                    INSERT INTO sales_status_changes 
                    (user_id, old_status, new_status, notes, changed_by, changed_at)
                    VALUES (?, 
                        (SELECT qualification_status FROM sales_intelligence WHERE user_id = ?),
                        ?, ?, ?, ?)
                """, (user_id, user_id, status, notes, sales_rep, datetime.now()))
                
                conn.commit()
                
                logger.info(f"Lead status updated for user {user_id}: {status}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update lead status: {e}")
            return False
