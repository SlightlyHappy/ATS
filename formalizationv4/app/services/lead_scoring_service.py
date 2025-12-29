"""
Lead Scoring Service - Core business logic for calculating lead scores
based on user behavior, engagement, and usage patterns.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass
from app import db
from app.models.user import User, CreditTransaction
from app.models.analysis import Analysis
from app.models.queue import AnalysisQueue, QueueStatus
from app.models.resume import Resume
from sqlalchemy import func, and_, desc

logger = logging.getLogger(__name__)

@dataclass
class ScoreComponents:
    """Data class for score breakdown."""
    engagement: int
    usage: int
    potential: int
    total: int

class LeadScoringService:
    """Service for calculating and managing lead scores."""
    
    # Scoring weights and thresholds
    MAX_ENGAGEMENT_SCORE = 40
    MAX_USAGE_SCORE = 30
    MAX_POTENTIAL_SCORE = 30
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def calculate_lead_score(self, user_id: str) -> Dict[str, int]:
        """
        Calculate comprehensive lead score for a user.
        
        Args:
            user_id: UUID of the user to score
            
        Returns:
            Dictionary with score breakdown
        """
        try:
            user = User.query.get(user_id)
            if not user:
                self.logger.warning(f"User {user_id} not found for scoring")
                return self._default_scores()
            
            # Calculate individual score components
            engagement_score = self._calculate_engagement_score(user)
            usage_score = self._calculate_usage_score(user)
            potential_score = self._calculate_potential_score(user)
            
            total_score = engagement_score + usage_score + potential_score
            
            self.logger.info(f"Calculated scores for {user.email}: "
                           f"E:{engagement_score}, U:{usage_score}, P:{potential_score}, T:{total_score}")
            
            return {
                'engagement': engagement_score,
                'usage': usage_score,
                'potential': potential_score,
                'total': min(total_score, 100)  # Cap at 100
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating lead score for {user_id}: {str(e)}")
            return self._default_scores()
    
    def _calculate_engagement_score(self, user: User) -> int:
        """
        Calculate engagement score (0-40 points) based on:
        - Login frequency
        - Recent activity
        - Platform exploration
        - Feature usage diversity
        """
        score = 0
        now = datetime.utcnow()
        
        # Login frequency (0-15 points)
        last_30_days = now - timedelta(days=30)
        
        # Count recent transactions as proxy for activity
        recent_transactions = user.credit_transactions.filter(
            CreditTransaction.created_at >= last_30_days
        ).count()
        
        login_score = min(recent_transactions * 2, 15)
        score += login_score
        
        # Recent activity (0-10 points)
        if hasattr(user, 'last_login') and user.last_login:
            days_since_login = (now - user.last_login).days
            if days_since_login <= 1:
                recent_activity_score = 10
            elif days_since_login <= 7:
                recent_activity_score = 7
            elif days_since_login <= 30:
                recent_activity_score = 4
            else:
                recent_activity_score = 0
        else:
            recent_activity_score = 0
        
        score += recent_activity_score
        
        # Platform exploration (0-10 points)
        # Check if user has used different features
        has_batch_uploads = user.resumes.join(AnalysisQueue).filter(
            AnalysisQueue.is_batch == True
        ).count() > 0
        
        has_multiple_analyses = user.resumes.count() > 1
        has_used_credits = user.total_credits_used > 0
        
        exploration_score = 0
        if has_batch_uploads:
            exploration_score += 4
        if has_multiple_analyses:
            exploration_score += 3
        if has_used_credits:
            exploration_score += 3
        
        score += exploration_score
        
        # Consistency (0-5 points)
        # Check for consistent usage over time
        if recent_transactions >= 5:
            consistency_score = 5
        elif recent_transactions >= 2:
            consistency_score = 3
        else:
            consistency_score = 0
        
        score += consistency_score
        
        return min(score, self.MAX_ENGAGEMENT_SCORE)
    
    def _calculate_usage_score(self, user: User) -> int:
        """
        Calculate usage score (0-30 points) based on:
        - Total analyses completed
        - Credits used/purchased
        - Batch processing usage
        - Analysis success rate
        """
        score = 0
        
        # Total analyses (0-12 points)
        total_analyses = Analysis.query.join(Resume).filter(
            Resume.user_id == user.id,
            Analysis.status == 'completed'
        ).count()
        
        analysis_score = min(total_analyses * 1.5, 12)
        score += analysis_score
        
        # Credits engagement (0-10 points)
        credits_used = user.total_credits_used or 0
        credits_purchased = user.total_credits_purchased or 0
        
        # Higher score for users who have purchased credits
        if credits_purchased > 0:
            credit_score = min(credits_purchased * 0.5 + 5, 10)
        else:
            credit_score = min(credits_used * 0.3, 5)
        
        score += credit_score
        
        # Batch processing usage (0-5 points)
        batch_analyses = AnalysisQueue.query.join(Resume).filter(
            Resume.user_id == user.id,
            AnalysisQueue.is_batch == True,
            AnalysisQueue.status == QueueStatus.COMPLETED.value
        ).count()
        
        batch_score = min(batch_analyses * 1, 5)
        score += batch_score
        
        # Success rate (0-3 points)
        total_submissions = AnalysisQueue.query.join(Resume).filter(
            Resume.user_id == user.id
        ).count()
        
        if total_submissions > 0:
            failed_submissions = AnalysisQueue.query.join(Resume).filter(
                Resume.user_id == user.id,
                AnalysisQueue.status == QueueStatus.FAILED.value
            ).count()
            
            success_rate = (total_submissions - failed_submissions) / total_submissions
            success_score = int(success_rate * 3)
        else:
            success_score = 0
        
        score += success_score
        
        return min(score, self.MAX_USAGE_SCORE)
    
    def _calculate_potential_score(self, user: User) -> int:
        """
        Calculate potential score (0-30 points) based on:
        - Account age and growth trajectory
        - Business indicators (email domain, usage patterns)
        - Scaling behavior
        - Premium feature interest
        """
        score = 0
        now = datetime.utcnow()
        
        # Account growth trajectory (0-12 points)
        account_age_days = (now - user.created_at).days
        
        if account_age_days > 0:
            analyses_count = Analysis.query.join(Resume).filter(
                Resume.user_id == user.id
            ).count()
            
            analyses_per_day = analyses_count / account_age_days
            
            # Higher score for users showing growth
            if analyses_per_day >= 1:
                growth_score = 12
            elif analyses_per_day >= 0.5:
                growth_score = 8
            elif analyses_per_day >= 0.2:
                growth_score = 5
            else:
                growth_score = 2
        else:
            growth_score = 0
        
        score += growth_score
        
        # Business email indicators (0-8 points)
        email_domain = user.email.split('@')[-1] if user.email else ''
        
        # Common business domains vs personal domains
        business_domains = [
            'company.com', 'corp.com', 'consulting.com', 'solutions.com',
            'hr.com', 'recruitment.com', 'staffing.com'
        ]
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        
        if any(bd in email_domain for bd in business_domains):
            business_score = 8
        elif email_domain not in personal_domains and '.' in email_domain:
            business_score = 5  # Likely business domain
        else:
            business_score = 0
        
        score += business_score
        
        # Scaling behavior (0-7 points)
        # Check for increasing usage over time
        last_30_days = now - timedelta(days=30)
        recent_analyses = Analysis.query.join(Resume).filter(
            Resume.user_id == user.id,
            Analysis.created_at >= last_30_days
        ).count()
        
        previous_30_days = last_30_days - timedelta(days=30)
        older_analyses = Analysis.query.join(Resume).filter(
            Resume.user_id == user.id,
            Analysis.created_at >= previous_30_days,
            Analysis.created_at < last_30_days
        ).count()
        
        if older_analyses > 0 and recent_analyses > older_analyses:
            scaling_score = 7  # Growing usage
        elif recent_analyses >= 5:
            scaling_score = 5  # High current usage
        elif recent_analyses >= 2:
            scaling_score = 3  # Moderate usage
        else:
            scaling_score = 0
        
        score += scaling_score
        
        # Premium indicators (0-3 points)
        # Users who hit credit limits or use advanced features
        if user.credits_balance == 0 and user.total_credits_used > 10:
            premium_score = 3  # Likely to need more credits
        elif user.total_credits_used > user.credits_balance:
            premium_score = 2  # Using credits actively
        else:
            premium_score = 0
        
        score += premium_score
        
        return min(score, self.MAX_POTENTIAL_SCORE)
    
    def _default_scores(self) -> Dict[str, int]:
        """Return default zero scores."""
        return {
            'engagement': 0,
            'usage': 0,
            'potential': 0,
            'total': 0
        }
    
    def batch_update_scores(self, user_ids: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Batch update scores for multiple users.
        
        Args:
            user_ids: List of user IDs to update. If None, updates all users.
            
        Returns:
            Dictionary with update statistics
        """
        try:
            if user_ids:
                users = User.query.filter(User.id.in_(user_ids)).all()
            else:
                # Update all users with recent activity
                cutoff_date = datetime.utcnow() - timedelta(days=90)
                users = User.query.filter(User.created_at >= cutoff_date).all()
            
            updated_count = 0
            error_count = 0
            
            for user in users:
                try:
                    # Update or create lead profile
                    from app.models.sales import Lead
                    
                    lead = Lead.query.filter_by(user_id=user.id).first()
                    if not lead:
                        lead = Lead(user_id=user.id)
                        db.session.add(lead)
                    
                    lead.update_score(force_recalculate=True)
                    updated_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Error updating score for user {user.id}: {str(e)}")
                    error_count += 1
            
            db.session.commit()
            
            self.logger.info(f"Batch score update completed: {updated_count} updated, {error_count} errors")
            
            return {
                'updated': updated_count,
                'errors': error_count,
                'total_processed': len(users)
            }
            
        except Exception as e:
            self.logger.error(f"Batch score update failed: {str(e)}")
            db.session.rollback()
            return {'updated': 0, 'errors': 0, 'total_processed': 0}
    
    def get_hot_leads(self, threshold: int = 80) -> List[Dict]:
        """
        Get all leads above the specified score threshold.
        
        Args:
            threshold: Minimum score for hot leads
            
        Returns:
            List of hot lead dictionaries
        """
        try:
            from app.models.sales import Lead
            
            hot_leads = Lead.query.filter(
                Lead.overall_score >= threshold
            ).order_by(desc(Lead.overall_score)).all()
            
            return [lead.to_dict() for lead in hot_leads]
            
        except Exception as e:
            self.logger.error(f"Error getting hot leads: {str(e)}")
            return []
    
    def get_score_distribution(self) -> Dict[str, int]:
        """Get distribution of lead scores for analytics."""
        try:
            from app.models.sales import Lead
            
            score_ranges = {
                'cold (0-39)': Lead.query.filter(Lead.overall_score < 40).count(),
                'warm (40-69)': Lead.query.filter(
                    and_(Lead.overall_score >= 40, Lead.overall_score < 70)
                ).count(),
                'hot (70-89)': Lead.query.filter(
                    and_(Lead.overall_score >= 70, Lead.overall_score < 90)
                ).count(),
                'super_hot (90-100)': Lead.query.filter(Lead.overall_score >= 90).count()
            }
            
            return score_ranges
            
        except Exception as e:
            self.logger.error(f"Error getting score distribution: {str(e)}")
            return {}
