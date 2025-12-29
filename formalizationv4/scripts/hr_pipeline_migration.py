"""
Database migration script for HR Pipeline Intelligence features.
Creates all necessary tables and relationships for candidate management.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.candidate import (Candidate, CandidateActivity, PipelineStageHistory, 
                                Interview, CandidateAlert, HiringAnalytics)
from app.models.user import User
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_hr_pipeline_tables():
    """Create all HR pipeline tables."""
    try:
        app = create_app()
        
        with app.app_context():
            logger.info("Creating HR Pipeline Intelligence tables...")
            
            # Create all tables
            db.create_all()
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = [
                'candidates',
                'candidate_activities', 
                'pipeline_stage_history',
                'interviews',
                'candidate_alerts',
                'hiring_analytics'
            ]
            
            created_tables = []
            missing_tables = []
            
            for table in required_tables:
                if table in tables:
                    created_tables.append(table)
                    logger.info(f"✓ Table '{table}' created successfully")
                else:
                    missing_tables.append(table)
                    logger.error(f"✗ Table '{table}' not found")
            
            if missing_tables:
                logger.error(f"Missing tables: {missing_tables}")
                return False
            
            logger.info("✓ All HR Pipeline Intelligence tables created successfully")
            
            # Create indexes for better performance
            create_performance_indexes()
            
            return True
            
    except Exception as e:
        logger.error(f"Error creating HR pipeline tables: {str(e)}")
        return False

def create_performance_indexes():
    """Create database indexes for better query performance."""
    try:
        logger.info("Creating performance indexes...")
        
        # Get database connection
        with db.engine.connect() as connection:
            # Candidate indexes
            connection.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_candidates_user_id_status 
                ON candidates(user_id, status);
            """))
            
            connection.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_candidates_current_stage 
                ON candidates(current_stage);
            """))
            
            connection.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_candidates_priority_score 
                ON candidates(priority, overall_score DESC);
            """))
            
            connection.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_candidates_applied_at 
                ON candidates(applied_at DESC);
            """))
            
            # Activity indexes
            connection.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_candidate_activities_candidate_created 
                ON candidate_activities(candidate_id, created_at DESC);
            """))
            
            connection.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_candidate_activities_type 
                ON candidate_activities(activity_type);
            """))
            
            # Stage history indexes
            connection.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_pipeline_stage_history_candidate 
                ON pipeline_stage_history(candidate_id, changed_at DESC);
            """))
            
            # Alert indexes
            connection.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_candidate_alerts_active 
                ON candidate_alerts(candidate_id, is_dismissed, is_read);
            """))
            
            connection.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_candidate_alerts_priority 
                ON candidate_alerts(priority, created_at DESC);
            """))
            
            # Interview indexes
            connection.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_interviews_candidate_scheduled 
                ON interviews(candidate_id, scheduled_at);
            """))
            
            # Commit the transaction
            connection.commit()
        
        logger.info("✓ Performance indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating performance indexes: {str(e)}")

def create_sample_data():
    """Create sample data for testing (optional)."""
    try:
        logger.info("Creating sample data...")
        
        # Get a test user (create one if needed)
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            logger.info("No test user found - skipping sample data creation")
            return
        
        # Check if sample data already exists
        existing_candidates = Candidate.query.filter_by(user_id=test_user.id).count()
        if existing_candidates > 0:
            logger.info("Sample data already exists - skipping")
            return
        
        # Create sample candidates
        sample_candidates = [
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
                'position_title': 'Senior Software Engineer',
                'department': 'Engineering',
                'source': 'linkedin',
                'overall_score': 85.0,
                'priority': 'high'
            },
            {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'jane.smith@example.com', 
                'position_title': 'Product Manager',
                'department': 'Product',
                'source': 'referral',
                'overall_score': 92.0,
                'priority': 'urgent'
            },
            {
                'first_name': 'Mike',
                'last_name': 'Johnson',
                'email': 'mike.johnson@example.com',
                'position_title': 'Data Scientist',
                'department': 'Analytics',
                'source': 'job_board',
                'overall_score': 78.0,
                'priority': 'medium'
            }
        ]
        
        for candidate_data in sample_candidates:
            candidate = Candidate(
                user_id=test_user.id,
                first_name=candidate_data['first_name'],
                last_name=candidate_data['last_name'],
                email=candidate_data['email'],
                position_title=candidate_data['position_title'],
                department=candidate_data['department'],
                source=candidate_data['source'],
                overall_score=candidate_data['overall_score'],
                priority=candidate_data['priority']
            )
            
            db.session.add(candidate)
            db.session.flush()
            
            # Add initial activity
            activity = CandidateActivity(
                candidate_id=candidate.id,
                activity_type='created',
                description=f"Sample candidate {candidate.full_name} added to pipeline",
                created_by='Migration Script'
            )
            db.session.add(activity)
        
        db.session.commit()
        logger.info(f"✓ Created {len(sample_candidates)} sample candidates")
        
    except Exception as e:
        logger.error(f"Error creating sample data: {str(e)}")
        db.session.rollback()

def verify_migration():
    """Verify the migration was successful."""
    try:
        logger.info("Verifying migration...")
        
        # Test basic queries
        candidate_count = Candidate.query.count()
        activity_count = CandidateActivity.query.count()
        alert_count = CandidateAlert.query.count()
        
        logger.info(f"Current database state:")
        logger.info(f"  - Candidates: {candidate_count}")
        logger.info(f"  - Activities: {activity_count}")
        logger.info(f"  - Alerts: {alert_count}")
        
        # Test relationships
        if candidate_count > 0:
            sample_candidate = Candidate.query.first()
            activities = sample_candidate.activities.count()
            logger.info(f"  - Sample candidate has {activities} activities")
        
        logger.info("✓ Migration verification completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying migration: {str(e)}")
        return False

def main():
    """Main migration function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    
    logger.info("="*60)
    logger.info("HR PIPELINE INTELLIGENCE DATABASE MIGRATION")
    logger.info("="*60)
    
    try:
        # Create tables
        if not create_hr_pipeline_tables():
            logger.error("Failed to create tables")
            return False
        
        # Create sample data (optional)
        if '--sample-data' in sys.argv:
            create_sample_data()
        
        # Verify migration
        if not verify_migration():
            logger.error("Migration verification failed")
            return False
        
        logger.info("="*60)
        logger.info("✓ HR PIPELINE INTELLIGENCE MIGRATION COMPLETED SUCCESSFULLY")
        logger.info("="*60)
        
        logger.info("\nNext steps:")
        logger.info("1. Start the application")
        logger.info("2. Test the new pipeline endpoints at /api/v1/pipeline/")
        logger.info("3. Check the candidate management features")
        logger.info("4. Review the analytics dashboards")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
