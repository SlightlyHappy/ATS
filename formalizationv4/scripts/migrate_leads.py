#!/usr/bin/env python3
"""
Lead Scoring Migration Script

This script creates lead profiles for existing users and calculates
initial scores based on their usage history.
"""
import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.user import User
from app.models.sales import Lead, LeadSource
from app.services.lead_scoring_service import LeadScoringService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_existing_users_to_leads():
    """Create lead profiles for all existing users who don't have one."""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("Starting lead profile migration for existing users...")
            
            # Initialize lead scoring service
            lead_scorer = LeadScoringService()
            
            # Get all users without lead profiles
            users_without_leads = User.query.outerjoin(Lead).filter(Lead.id.is_(None)).all()
            
            created_count = 0
            error_count = 0
            
            for user in users_without_leads:
                try:
                    # Skip admin users for now (they're typically not leads)
                    if user.is_admin:
                        continue
                    
                    # Determine lead source based on user data
                    source = LeadSource.ORGANIC.value  # Default
                    
                    # Try to infer source from email domain or other indicators
                    if user.email:
                        domain = user.email.split('@')[-1].lower()
                        if domain in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']:
                            source = LeadSource.ORGANIC.value
                        else:
                            source = LeadSource.DIRECT.value  # Business email suggests direct signup
                    
                    # Create lead profile
                    lead = Lead(
                        user_id=user.id,
                        source=source,
                        first_activity=user.created_at,
                        last_activity=user.created_at
                    )
                    
                    db.session.add(lead)
                    db.session.flush()  # Get the ID
                    
                    # Calculate initial score
                    lead.update_score(force_recalculate=True)
                    
                    # Log the creation
                    lead.log_activity(
                        'profile_created',
                        'Lead profile created during migration',
                        {'migration_date': 'initial_migration'}
                    )
                    
                    created_count += 1
                    logger.info(f"Created lead profile for {user.email} (score: {lead.overall_score})")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error creating lead profile for user {user.id}: {str(e)}")
                    db.session.rollback()
                    continue
            
            # Commit all changes
            db.session.commit()
            
            logger.info(f"Migration completed: {created_count} lead profiles created, {error_count} errors")
            
            # Generate summary statistics
            print_migration_summary()
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            db.session.rollback()
            raise

def print_migration_summary():
    """Print summary of lead profiles after migration."""
    try:
        total_leads = Lead.query.count()
        hot_leads = Lead.query.filter(Lead.overall_score >= 70).count()
        warm_leads = Lead.query.filter(
            Lead.overall_score >= 40,
            Lead.overall_score < 70
        ).count()
        cold_leads = Lead.query.filter(Lead.overall_score < 40).count()
        
        print("\n" + "="*50)
        print("LEAD SCORING MIGRATION SUMMARY")
        print("="*50)
        print(f"Total Lead Profiles: {total_leads}")
        print(f"Hot Leads (70+):     {hot_leads}")
        print(f"Warm Leads (40-69):  {warm_leads}")
        print(f"Cold Leads (<40):    {cold_leads}")
        print("="*50)
        
        # Show top 5 leads
        top_leads = Lead.query.join(User).order_by(Lead.overall_score.desc()).limit(5).all()
        
        if top_leads:
            print("\nTOP 5 LEADS BY SCORE:")
            print("-"*50)
            for i, lead in enumerate(top_leads, 1):
                print(f"{i}. {lead.user.email} - Score: {lead.overall_score} - Status: {lead.status}")
        
        print("\n")
        
    except Exception as e:
        logger.error(f"Error generating migration summary: {str(e)}")

def update_all_lead_scores():
    """Force update scores for all existing leads."""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("Updating scores for all existing leads...")
            
            lead_scorer = LeadScoringService()
            result = lead_scorer.batch_update_scores()
            
            logger.info(f"Batch score update completed: {result}")
            
        except Exception as e:
            logger.error(f"Batch score update failed: {str(e)}")
            raise

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "update-scores":
        update_all_lead_scores()
    else:
        migrate_existing_users_to_leads()
