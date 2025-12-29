"""
Background scheduler for HR Pipeline Intelligence automation.
Handles automated candidate scoring, alert generation, and analytics updates.
"""
import logging
from datetime import datetime, timedelta
from threading import Thread
import time
import schedule
from app import db
from app.services.candidate_scoring_service import CandidateScoringService
from app.services.high_priority_alert_service import HighPriorityAlertService
from app.services.hiring_analytics_service import HiringAnalyticsService
from app.models.user import User
from app.models.candidate import Candidate, CandidateStatus

logger = logging.getLogger(__name__)

class HRPipelineScheduler:
    """Scheduler for automated HR pipeline tasks."""
    
    def __init__(self, app=None):
        self.app = app
        self.scoring_service = CandidateScoringService()
        self.alert_service = HighPriorityAlertService()
        self.analytics_service = HiringAnalyticsService()
        self.running = False
        self.scheduler_thread = None
    
    def init_app(self, app):
        """Initialize with Flask app."""
        self.app = app
        
        # Setup scheduled tasks
        self.setup_schedule()
        
        # Start scheduler in background
        self.start_scheduler()
        
        logger.info("HR Pipeline Scheduler initialized")
    
    def setup_schedule(self):
        """Setup all scheduled tasks."""
        # Alert generation - every 30 minutes
        schedule.every(30).minutes.do(self.generate_alerts_for_all_users)
        
        # Candidate scoring - every 2 hours
        schedule.every(2).hours.do(self.score_unscored_candidates)
        
        # Analytics updates - daily at 6 AM
        schedule.every().day.at("06:00").do(self.update_daily_analytics)
        
        # Cleanup expired alerts - daily at 2 AM
        schedule.every().day.at("02:00").do(self.cleanup_expired_alerts)
        
        # Weekly analytics - Mondays at 8 AM
        schedule.every().monday.at("08:00").do(self.generate_weekly_analytics)
        
        logger.info("Scheduled tasks configured:")
        logger.info("  - Alert generation: every 30 minutes")
        logger.info("  - Candidate scoring: every 2 hours")
        logger.info("  - Daily analytics: daily at 6 AM")
        logger.info("  - Alert cleanup: daily at 2 AM")
        logger.info("  - Weekly analytics: Mondays at 8 AM")
    
    def start_scheduler(self):
        """Start the background scheduler."""
        if not self.running:
            self.running = True
            self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            logger.info("HR Pipeline Scheduler started")
    
    def stop_scheduler(self):
        """Stop the background scheduler."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("HR Pipeline Scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler in a background thread."""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(60)  # Continue running even if there's an error
    
    def generate_alerts_for_all_users(self):
        """Generate alerts for all active users."""
        try:
            if not self.app:
                logger.warning("No app context available for alert generation")
                return
            
            with self.app.app_context():
                logger.info("Starting automated alert generation for all users")
                
                # Get all users who have active candidates
                users_with_candidates = db.session.query(User.id).join(
                    Candidate, User.id == Candidate.user_id
                ).filter(
                    Candidate.status == CandidateStatus.ACTIVE.value
                ).distinct().all()
                
                total_alerts = 0
                
                for (user_id,) in users_with_candidates:
                    try:
                        result = self.alert_service.check_and_generate_alerts(str(user_id))
                        alerts_created = result.get('alerts_created', 0)
                        total_alerts += alerts_created
                        
                        if alerts_created > 0:
                            logger.info(f"Generated {alerts_created} alerts for user {user_id}")
                    
                    except Exception as e:
                        logger.error(f"Error generating alerts for user {user_id}: {str(e)}")
                
                logger.info(f"Automated alert generation completed: {total_alerts} total alerts created")
        
        except Exception as e:
            logger.error(f"Error in automated alert generation: {str(e)}")
    
    def score_unscored_candidates(self):
        """Score candidates that don't have scores yet."""
        try:
            if not self.app:
                logger.warning("No app context available for candidate scoring")
                return
            
            with self.app.app_context():
                logger.info("Starting automated candidate scoring")
                
                # Get candidates without scores
                unscored_candidates = Candidate.query.filter(
                    Candidate.status == CandidateStatus.ACTIVE.value,
                    (Candidate.overall_score == None) | (Candidate.overall_score == 0)
                ).all()
                
                scored_count = 0
                
                for candidate in unscored_candidates:
                    try:
                        result = self.scoring_service.score_candidate(candidate)
                        if result.get('overall_score', 0) > 0:
                            scored_count += 1
                    
                    except Exception as e:
                        logger.error(f"Error scoring candidate {candidate.full_name}: {str(e)}")
                
                # Commit changes
                db.session.commit()
                
                logger.info(f"Automated candidate scoring completed: {scored_count} candidates scored")
        
        except Exception as e:
            logger.error(f"Error in automated candidate scoring: {str(e)}")
    
    def update_daily_analytics(self):
        """Update daily analytics for all users."""
        try:
            if not self.app:
                logger.warning("No app context available for analytics update")
                return
            
            with self.app.app_context():
                logger.info("Starting daily analytics update")
                
                # Get all users with candidates
                users_with_candidates = db.session.query(User.id).join(
                    Candidate, User.id == Candidate.user_id
                ).distinct().all()
                
                updated_count = 0
                
                for (user_id,) in users_with_candidates:
                    try:
                        # Generate analytics for the last 30 days
                        result = self.analytics_service.generate_hiring_analytics(str(user_id), 30)
                        
                        if not result.get('error'):
                            updated_count += 1
                    
                    except Exception as e:
                        logger.error(f"Error updating analytics for user {user_id}: {str(e)}")
                
                logger.info(f"Daily analytics update completed: {updated_count} users updated")
        
        except Exception as e:
            logger.error(f"Error in daily analytics update: {str(e)}")
    
    def cleanup_expired_alerts(self):
        """Clean up expired alerts."""
        try:
            if not self.app:
                logger.warning("No app context available for alert cleanup")
                return
            
            with self.app.app_context():
                logger.info("Starting expired alert cleanup")
                
                # This is handled by the alert service
                self.alert_service._cleanup_expired_alerts()
                
                logger.info("Expired alert cleanup completed")
        
        except Exception as e:
            logger.error(f"Error in expired alert cleanup: {str(e)}")
    
    def generate_weekly_analytics(self):
        """Generate comprehensive weekly analytics."""
        try:
            if not self.app:
                logger.warning("No app context available for weekly analytics")
                return
            
            with self.app.app_context():
                logger.info("Starting weekly analytics generation")
                
                # Get all users with candidates
                users_with_candidates = db.session.query(User.id).join(
                    Candidate, User.id == Candidate.user_id
                ).distinct().all()
                
                for (user_id,) in users_with_candidates:
                    try:
                        # Generate comprehensive 7-day analytics
                        analytics = self.analytics_service.generate_hiring_analytics(str(user_id), 7)
                        
                        # Log key insights for monitoring
                        if not analytics.get('error'):
                            overview = analytics.get('overview', {})
                            logger.info(f"User {user_id} weekly stats: "
                                      f"{overview.get('total_candidates', 0)} candidates, "
                                      f"{overview.get('hire_rate', 0):.1f}% hire rate")
                    
                    except Exception as e:
                        logger.error(f"Error generating weekly analytics for user {user_id}: {str(e)}")
                
                logger.info("Weekly analytics generation completed")
        
        except Exception as e:
            logger.error(f"Error in weekly analytics generation: {str(e)}")
    
    def manual_alert_check(self, user_id: str = None):
        """Manually trigger alert check for a specific user or all users."""
        try:
            if not self.app:
                logger.warning("No app context available for manual alert check")
                return {'error': 'No app context'}
            
            with self.app.app_context():
                if user_id:
                    logger.info(f"Manual alert check for user {user_id}")
                    result = self.alert_service.check_and_generate_alerts(user_id)
                else:
                    logger.info("Manual alert check for all users")
                    self.generate_alerts_for_all_users()
                    result = {'message': 'Alert check completed for all users'}
                
                return result
        
        except Exception as e:
            logger.error(f"Error in manual alert check: {str(e)}")
            return {'error': str(e)}
    
    def manual_scoring_update(self, user_id: str = None, force_recalculate: bool = False):
        """Manually trigger candidate scoring update."""
        try:
            if not self.app:
                logger.warning("No app context available for manual scoring")
                return {'error': 'No app context'}
            
            with self.app.app_context():
                logger.info(f"Manual scoring update for user {user_id}")
                
                result = self.scoring_service.score_all_candidates(user_id, force_recalculate)
                
                # Commit changes
                db.session.commit()
                
                return result
        
        except Exception as e:
            logger.error(f"Error in manual scoring update: {str(e)}")
            return {'error': str(e)}
    
    def get_scheduler_status(self):
        """Get current scheduler status and statistics."""
        try:
            status = {
                'running': self.running,
                'next_jobs': [],
                'last_run_times': {}
            }
            
            # Get next scheduled jobs
            for job in schedule.jobs:
                status['next_jobs'].append({
                    'job': str(job.job_func.__name__),
                    'next_run': str(job.next_run) if job.next_run else 'Not scheduled',
                    'interval': str(job.interval) if hasattr(job, 'interval') else 'Unknown'
                })
            
            return status
        
        except Exception as e:
            logger.error(f"Error getting scheduler status: {str(e)}")
            return {'error': str(e)}

# Global scheduler instance
hr_pipeline_scheduler = HRPipelineScheduler()
