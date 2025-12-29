#!/usr/bin/env python3
"""
Sales Intelligence Background Tasks

This script runs background tasks for:
- Checking and sending hot lead alerts
- Batch updating lead scores
- Generating sales metrics
"""
import os
import sys
import time
import schedule
import threading
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
from app.services.lead_scoring_service import LeadScoringService
from app.services.hot_lead_alert_service import HotLeadAlertService
from app.models.sales import SalesMetrics, Lead
from sqlalchemy import func
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SalesIntelligenceScheduler:
    """Background task scheduler for sales intelligence operations."""
    
    def __init__(self):
        self.app = create_app()
        self.running = False
        
        # Initialize services
        with self.app.app_context():
            self.lead_scorer = LeadScoringService()
            self.hot_lead_alerter = HotLeadAlertService(self.app.websocket_service)
    
    def start(self):
        """Start the background scheduler."""
        logger.info("Starting Sales Intelligence Background Scheduler...")
        
        # Schedule tasks
        self._schedule_tasks()
        
        # Run initial tasks
        self._run_initial_tasks()
        
        # Start the scheduler loop
        self.running = True
        self._run_scheduler()
    
    def stop(self):
        """Stop the background scheduler."""
        logger.info("Stopping Sales Intelligence Background Scheduler...")
        self.running = False
    
    def _schedule_tasks(self):
        """Schedule all background tasks."""
        
        # Hot lead alerts - every 30 minutes
        schedule.every(30).minutes.do(self._check_hot_leads)
        
        # Score updates - every 2 hours
        schedule.every(2).hours.do(self._update_scores)
        
        # Daily metrics generation - at 2 AM
        schedule.every().day.at("02:00").do(self._generate_daily_metrics)
        
        # Weekly metrics - Mondays at 3 AM
        schedule.every().monday.at("03:00").do(self._generate_weekly_metrics)
        
        # Monthly metrics - 1st of month at 4 AM
        schedule.every().month.do(self._generate_monthly_metrics)
        
        # Cleanup old data - every Sunday at 5 AM
        schedule.every().sunday.at("05:00").do(self._cleanup_old_data)
        
        logger.info("Background tasks scheduled successfully")
    
    def _run_initial_tasks(self):
        """Run initial tasks on startup."""
        logger.info("Running initial background tasks...")
        
        # Check for hot leads immediately
        self._check_hot_leads()
        
        # Update scores for recently active users
        self._update_recent_scores()
        
        logger.info("Initial tasks completed")
    
    def _run_scheduler(self):
        """Main scheduler loop."""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, stopping scheduler")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(60)  # Continue after error
    
    def _check_hot_leads(self):
        """Check for hot leads and send alerts."""
        try:
            with self.app.app_context():
                logger.info("Checking for hot leads...")
                result = self.hot_lead_alerter.check_and_send_hot_lead_alerts()
                
                if result['alerts_sent'] > 0:
                    logger.info(f"Sent {result['alerts_sent']} hot lead alerts "
                              f"({result['super_hot_alerts']} super hot)")
                else:
                    logger.debug("No new hot lead alerts to send")
                    
        except Exception as e:
            logger.error(f"Error checking hot leads: {str(e)}")
    
    def _update_scores(self):
        """Update lead scores for all users."""
        try:
            with self.app.app_context():
                logger.info("Starting batch score update...")
                result = self.lead_scorer.batch_update_scores()
                
                logger.info(f"Batch score update completed: "
                          f"{result['updated']} updated, {result['errors']} errors")
                    
        except Exception as e:
            logger.error(f"Error updating scores: {str(e)}")
    
    def _update_recent_scores(self):
        """Update scores only for recently active users."""
        try:
            with self.app.app_context():
                logger.info("Updating scores for recently active users...")
                
                # Get users active in last 7 days
                cutoff_date = datetime.utcnow() - timedelta(days=7)
                from app.models.user import User
                from app.models.analysis import Analysis
                from app.models.resume import Resume
                
                recent_user_ids = db.session.query(User.id).join(
                    Resume
                ).join(
                    Analysis
                ).filter(
                    Analysis.created_at >= cutoff_date
                ).distinct().all()
                
                user_ids = [str(uid[0]) for uid in recent_user_ids]
                
                if user_ids:
                    result = self.lead_scorer.batch_update_scores(user_ids)
                    logger.info(f"Updated scores for {result['updated']} recently active users")
                else:
                    logger.info("No recently active users found")
                    
        except Exception as e:
            logger.error(f"Error updating recent scores: {str(e)}")
    
    def _generate_daily_metrics(self):
        """Generate daily sales metrics."""
        try:
            with self.app.app_context():
                logger.info("Generating daily sales metrics...")
                
                yesterday = datetime.utcnow().date() - timedelta(days=1)
                
                # Check if metrics already exist
                existing = SalesMetrics.query.filter_by(
                    metric_date=yesterday,
                    metric_type='daily'
                ).first()
                
                if existing:
                    logger.info(f"Daily metrics for {yesterday} already exist, skipping")
                    return
                
                # Calculate metrics
                total_leads = Lead.query.count()
                new_leads = Lead.query.filter(
                    func.date(Lead.created_at) == yesterday
                ).count()
                hot_leads = Lead.query.filter(Lead.overall_score >= 70).count()
                qualified_leads = Lead.query.filter(Lead.status == 'qualified').count()
                converted_leads = Lead.query.filter(Lead.status == 'converted').count()
                
                conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
                avg_score = db.session.query(func.avg(Lead.overall_score)).scalar() or 0
                
                # Create metrics record
                metrics = SalesMetrics(
                    metric_date=yesterday,
                    metric_type='daily',
                    total_leads=total_leads,
                    new_leads=new_leads,
                    hot_leads=hot_leads,
                    qualified_leads=qualified_leads,
                    converted_leads=converted_leads,
                    conversion_rate=conversion_rate,
                    average_score=float(avg_score)
                )
                
                db.session.add(metrics)
                db.session.commit()
                
                logger.info(f"Daily metrics generated for {yesterday}")
                    
        except Exception as e:
            logger.error(f"Error generating daily metrics: {str(e)}")
            db.session.rollback()
    
    def _generate_weekly_metrics(self):
        """Generate weekly sales metrics."""
        try:
            with self.app.app_context():
                logger.info("Generating weekly sales metrics...")
                # Implementation similar to daily but for week ranges
                # Left as exercise - would aggregate daily metrics
                pass
                    
        except Exception as e:
            logger.error(f"Error generating weekly metrics: {str(e)}")
    
    def _generate_monthly_metrics(self):
        """Generate monthly sales metrics."""
        try:
            with self.app.app_context():
                logger.info("Generating monthly sales metrics...")
                # Implementation similar to daily but for month ranges
                # Left as exercise - would aggregate daily/weekly metrics
                pass
                    
        except Exception as e:
            logger.error(f"Error generating monthly metrics: {str(e)}")
    
    def _cleanup_old_data(self):
        """Clean up old data to prevent database bloat."""
        try:
            with self.app.app_context():
                logger.info("Cleaning up old sales intelligence data...")
                
                # Remove score history older than 90 days
                cutoff_date = datetime.utcnow() - timedelta(days=90)
                from app.models.sales import LeadScoreHistory, LeadActivity
                
                old_history = LeadScoreHistory.query.filter(
                    LeadScoreHistory.created_at < cutoff_date
                ).delete()
                
                # Remove old activities (keep 180 days)
                activity_cutoff = datetime.utcnow() - timedelta(days=180)
                old_activities = LeadActivity.query.filter(
                    LeadActivity.created_at < activity_cutoff
                ).delete()
                
                db.session.commit()
                
                logger.info(f"Cleanup completed: {old_history} score history records, "
                          f"{old_activities} activity records removed")
                    
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            db.session.rollback()

def run_scheduler():
    """Main function to run the scheduler."""
    scheduler = SalesIntelligenceScheduler()
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    finally:
        scheduler.stop()

def run_once(task_name):
    """Run a single task once for testing."""
    scheduler = SalesIntelligenceScheduler()
    
    with scheduler.app.app_context():
        if task_name == "hot-leads":
            scheduler._check_hot_leads()
        elif task_name == "update-scores":
            scheduler._update_scores()
        elif task_name == "daily-metrics":
            scheduler._generate_daily_metrics()
        elif task_name == "cleanup":
            scheduler._cleanup_old_data()
        else:
            print(f"Unknown task: {task_name}")
            print("Available tasks: hot-leads, update-scores, daily-metrics, cleanup")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_once(sys.argv[1])
    else:
        run_scheduler()
